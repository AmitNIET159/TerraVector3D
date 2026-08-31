"""Source Metadata ORM model."""
import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class SourceMetadata(TimestampMixin, Base):
    __tablename__ = "source_metadata"
    __table_args__ = (CheckConstraint("sha256_hash ~ '^[a-f0-9]{64}$'", name="chk_sha256"),)
    source_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
