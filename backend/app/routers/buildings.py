"""Building endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.building import Building
from app.schemas.building import BuildingResponse

router = APIRouter(prefix="/buildings", tags=["buildings"])

@router.get("/{building_id}", response_model=BuildingResponse)
def get_building(building_id: str, db: Session = Depends(get_db)):
    building = db.query(Building).filter(Building.building_id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Building '{building_id}' not found")
    return building
