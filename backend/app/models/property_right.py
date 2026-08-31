"""Property Right ORM model."""
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.spatial_unit import SpatialUnit

class PropertyRight(TimestampMixin, Base):
    __tablename__ = "property_rights"
    right_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    unit_id: Mapped[str] = mapped_column(String(50), ForeignKey("spatial_units.unit_id", ondelete="CASCADE"), nullable=False, index=True)
    right_type: Mapped[str] = mapped_column(String(50), nullable=False)
    holder_name_masked: Mapped[str] = mapped_column(String(200), nullable=False)
    record_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    document_reference: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    spatial_unit: Mapped["SpatialUnit"] = relationship("SpatialUnit", back_populates="property_rights")
