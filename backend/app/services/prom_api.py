from collections.abc import Callable
import time
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.config import settings


def _validate_config() -> None:
    if not settings.prom_api_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='PROM_API_TOKEN is not configured')


def _extract_items(payload: Any, preferred_keys: list[str]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in preferred_keys:
        candidate = payload.get(key)
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]

    data = payload.get('data')
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    return []


def _extract_cursor(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ['last_id', 'next_last_id', 'next_id', 'cursor', 'next_cursor']:
        value = payload.get(key)
        if value not in (None, ''):
            return str(value)
    pagination = payload.get('pagination')
    if isinstance(pagination, dict):
        for key in ['last_id', 'next_last_id', 'next_id', 'cursor', 'next_cursor']:
            value = pagination.get(key)
            if value not in (None, ''):
                return str(value)
    return None


def _extract_item_id(item: dict[str, Any]) -> str | None:
    for key in ['id', 'order_id', 'number', 'prom_uid', 'uid', 'external_id']:
        value = item.get(key)
        if value not in (None, ''):
            return str(value)
    return None


def _fetch_with_retry(
    client: httpx.Client,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
) -> httpx.Response:
    last_error: Exception | None = None
    attempts = max(1, settings.prom_retry_attempts)

    for attempt in range(1, attempts + 1):
        try:
            response = client.get(url, headers=headers, params=params)
            if response.status_code < 500:
                return response
            detail = f'Prom API error {response.status_code}'
            try:
                payload = response.json()
                if isinstance(payload, dict) and payload.get('message'):
                    detail = str(payload['message'])
            except Exception:
                pass
            last_error = HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=detail,
            )
        except httpx.TimeoutException as exc:
            last_error = exc
        except httpx.HTTPError as exc:
            last_error = exc

        if attempt < attempts:
            time.sleep(settings.prom_retry_backoff_seconds * attempt)

    if isinstance(last_error, HTTPException):
        raise last_error

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail='Prom API request failed after retries',
    ) from last_error


def fetch_all(
    path: str,
    item_keys: list[str],
    *,
    stop_when: Callable[[dict[str, Any]], bool] | None = None,
) -> list[dict[str, Any]]:
    _validate_config()

    base_url = settings.prom_api_base_url.rstrip('/')
    endpoint = path if path.startswith('/') else f'/{path}'
    url = f'{base_url}{endpoint}'

    headers = {'Authorization': f'Bearer {settings.prom_api_token}'}
    all_items: list[dict[str, Any]] = []

    with httpx.Client(timeout=settings.prom_request_timeout) as client:
        cursor: str | None = None
        page = 1
        previous_signature: tuple[str, ...] | None = None
        seen_cursors: set[str] = set()

        for _ in range(settings.prom_max_pages):
            params: dict[str, Any] = {'limit': settings.prom_page_size, 'per_page': settings.prom_page_size}
            # Prom often uses cursor-based pagination via last_id.
            if cursor:
                params['last_id'] = cursor
                params['from_id'] = cursor
            else:
                params['page'] = page

            response = _fetch_with_retry(client, url, headers, params)
            if response.status_code >= 400:
                detail = f'Prom API error {response.status_code}'
                try:
                    payload = response.json()
                    if isinstance(payload, dict) and payload.get('message'):
                        detail = str(payload['message'])
                except Exception:
                    pass
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

            payload = response.json()
            items = _extract_items(payload, item_keys)
            if not items:
                break

            stop_reached = False
            if stop_when is not None:
                filtered_items: list[dict[str, Any]] = []
                for item in items:
                    if stop_when(item):
                        stop_reached = True
                        break
                    filtered_items.append(item)
                items = filtered_items

            if items:
                all_items.extend(items)

            if stop_reached:
                break

            signature = tuple(str(item.get('id') or item.get('prom_uid') or item.get('uid') or '') for item in items[:5])
            if previous_signature is not None and signature == previous_signature and not cursor:
                # Pagination params are likely ignored by upstream API, avoid infinite duplicates.
                break
            previous_signature = signature

            next_cursor = _extract_cursor(payload)
            if not next_cursor and items:
                # Some Prom endpoints do not return pagination metadata; derive cursor from last item id.
                derived = _extract_item_id(items[-1])
                if derived and derived != cursor:
                    next_cursor = derived

            if next_cursor and next_cursor != cursor and next_cursor not in seen_cursors:
                seen_cursors.add(next_cursor)
                cursor = next_cursor
                continue

            if len(items) < settings.prom_page_size:
                break
            page += 1

    return all_items
