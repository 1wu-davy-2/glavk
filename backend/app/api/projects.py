from __future__ import annotations

import base64
import logging
from collections.abc import Generator
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..auth import AuthenticatedUser, require_current_user
from ..schemas import CredentialData, CredentialEnvelope, CredentialRead, ProjectCreate, ProjectListResponse, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)


def get_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def decrypt_credentials(request: Request, envelope: CredentialEnvelope | None) -> CredentialData | None:
    if envelope is None:
        return None
    try:
        return CredentialData.model_validate(
            request.app.state.transport_crypto.decrypt_envelope(envelope.model_dump())
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="凭据数据无效") from error


def capture_project_screenshot(request: Request, session: Session, project_id: str, url: str) -> None:
    screenshot_service = request.app.state.screenshot_service
    try:
        relative_path = screenshot_service.capture(project_id, url)
    except Exception as error:
        logger.warning(
            "project screenshot capture failed",
            extra={"project_id": project_id, "error_type": type(error).__name__},
        )
        relative_path = None
    request.app.state.project_service.set_screenshot_path(session, project_id, relative_path)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    request: Request,
    search: str = Query(default="", max_length=120),
    category: str | None = Query(default=None, max_length=80),
    favorite: bool | None = None,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    return request.app.state.project_service.list(session, search=search, category=category, favorite=favorite)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    request: Request,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    project = request.app.state.project_service.create(
        session,
        payload,
        decrypt_credentials(request, payload.credential_envelope),
    )
    capture_project_screenshot(request, session, project.id, project.url)
    return request.app.state.project_service.get(session, project.id)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    request: Request,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    return request.app.state.project_service.get(session, project_id)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    request: Request,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    project = request.app.state.project_service.update(
        session,
        project_id,
        payload,
        decrypt_credentials(request, payload.credential_envelope),
    )
    capture_project_screenshot(request, session, project.id, project.url)
    return request.app.state.project_service.get(session, project.id)


@router.get("/{project_id}/credential", response_model=CredentialRead)
def reveal_credential(
    project_id: str,
    request: Request,
    client_public_key: str = Header(alias="X-Client-Public-Key"),
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    try:
        client_key_der = base64.b64decode(client_public_key, validate=True)
        envelope = request.app.state.transport_crypto.encrypt_for_client(
            request.app.state.project_service.credentials(session, project_id).model_dump(),
            client_key_der,
        )
        return CredentialRead(project_id=project_id, envelope=CredentialEnvelope.model_validate(envelope))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="客户端公钥无效") from error


@router.get("/{project_id}/screenshot")
def get_screenshot(
    project_id: str,
    request: Request,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    relative_path = request.app.state.project_service.screenshot_path(session, project_id)
    if not relative_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目暂无截图")
    try:
        path = request.app.state.screenshot_service.resolve_path(relative_path)
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目暂无截图") from error
    if not isinstance(path, Path) or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目暂无截图")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "private, no-store"})


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    request: Request,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    relative_path = request.app.state.project_service.delete(session, project_id)
    request.app.state.screenshot_service.delete(relative_path)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
