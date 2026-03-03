from fastapi import Cookie, Depends, Header, HTTPException, status

from app.config import settings
from app.security import verify_token


def get_token(authorization: str | None = Header(default=None), access_token: str | None = Cookie(default=None)) -> str:
    if authorization and authorization.lower().startswith('bearer '):
        return authorization.split(' ', 1)[1]
    if access_token:
        return access_token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')


def require_admin(token: str = Depends(get_token)) -> str:
    username = verify_token(token)
    if username != settings.admin_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')
    return username
