"""Spatial unit endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.spatial_unit import SpatialUnit
from app.schemas.spatial_unit import SpatialUnitResponse
from app.schemas.common import validate_vertical_id

router = APIRouter(prefix="/spatial-units", tags=["spatial-units"])

@router.get("/{unit_id}", response_model=SpatialUnitResponse)
def get_spatial_unit(unit_id: str, db: Session = Depends(get_db)):
    unit = db.query(SpatialUnit).filter(SpatialUnit.unit_id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail=f"Spatial unit '{unit_id}' not found")
    return unit

@router.get("/vertical/{vertical_id}", response_model=SpatialUnitResponse)
def get_spatial_unit_by_vertical_id(vertical_id: str, db: Session = Depends(get_db)):
    try:
        validate_vertical_id(vertical_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    unit = db.query(SpatialUnit).filter(SpatialUnit.vertical_id == vertical_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail=f"Spatial unit with vertical ID '{vertical_id}' not found")
    return unit
