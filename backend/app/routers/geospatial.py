"""Geospatial processing endpoints."""
from fastapi import APIRouter, HTTPException
from app.schemas.validation import GeospatialNormalizeRequest, GeospatialNormalizeResponse, GeospatialFloorsRequest, GeospatialFloorsResponse
from app.services.geospatial_service import GeospatialService

router = APIRouter(prefix="/geospatial", tags=["geospatial"])
_service = GeospatialService()

@router.post("/normalize", response_model=GeospatialNormalizeResponse)
def normalize_geojson(request: GeospatialNormalizeRequest):
    try:
        return _service.normalize(request.geojson_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/floors", response_model=GeospatialFloorsResponse)
def detect_floors(request: GeospatialFloorsRequest):
    try:
        return _service.detect_floors(point_cloud_data=request.point_cloud_data, merge_tolerance_m=request.merge_tolerance_m)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
