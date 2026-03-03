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


def fetch_all(path: str, item_keys: list[str]) -> list[dict[str, Any]]:
    _validate_config()

    base_url = settings.prom_api_base_url.rstrip('/')
    endpoint = path if path.startswith('/') else f'/{path}'
    url = f'{base_url}{endpoint}'

    headers = {'Authorization': f'Bearer {settings.prom_api_token}'}
    all_items: list[dict[str, Any]] = []

    with httpx.Client(timeout=30.0) as client:
        for page in range(1, settings.prom_max_pages + 1):
            params = {'page': page, 'limit': settings.prom_page_size}
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

            all_items.extend(items)
            if len(items) < settings.prom_page_size:
                break

    return all_items
