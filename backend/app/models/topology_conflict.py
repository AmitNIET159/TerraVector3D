"""Topology Conflict ORM model."""
from typing import Optional
from sqlalchemy import String, Float, Text, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class TopologyConflict(TimestampMixin, Base):
    __tablename__ = "topology_conflicts"
    __table_args__ = (CheckConstraint("severity IN ('low', 'medium', 'high')", name="chk_severity"),)
    conflict_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    affected_unit_ids: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    affected_vertical_ids: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    horizontal_overlap_area_sqm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overlapping_z_min_m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overlapping_z_max_m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    estimated_overlap_volume_cum: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    human_readable_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    validation_run_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("validation_runs.run_id"), nullable=True)
