from __future__ import annotations

import base64
import json
import os
import urllib.request

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


BASE_URL = os.getenv("GLAVK_BASE_URL", "http://127.0.0.1:6555").rstrip("/")
USERNAME = os.getenv("ADMIN_USERNAME", "admin")
PASSWORD = os.getenv("ADMIN_PASSWORD", "admin@123")


def request(path: str, *, method: str = "GET", body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    request_object = urllib.request.Request(f"{BASE_URL}{path}", data=payload, headers=headers, method=method)
    with urllib.request.urlopen(request_object, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def encrypted_credentials(public_key_b64: str, username: str, password: str) -> dict[str, str]:
    public_key = serialization.load_der_public_key(base64.b64decode(public_key_b64))
    aes_key = AESGCM.generate_key(bit_length=256)
    iv = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(
        iv,
        json.dumps({"username": username, "password": password}).encode("utf-8"),
        None,
    )
    wrapped_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return {
        "version": "v1",
        "wrapped_key": base64.b64encode(wrapped_key).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def main() -> None:
    health_status, health = request("/api/health")
    assert health_status == 200 and health["status"] == "ok"
    key_status, transport_key = request("/api/security/transport-key")
    assert key_status == 200 and transport_key["public_key"]
    login_status, login = request(
        "/api/auth/login",
        method="POST",
        body={"credential_envelope": encrypted_credentials(transport_key["public_key"], USERNAME, PASSWORD)},
    )
    assert login_status == 200 and login["user"]["username"] == USERNAME
    projects_status, projects = request("/api/projects", token=login["access_token"])
    assert projects_status == 200 and "items" in projects and "total" in projects
    print(f"glavk smoke test passed: health=ok, login=ok, projects={projects['total']}")


if __name__ == "__main__":
    main()
