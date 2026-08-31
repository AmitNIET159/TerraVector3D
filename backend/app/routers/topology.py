"""Topology validation endpoint."""
from fastapi import APIRouter, HTTPException
from app.schemas.validation import TopologyValidateRequest, TopologyValidateResponse
from app.services.topology_service import TopologyService

router = APIRouter(prefix="/topology", tags=["topology"])
_service = TopologyService()

@router.post("/validate", response_model=TopologyValidateResponse)
def validate_topology(request: TopologyValidateRequest):
    try:
        return _service.validate(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
