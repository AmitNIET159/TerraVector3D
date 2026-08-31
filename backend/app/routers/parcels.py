"""Parcel endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.parcel import Parcel
from app.schemas.parcel import ParcelResponse
from app.schemas.common import validate_parent_ulpin

router = APIRouter(prefix="/parcels", tags=["parcels"])

@router.get("", response_model=List[ParcelResponse])
def list_parcels(db: Session = Depends(get_db)):
    return db.query(Parcel).all()

@router.get("/{parent_ulpin}", response_model=ParcelResponse)
def get_parcel(parent_ulpin: str, db: Session = Depends(get_db)):
    try:
        validate_parent_ulpin(parent_ulpin)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    parcel = db.query(Parcel).filter(Parcel.parent_ulpin == parent_ulpin).first()
    if not parcel:
        raise HTTPException(status_code=404, detail=f"Parcel with ULPIN '{parent_ulpin}' not found")
    return parcel
