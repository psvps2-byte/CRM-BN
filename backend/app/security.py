from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status

from app.config import settings

ALGORITHM = 'HS256'
TOKEN_EXPIRE_HOURS = 24


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {'sub': subject, 'exp': expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        sub = payload.get('sub')
        if not sub:
            raise ValueError('Missing subject')
        return str(sub)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc
