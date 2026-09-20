from __future__ import annotations

from sqlalchemy import make_url

from app.config import Settings


def test_db_env_builds_url_with_encoded_password(monkeypatch):
    monkeypatch.setenv("DB_HOST", "101.43.75.72")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USER", "root")
    monkeypatch.setenv("DB_PASSWORD", "p@ss:w/rd#1")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    url = make_url(Settings().database_url)

    assert url.host == "101.43.75.72"
    assert url.port == 3306
    assert url.username == "root"
    assert url.password == "p@ss:w/rd#1"
    assert url.database == "glavk"


def test_db_env_falls_back_to_database_url(monkeypatch):
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./local.db")

    assert Settings().database_url == "sqlite:///./local.db"


def test_db_env_default_port_and_name(monkeypatch):
    monkeypatch.setenv("DB_HOST", "db.lan")
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    url = make_url(Settings().database_url)

    assert url.host == "db.lan"
    assert url.port == 3306
    assert url.database == "glavk"
