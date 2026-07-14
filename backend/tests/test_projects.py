from __future__ import annotations

import base64
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import Settings
from backend.app.db import Base
from backend.app.main import create_app
from backend.tests.helpers import login_payload, make_envelope


class FakeScreenshotService:
    def __init__(self, root: Path):
        self.root = root

    def capture(self, project_id: str, url: str) -> str:
        if "capture-fails" in url:
            raise RuntimeError("capture failed")
        self.root.mkdir(parents=True, exist_ok=True)
        relative_path = f"{project_id}.png"
        (self.root / relative_path).write_bytes(b"fake-png")
        return relative_path

    def resolve_path(self, relative_path: str) -> Path:
        return self.root / relative_path

    def delete(self, relative_path: str | None) -> None:
        if relative_path:
            (self.root / relative_path).unlink(missing_ok=True)


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
    return TestClient(
        create_app(
            settings=settings,
            session_factory=session_factory,
            screenshot_service=FakeScreenshotService(tmp_path / "screenshots"),
        )
    )


def login_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/login", json=login_payload(client))
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def project_payload(client: TestClient, *, username: str = "crm-admin", password: str | None = "crm-secret") -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "客户管理后台",
        "url": "https://crm.example.com/login",
        "category": "业务系统",
        "description": "客户资料和销售流程",
        "notes": "工作日使用",
        "is_favorite": True,
        "is_enabled": True,
    }
    if username or password:
        public_key = client.get("/api/security/transport-key").json()["public_key"]
        payload["credential_envelope"] = make_envelope(
            public_key,
            {"username": username, "password": password},
        )
    return payload


def client_key() -> tuple[rsa.RSAPrivateKey, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key, base64.b64encode(public_key_der).decode("ascii")


def decrypt_client_envelope(private_key: rsa.RSAPrivateKey, envelope: dict[str, str]) -> dict[str, str | None]:
    aes_key = private_key.decrypt(
        base64.b64decode(envelope["wrapped_key"]),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    plaintext = AESGCM(aes_key).decrypt(
        base64.b64decode(envelope["iv"]),
        base64.b64decode(envelope["ciphertext"]),
        None,
    )
    import json

    return json.loads(plaintext.decode("utf-8"))


def test_project_crud_masks_password_and_reveals_it_separately(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        created = client.post("/api/projects", json=project_payload(client), headers=headers)
        project_id = created.json()["id"]

        assert created.status_code == 201
        assert created.json()["password_masked"] == "********"
        assert created.json()["has_credentials"] is True
        assert created.json()["has_screenshot"] is True
        assert "password" not in created.json()

        listed = client.get("/api/projects?search=客户&category=业务系统", headers=headers)
        private_key, public_key = client_key()
        credential = client.get(
            f"/api/projects/{project_id}/credential",
            headers={**headers, "X-Client-Public-Key": public_key},
        )

        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["name"] == "客户管理后台"
        assert listed.json()["items"][0]["password_masked"] == "********"
        assert listed.json()["items"][0]["username"] == ""
        assert "crm-secret" not in credential.text
        assert decrypt_client_envelope(private_key, credential.json()["envelope"]) == {
            "username": "crm-admin",
            "password": "crm-secret",
        }

        updated = client.put(
            f"/api/projects/{project_id}",
            json={
                "name": "客户运营后台",
                "credential_envelope": make_envelope(
                    client.get("/api/security/transport-key").json()["public_key"],
                    {"username": "crm-admin", "password": "new-secret"},
                ),
                "is_favorite": False,
            },
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "客户运营后台"
        assert updated.json()["is_favorite"] is False

        updated_credential = client.get(
            f"/api/projects/{project_id}/credential",
            headers={**headers, "X-Client-Public-Key": public_key},
        )
        assert decrypt_client_envelope(private_key, updated_credential.json()["envelope"])["password"] == "new-secret"

        screenshot = client.get(f"/api/projects/{project_id}/screenshot", headers=headers)
        assert screenshot.status_code == 200
        assert screenshot.headers["content-type"] == "image/png"
        assert screenshot.content == b"fake-png"

        deleted = client.delete(f"/api/projects/{project_id}", headers=headers)
        assert deleted.status_code == 204
        assert client.get("/api/projects", headers=headers).json() == {"items": [], "total": 0}


def test_project_rejects_non_http_url_and_requires_authentication(tmp_path: Path):
    with make_client(tmp_path) as client:
        response = client.post("/api/projects", json={**project_payload(client), "url": "ftp://example.com"})
        unauthenticated = client.get("/api/projects")

    assert response.status_code == 401
    assert unauthenticated.status_code == 401


def test_project_validation_rejects_non_http_url_after_login(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        response = client.post("/api/projects", json={**project_payload(client), "url": "ftp://example.com"}, headers=headers)

    assert response.status_code == 422


def test_project_can_be_created_without_login_credentials(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        response = client.post("/api/projects", json=project_payload(client, username="", password=None), headers=headers)

    assert response.status_code == 201
    assert response.json()["has_credentials"] is False
    assert response.json()["password_masked"] == ""
    assert response.json()["has_screenshot"] is True


def test_project_save_survives_screenshot_failure(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        payload = project_payload(client, username="", password=None)
        payload["url"] = "https://capture-fails.example.com"
        response = client.post("/api/projects", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["has_screenshot"] is False


def test_project_allows_only_one_credential_field(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        response = client.post(
            "/api/projects",
            json=project_payload(client, username="only-user", password=None),
            headers=headers,
        )
        private_key, public_key = client_key()
        credential = client.get(
            f"/api/projects/{response.json()['id']}/credential",
            headers={**headers, "X-Client-Public-Key": public_key},
        )

    assert response.status_code == 201
    assert response.json()["has_credentials"] is True
    assert decrypt_client_envelope(private_key, credential.json()["envelope"]) == {
        "username": "only-user",
        "password": None,
    }


def test_updating_only_username_preserves_existing_password(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        created = client.post("/api/projects", json=project_payload(client), headers=headers)
        project_id = created.json()["id"]
        public_key = client.get("/api/security/transport-key").json()["public_key"]
        updated = client.put(
            f"/api/projects/{project_id}",
            json={"credential_envelope": make_envelope(public_key, {"username": "new-admin"})},
            headers=headers,
        )
        private_key, client_public_key = client_key()
        credential = client.get(
            f"/api/projects/{project_id}/credential",
            headers={**headers, "X-Client-Public-Key": client_public_key},
        )

    assert updated.status_code == 200
    assert decrypt_client_envelope(private_key, credential.json()["envelope"]) == {
        "username": "new-admin",
        "password": "crm-secret",
    }


def test_updating_only_password_preserves_existing_username(tmp_path: Path):
    with make_client(tmp_path) as client:
        headers = login_headers(client)
        created = client.post("/api/projects", json=project_payload(client), headers=headers)
        project_id = created.json()["id"]
        public_key = client.get("/api/security/transport-key").json()["public_key"]
        updated = client.put(
            f"/api/projects/{project_id}",
            json={"credential_envelope": make_envelope(public_key, {"password": "new-secret"})},
            headers=headers,
        )
        private_key, client_public_key = client_key()
        credential = client.get(
            f"/api/projects/{project_id}/credential",
            headers={**headers, "X-Client-Public-Key": client_public_key},
        )

    assert updated.status_code == 200
    assert decrypt_client_envelope(private_key, credential.json()["envelope"]) == {
        "username": "crm-admin",
        "password": "new-secret",
    }
