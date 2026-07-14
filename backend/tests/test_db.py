from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from backend.app.db import ensure_schema


def test_ensure_schema_adds_screenshot_column_to_existing_database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.sqlite3'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE web_projects (id VARCHAR(36) PRIMARY KEY, name VARCHAR(120) NOT NULL)"))

    ensure_schema(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("web_projects")}
    assert "screenshot_path" in columns
