from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import Settings
from backend.app.db import Base
from backend.app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "projects.sqlite3"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    settings = Settings(
        database_url=f"sqlite:///{database_path}",
        auth_secret_key="test-auth-secret-key-with-enough-length",
        credential_encryption_key=Fernet.generate_key().decode("ascii"),
        admin_username="admin",
        admin_password="admin@123",
    )
    return TestClient(create_app(settings=settings, session_factory=session_factory))


def login_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin@123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def project_payload() -> dict[str, object]:
    return {
        "name": "客户管理后台",
        "url": "https://crm.example.com/login",
        "category": "业务系统",
        "description": "客户资料和销售流程",
        "notes": "工作日使用",
        "username": "crm-admin",
        "password": "crm-secret",
        "is_favorite": True,
        "is_enabled": True,
    }


def test_project_crud_masks_password_and_reveals_it_separately(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        created = client.post("/api/projects", json=project_payload(), headers=headers)
        project_id = created.json()["id"]

        assert created.status_code == 201
        assert created.json()["password_masked"] == "********"
        assert "password" not in created.json()

        listed = client.get("/api/projects?search=客户&category=业务系统", headers=headers)
        credential = client.get(f"/api/projects/{project_id}/credential", headers=headers)

        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["name"] == "客户管理后台"
        assert listed.json()["items"][0]["password_masked"] == "********"
        assert credential.json() == {"project_id": project_id, "password": "crm-secret"}

        updated = client.put(
            f"/api/projects/{project_id}",
            json={"name": "客户运营后台", "password": "new-secret", "is_favorite": False},
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "客户运营后台"
        assert updated.json()["is_favorite"] is False

        updated_credential = client.get(f"/api/projects/{project_id}/credential", headers=headers)
        assert updated_credential.json()["password"] == "new-secret"

        deleted = client.delete(f"/api/projects/{project_id}", headers=headers)
        assert deleted.status_code == 204
        assert client.get("/api/projects", headers=headers).json() == {"items": [], "total": 0}


def test_project_rejects_non_http_url_and_requires_authentication(tmp_path: Path):
    with make_client(tmp_path) as client:
        response = client.post("/api/projects", json={**project_payload(), "url": "ftp://example.com"})
        unauthenticated = client.get("/api/projects")

    assert response.status_code == 401
    assert unauthenticated.status_code == 401


def test_project_validation_rejects_non_http_url_after_login(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        response = client.post("/api/projects", json={**project_payload(), "url": "ftp://example.com"}, headers=headers)

    assert response.status_code == 422
