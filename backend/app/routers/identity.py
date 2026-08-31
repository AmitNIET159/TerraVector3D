"""Identity (vertical ID) endpoints."""
from fastapi import APIRouter, HTTPException
from app.schemas.validation import IdentityGenerateRequest, IdentityGenerateResponse, IdentityValidateRequest, IdentityValidateResponse
from app.services.identity_service import IdentityService

router = APIRouter(prefix="/identity", tags=["identity"])
_service = IdentityService()

@router.post("/generate", response_model=IdentityGenerateResponse)
def generate_identity(request: IdentityGenerateRequest):
    try:
        return _service.generate(parent_ulpin=request.parent_ulpin, level=request.level, unit_code=request.unit_code, revision=request.revision)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/validate", response_model=IdentityValidateResponse)
def validate_identity(request: IdentityValidateRequest):
    try:
        return _service.validate(request.vertical_id)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
