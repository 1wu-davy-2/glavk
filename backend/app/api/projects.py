from __future__ import annotations

from collections.abc import Generator

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from ..auth import AuthenticatedUser, require_current_user
from ..schemas import CredentialRead, ProjectCreate, ProjectListResponse, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


def get_session(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


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
    return request.app.state.project_service.create(session, payload)


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
    return request.app.state.project_service.update(session, project_id, payload)


@router.get("/{project_id}/credential", response_model=CredentialRead)
def reveal_credential(
    project_id: str,
    request: Request,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    return request.app.state.project_service.reveal(session, project_id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    request: Request,
    _: AuthenticatedUser = Depends(require_current_user),
    session: Session = Depends(get_session),
):
    request.app.state.project_service.delete(session, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

