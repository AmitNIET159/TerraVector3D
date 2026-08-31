"""
bhudrishti_evidence_reports — public API.

Provides five public functions for BhuDrishti 3D validation report generation:

    from bhudrishti_evidence_reports.src import (
        generate_report,
        generate_html_report,
        generate_pdf_report,
        create_verification_manifest,
        calculate_audit_hash,
    )
"""

from .report_generator import (
    generate_report,
    generate_html_report,
    generate_pdf_report,
    create_verification_manifest,
)
from .audit_hash import calculate_audit_hash
from .models import ValidationInput

__all__ = [
    "generate_report",
    "generate_html_report",
    "generate_pdf_report",
    "create_verification_manifest",
    "calculate_audit_hash",
    "ValidationInput",
]

