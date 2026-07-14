from __future__ import annotations

from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import WebProject
from ..schemas import CredentialRead, ProjectCreate, ProjectListResponse, ProjectRead, ProjectUpdate

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
            username=project.username,
            password_masked=MASKED_PASSWORD,
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

    def create(self, session: Session, payload: ProjectCreate) -> ProjectRead:
        project = WebProject(
            id=str(uuid4()),
            name=payload.name.strip(),
            url=payload.url.strip(),
            category=payload.category.strip() or "未分类",
            description=payload.description.strip(),
            notes=payload.notes.strip(),
            username=payload.username.strip(),
            password_ciphertext=self._cipher.encrypt(payload.password.encode("utf-8")).decode("ascii"),
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

    def update(self, session: Session, project_id: str, payload: ProjectUpdate) -> ProjectRead:
        project = self._get_or_404(session, project_id)
        values = payload.model_dump(exclude_unset=True)
        password = values.pop("password", None)
        for key, value in values.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(project, key, value)
        if password is not None:
            project.password_ciphertext = self._cipher.encrypt(password.encode("utf-8")).decode("ascii")
        session.commit()
        session.refresh(project)
        return self._read(project)

    def reveal(self, session: Session, project_id: str) -> CredentialRead:
        project = self._get_or_404(session, project_id)
        password = self._cipher.decrypt(project.password_ciphertext.encode("ascii")).decode("utf-8")
        return CredentialRead(project_id=project.id, password=password)

    def delete(self, session: Session, project_id: str) -> None:
        project = self._get_or_404(session, project_id)
        session.delete(project)
        session.commit()

