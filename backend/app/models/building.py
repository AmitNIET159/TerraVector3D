"""Building ORM model."""
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.parcel import Parcel
    from app.models.level import Level
    from app.models.spatial_unit import SpatialUnit

class Building(TimestampMixin, Base):
    __tablename__ = "buildings"
    building_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    parent_ulpin: Mapped[str] = mapped_column(String(14), ForeignKey("parcels.parent_ulpin", ondelete="CASCADE"), nullable=False, index=True)
    building_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    total_height_m: Mapped[float] = mapped_column(Float, nullable=False)
    num_floors: Mapped[int] = mapped_column(Integer, nullable=False)
    construction_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    footprint = mapped_column(Geometry("POLYGON", srid=0), nullable=True)
    parcel: Mapped["Parcel"] = relationship("Parcel", back_populates="buildings")
    levels: Mapped[List["Level"]] = relationship("Level", back_populates="building", cascade="all, delete-orphan")
    spatial_units: Mapped[List["SpatialUnit"]] = relationship("SpatialUnit", back_populates="building")
