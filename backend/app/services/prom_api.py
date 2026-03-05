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


def fetch_all(path: str, item_keys: list[str]) -> list[dict[str, Any]]:
    _validate_config()

    base_url = settings.prom_api_base_url.rstrip('/')
    endpoint = path if path.startswith('/') else f'/{path}'
    url = f'{base_url}{endpoint}'

    headers = {'Authorization': f'Bearer {settings.prom_api_token}'}
    all_items: list[dict[str, Any]] = []

    with httpx.Client(timeout=30.0) as client:
        cursor: str | None = None
        page = 1
        previous_signature: tuple[str, ...] | None = None

        for _ in range(settings.prom_max_pages):
            params: dict[str, Any] = {'limit': settings.prom_page_size}
            # Prom often uses cursor-based pagination via last_id.
            if cursor:
                params['last_id'] = cursor
            else:
                params['page'] = page

            response = client.get(url, headers=headers, params=params)
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

            signature = tuple(str(item.get('id') or item.get('prom_uid') or item.get('uid') or '') for item in items[:5])
            if previous_signature is not None and signature == previous_signature and not cursor:
                # Pagination params are likely ignored by upstream API, avoid infinite duplicates.
                break
            previous_signature = signature

            all_items.extend(items)

            next_cursor = _extract_cursor(payload)
            if next_cursor and next_cursor != cursor:
                cursor = next_cursor
                continue

            if len(items) < settings.prom_page_size:
                break
            page += 1

    return all_items
