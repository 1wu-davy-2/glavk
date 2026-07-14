from __future__ import annotations

import time
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..auth import AuthenticatedUser, require_current_user
from ..schemas import AuthUserRead, CredentialData, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, session: Session = Depends(get_session)):
    auth_service = request.app.state.auth_service
    try:
        credential_data = CredentialData.model_validate(
            request.app.state.transport_crypto.decrypt_envelope(payload.credential_envelope.model_dump())
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    user = auth_service.authenticate(session, credential_data.username, credential_data.password or "")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in, expires_at = auth_service.create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        expires_at=expires_at,
        user=AuthUserRead(username=user.username, is_active=user.is_active),
    )


@router.get("/me", response_model=AuthUserRead)
def me(user: AuthenticatedUser = Depends(require_current_user)):
    return AuthUserRead(username=user.username, is_active=user.is_active)
