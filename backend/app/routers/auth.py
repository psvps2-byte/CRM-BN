from fastapi import APIRouter, HTTPException, Response, status

from app.config import settings
from app.schemas import LoginRequest, LoginResponse
from app.security import create_access_token

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/login', response_model=LoginResponse)
def login(payload: LoginRequest, response: Response):
    if payload.username != settings.admin_user or payload.password != settings.admin_pass:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    token = create_access_token(payload.username)
    response.set_cookie(
        key='access_token',
        value=token,
        httponly=True,
        samesite='lax',
        secure=False,
        max_age=60 * 60 * 24,
    )
    return LoginResponse(access_token=token)
