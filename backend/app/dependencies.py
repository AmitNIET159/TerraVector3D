"""FastAPI dependency injection providers."""

from typing import Generator

from fastapi import HTTPException
from sqlalchemy.orm import Session


def get_db() -> Generator[Session, None, None]:
    """Provide a database session. Raises 503 if DB is unavailable."""
    try:
        from app.database import SessionLocal
        db = SessionLocal()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Ensure PostgreSQL + PostGIS is running.",
        )
    try:
        yield db
    finally:
        db.close()
