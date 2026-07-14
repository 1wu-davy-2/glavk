from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import Settings
from backend.app.db import Base
from backend.app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.sqlite3'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'auth.sqlite3'}",
        auth_secret_key="test-auth-secret-key-with-enough-length",
        admin_username="admin",
        admin_password="admin@123",
        auth_token_ttl_days=30,
    )
    return TestClient(create_app(settings=settings, session_factory=session_factory))


def test_login_creates_default_admin_and_returns_30_day_token(tmp_path: Path):
    with make_client(tmp_path) as client:
        response = client.post("/api/auth/login", json={"username": "admin", "password": "admin@123"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 30 * 24 * 60 * 60
    assert body["expires_at"] >= int(time.time()) + body["expires_in"] - 2
    assert body["user"] == {"username": "admin", "is_active": True}
    assert body["access_token"]


def test_login_rejects_invalid_credentials_without_revealing_account_state(tmp_path: Path):
    with make_client(tmp_path) as client:
        response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_me_requires_and_accepts_bearer_token(tmp_path: Path):
    with make_client(tmp_path) as client:
        login = client.post("/api/auth/login", json={"username": "admin", "password": "admin@123"})
        token = login.json()["access_token"]

        assert client.get("/api/auth/me").status_code == 401
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"username": "admin", "is_active": True}
