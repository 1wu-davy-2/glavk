from __future__ import annotations

from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import WebProject
from ..schemas import CredentialData, ProjectCreate, ProjectListResponse, ProjectRead, ProjectUpdate

MASKED_PASSWORD = "********"


class ProjectService:
    def __init__(self, settings: Settings):
        self._cipher = Fernet(settings.credential_key.encode("ascii"))

    def _read(self, project: WebProject) -> ProjectRead:
        return ProjectRead(
            id=project.id,
            name=project.name,
            url=project.url,
            category=project.category,
            description=project.description,
            notes=project.notes,
            username="",
            password_masked=MASKED_PASSWORD if project.password_ciphertext else "",
            has_credentials=bool(project.username or project.password_ciphertext),
            has_screenshot=bool(project.screenshot_path),
            is_favorite=project.is_favorite,
            is_enabled=project.is_enabled,
            sort_order=project.sort_order,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    def _get_or_404(self, session: Session, project_id: str) -> WebProject:
        project = session.get(WebProject, project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="网页系统不存在")
        return project

    def list(
        self,
        session: Session,
        *,
        search: str = "",
        category: str | None = None,
        favorite: bool | None = None,
    ) -> ProjectListResponse:
        statement = select(WebProject)
        if search.strip():
            term = f"%{search.strip()}%"
            statement = statement.where(
                or_(WebProject.name.ilike(term), WebProject.url.ilike(term), WebProject.username.ilike(term))
            )
        if category:
            statement = statement.where(WebProject.category == category)
        if favorite is not None:
            statement = statement.where(WebProject.is_favorite == favorite)
        projects = list(session.scalars(statement.order_by(WebProject.sort_order.asc(), WebProject.updated_at.desc())))
        return ProjectListResponse(items=[self._read(project) for project in projects], total=len(projects))

    def create(self, session: Session, payload: ProjectCreate, credentials: CredentialData | None = None) -> ProjectRead:
        username = credentials.username.strip() if credentials else ""
        password = credentials.password if credentials else None
        project = WebProject(
            id=str(uuid4()),
            name=payload.name.strip(),
            url=payload.url.strip(),
            category=payload.category.strip() or "未分类",
            description=payload.description.strip(),
            notes=payload.notes.strip(),
            password_ciphertext=(
                self._cipher.encrypt(password.encode("utf-8")).decode("ascii")
                if password
                else None
            ),
            username=username,
            is_favorite=payload.is_favorite,
            is_enabled=payload.is_enabled,
            sort_order=payload.sort_order,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return self._read(project)

    def get(self, session: Session, project_id: str) -> ProjectRead:
        return self._read(self._get_or_404(session, project_id))

    def update(
        self,
        session: Session,
        project_id: str,
        payload: ProjectUpdate,
        credentials: CredentialData | None = None,
    ) -> ProjectRead:
        project = self._get_or_404(session, project_id)
        values = payload.model_dump(exclude_unset=True)
        values.pop("credential_envelope", None)
        for key, value in values.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(project, key, value)
        if credentials is not None:
            if "username" in credentials.model_fields_set:
                project.username = credentials.username.strip()
            if "password" in credentials.model_fields_set:
                project.password_ciphertext = (
                    self._cipher.encrypt(credentials.password.encode("utf-8")).decode("ascii")
                    if credentials.password
                    else None
                )
        session.commit()
        session.refresh(project)
        return self._read(project)

    def credentials(self, session: Session, project_id: str) -> CredentialData:
        project = self._get_or_404(session, project_id)
        password = (
            self._cipher.decrypt(project.password_ciphertext.encode("ascii")).decode("utf-8")
            if project.password_ciphertext
            else None
        )
        return CredentialData(username=project.username, password=password)

    def screenshot_path(self, session: Session, project_id: str) -> str | None:
        return self._get_or_404(session, project_id).screenshot_path

    def set_screenshot_path(self, session: Session, project_id: str, relative_path: str | None) -> None:
        project = self._get_or_404(session, project_id)
        project.screenshot_path = relative_path
        session.commit()

    def delete(self, session: Session, project_id: str) -> str | None:
        project = self._get_or_404(session, project_id)
        screenshot_path = project.screenshot_path
        session.delete(project)
        session.commit()
        return screenshot_path
