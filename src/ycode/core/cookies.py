from fastapi import Response

from src.ycode.core.config import settings
from src.ycode.core.security import create_access_token, create_refresh_token


SECURE = settings.ENVIRONMENT == "production"
SAMESITE = "lax" if settings.ENVIRONMENT == "development" else "strict"


def set_access_token_cookie(response: Response, subject: int | str) -> str:   
    token = create_access_token(subject)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=SECURE,
        httponly=True,
        samesite=SAMESITE,
        path="/"
    )
    return token


def set_refresh_token_cookie(response: Response, subject: int | str, jti: str | None = None) -> str:    
    token = create_refresh_token(subject, jti)
    response.set_cookie(
        key="refresh_token",
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        secure=SECURE,
        httponly=True,
        samesite=SAMESITE,
        path="/"
    )
    return token


def set_auth_cookies(response: Response, subject: int | str, jti: str | None = None) -> dict:    
    access_token = set_access_token_cookie(response, subject)
    refresh_token = set_refresh_token_cookie(response, subject, jti)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def clear_auth_cookies(response: Response) -> None:   
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=SECURE,
        httponly=True,
        samesite=SAMESITE
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=SECURE,
        httponly=True,
        samesite=SAMESITE
    )
