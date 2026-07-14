from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import uuid4

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AdminUser
from .security import hash_password, verify_password

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    username: str
    is_active: bool


class AuthService:
    def __init__(self, settings):
        self.settings = settings

    def ensure_default_admin(self, session: Session) -> AdminUser:
        user = session.scalar(select(AdminUser).where(AdminUser.username == self.settings.admin_username))
        if user is not None:
            return user
        user = AdminUser(
            id=str(uuid4()),
            username=self.settings.admin_username,
            password_hash=self.settings.admin_password_hash or hash_password(self.settings.admin_password),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def authenticate(self, session: Session, username: str, password: str) -> AdminUser | None:
        user = session.scalar(select(AdminUser).where(AdminUser.username == username))
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, username: str, ttl_seconds: int | None = None) -> tuple[str, int, int]:
        now = int(time.time())
        expires_in = ttl_seconds if ttl_seconds is not None else self.settings.auth_token_ttl_seconds
        expires_at = now + expires_in
        token = jwt.encode(
            {"sub": username, "iat": now, "exp": expires_at},
            self.settings.auth_secret_key,
            algorithm="HS256",
        )
        return token, expires_in, expires_at

    def current_user(self, session: Session, token: str) -> AuthenticatedUser:
        try:
            payload = jwt.decode(token, self.settings.auth_secret_key, algorithms=["HS256"])
        except ExpiredSignatureError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except InvalidTokenError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error

        username = payload.get("sub")
        if not isinstance(username, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = session.scalar(select(AdminUser).where(AdminUser.username == username))
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User disabled or not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AuthenticatedUser(id=user.id, username=user.username, is_active=user.is_active)


def require_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    session = request.app.state.session_factory()
    try:
        return request.app.state.auth_service.current_user(session, credentials.credentials)
    finally:
        session.close()

