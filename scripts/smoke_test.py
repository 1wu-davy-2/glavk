from __future__ import annotations

import json
import os
import urllib.request


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


def main() -> None:
    health_status, health = request("/api/health")
    assert health_status == 200 and health["status"] == "ok"
    login_status, login = request("/api/auth/login", method="POST", body={"username": USERNAME, "password": PASSWORD})
    assert login_status == 200 and login["user"]["username"] == USERNAME
    projects_status, projects = request("/api/projects", token=login["access_token"])
    assert projects_status == 200 and "items" in projects and "total" in projects
    print(f"glavk smoke test passed: health=ok, login=ok, projects={projects['total']}")


if __name__ == "__main__":
    main()

