from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def ensure_schema(engine) -> None:
    Base.metadata.create_all(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("web_projects")}
    if "screenshot_path" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE web_projects ADD COLUMN screenshot_path VARCHAR(500) NULL"))


def create_session_factory(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def session_dependency(session_factory) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
