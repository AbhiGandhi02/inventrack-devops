"""SQLAlchemy engine, session factory and the declarative base."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.settings import get_settings

_url = get_settings().database_url
# SQLite (used by the tests) needs this flag because TestClient runs requests in another thread
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
