"""Rights validation endpoint."""
from fastapi import APIRouter, HTTPException
from app.schemas.validation import RightsValidateRequest, RightsValidateResponse
from app.services.identity_service import IdentityService

router = APIRouter(prefix="/rights", tags=["rights"])
_service = IdentityService()

@router.post("/validate", response_model=RightsValidateResponse)
def validate_rights(request: RightsValidateRequest):
    try:
        return _service.validate_rights(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
