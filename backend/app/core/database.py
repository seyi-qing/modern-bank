"""
Database setup - SQLAlchemy 2.0 style.

On Vercel serverless, local SQLite under /tmp is ephemeral and NOT shared
across instances — that causes login 200 then /me 401. Use Postgres
(Neon / Vercel Postgres) via DATABASE_URL in production.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


def _resolve_database_url() -> str:
    url = (settings.DATABASE_URL or "").strip()
    # Neon / Vercel sometimes give postgres:// — SQLAlchemy wants postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql") or url.startswith("mysql"):
        return url
    # Serverless + SQLite file: /tmp only (demo; multi-instance flaky)
    if url.startswith("sqlite") and (
        os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    ):
        return "sqlite:////tmp/modern_bank.db"
    return url or "sqlite:///./modern_bank.db"


DATABASE_URL = _resolve_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG and os.environ.get("VERCEL") != "1",
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
