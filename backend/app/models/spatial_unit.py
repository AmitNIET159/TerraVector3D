"""Spatial Unit ORM model."""
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.parcel import Parcel
    from app.models.building import Building
    from app.models.property_right import PropertyRight

class SpatialUnit(TimestampMixin, Base):
    __tablename__ = "spatial_units"
    __table_args__ = (CheckConstraint("z_min_m < z_max_m", name="chk_unit_z"),)
    unit_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    vertical_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    parent_ulpin: Mapped[str] = mapped_column(String(14), ForeignKey("parcels.parent_ulpin"), nullable=False, index=True)
    building_id: Mapped[str] = mapped_column(String(50), ForeignKey("buildings.building_id"), nullable=False, index=True)
    level_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    unit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    footprint = mapped_column(Geometry("POLYGON", srid=0), nullable=True)
    z_min_m: Mapped[float] = mapped_column(Float, nullable=False)
    z_max_m: Mapped[float] = mapped_column(Float, nullable=False)
    area_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    usage_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    model_object_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    parcel: Mapped["Parcel"] = relationship("Parcel", back_populates="spatial_units")
    building: Mapped["Building"] = relationship("Building", back_populates="spatial_units")
    property_rights: Mapped[List["PropertyRight"]] = relationship("PropertyRight", back_populates="spatial_unit", cascade="all, delete-orphan")
