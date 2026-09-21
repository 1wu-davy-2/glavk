from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

SQLITE_PREFIX = "sqlite:///"


class Base(DeclarativeBase):
    pass


def sqlite_file_path(database_url: str) -> Path | None:
    """返回 SQLite 数据文件路径；内存库、file: URI 和非 SQLite 连接串返回 None。"""
    if not database_url.startswith(SQLITE_PREFIX):
        return None
    raw = database_url[len(SQLITE_PREFIX) :]
    if not raw or raw.startswith(":memory:") or raw.startswith("file:"):
        return None
    return Path(raw)


def prepare_sqlite_file(database_url: str) -> None:
    """SQLite 不会自建父目录，缺目录时只报一句 "unable to open database file"，先建好。"""
    path = sqlite_file_path(database_url)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)


def _enable_sqlite_pragmas(engine) -> None:
    """保存项目时会同时抓截图，容器内存在并发写，WAL + busy_timeout 避免 database is locked。"""

    @event.listens_for(engine, "connect")
    def _apply(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
        finally:
            cursor.close()


def ensure_schema(engine) -> None:
    """建表，并给已存在的旧库补上后来新增的列（create_all 不会改已存在的表）。"""
    Base.metadata.create_all(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("web_projects")}
    if "screenshot_path" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE web_projects ADD COLUMN screenshot_path VARCHAR(500)"))


def create_session_factory(database_url: str):
    is_sqlite = database_url.startswith("sqlite")
    if is_sqlite:
        prepare_sqlite_file(database_url)
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        pool_pre_ping=True,
    )
    if is_sqlite:
        _enable_sqlite_pragmas(engine)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def session_dependency(session_factory) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
