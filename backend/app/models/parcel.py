"""Parcel ORM model."""
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.building import Building
    from app.models.spatial_unit import SpatialUnit

class Parcel(TimestampMixin, Base):
    __tablename__ = "parcels"
    parcel_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_ulpin: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    area_sqm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    land_use: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    survey_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    boundary = mapped_column(Geometry("POLYGON", srid=0), nullable=True)
    buildings: Mapped[List["Building"]] = relationship("Building", back_populates="parcel", cascade="all, delete-orphan")
    spatial_units: Mapped[List["SpatialUnit"]] = relationship("SpatialUnit", back_populates="parcel")
