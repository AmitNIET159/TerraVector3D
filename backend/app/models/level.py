"""Level ORM model."""
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.building import Building

class Level(TimestampMixin, Base):
    __tablename__ = "levels"
    __table_args__ = (CheckConstraint("z_min_m < z_max_m", name="chk_level_z"),)
    level_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    building_id: Mapped[str] = mapped_column(String(50), ForeignKey("buildings.building_id", ondelete="CASCADE"), nullable=False, index=True)
    level_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    level_number: Mapped[int] = mapped_column(Integer, nullable=False)
    z_min_m: Mapped[float] = mapped_column(Float, nullable=False)
    z_max_m: Mapped[float] = mapped_column(Float, nullable=False)
    floor_area_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    level_type: Mapped[str] = mapped_column(String(50), nullable=False, default="above_ground")
    building: Mapped["Building"] = relationship("Building", back_populates="levels")
