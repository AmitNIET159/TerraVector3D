"""Validation Run ORM model."""
import uuid
from typing import Optional, Any
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class ValidationRun(TimestampMixin, Base):
    __tablename__ = "validation_runs"
    run_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_ulpin: Mapped[str] = mapped_column(String(14), nullable=False)
    building_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    run_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result_summary: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    source_metadata_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("source_metadata.source_id"), nullable=True)
