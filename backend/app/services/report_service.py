"""Service adapter for bhudrishti_evidence_reports module."""
import tempfile
from typing import Optional
from app.services.module_adapter import ensure_module_path
ensure_module_path()

from modules.bhudrishti_evidence_reports.src import generate_report

class ReportService:
    def generate(self, validation_data: dict, output_dir: Optional[str] = None) -> dict:
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="bhudrishti_report_")
        return generate_report(validation_data, output_dir=output_dir)
