"""
Database setup - SQLAlchemy 2.0 style.
On Vercel serverless, SQLite uses /tmp (ephemeral but seed runs on cold start).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


def _resolve_database_url() -> str:
    url = settings.DATABASE_URL
    # Serverless / read-only FS: force SQLite into /tmp
    if url.startswith("sqlite") and (
        os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    ):
        return "sqlite:////tmp/modern_bank.db"
    return url


DATABASE_URL = _resolve_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG and os.environ.get("VERCEL") != "1",
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
