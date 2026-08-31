"""Tests for SQLAlchemy ORM model definitions."""
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.parcel import Parcel
from app.models.building import Building

def test_parcel_tablename():
    assert Parcel.__tablename__ == "parcels"

def test_building_tablename():
    assert Building.__tablename__ == "buildings"
