from __future__ import annotations

from app.config import DEFAULT_SQLITE_URL, Settings


def test_database_url_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert Settings().database_url == DEFAULT_SQLITE_URL


def test_database_url_env_overrides_default(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:////app/data/glavk.sqlite3")

    assert Settings().database_url == "sqlite:////app/data/glavk.sqlite3"
