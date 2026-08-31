"""Report generation endpoint."""
from fastapi import APIRouter, HTTPException
from app.schemas.validation import ReportGenerateRequest, ReportGenerateResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
_service = ReportService()

@router.post("/generate", response_model=ReportGenerateResponse)
def generate_report(request: ReportGenerateRequest):
    try:
        return _service.generate(validation_data=request.validation_data, output_dir=request.output_dir)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
