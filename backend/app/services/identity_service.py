"""Service adapter for bhudrishti_identity_rights module."""
from app.services.module_adapter import ensure_module_path
ensure_module_path()

from modules.bhudrishti_identity_rights.src import (
    generate_vertical_id, validate_vertical_id, validate_rights_record, build_human_readable_label
)

class IdentityService:
    def generate(self, parent_ulpin: str, level: str, unit_code: str, revision: int = 1) -> dict:
        vertical_id = generate_vertical_id(parent_ulpin, level, unit_code, revision)
        label = build_human_readable_label(vertical_id)
        return {"vertical_id": vertical_id, "human_readable_label": label}

    def validate(self, vertical_id: str) -> dict:
        result = validate_vertical_id(vertical_id)
        return result.model_dump() if hasattr(result, "model_dump") else {
            "is_valid": result.is_valid, "errors": result.errors, "warnings": result.warnings
        }

    def validate_rights(self, record: dict) -> dict:
        result = validate_rights_record(record)
        return result.model_dump() if hasattr(result, "model_dump") else {
            "status": result.status.value if hasattr(result.status, "value") else result.status,
            "errors": result.errors, "warnings": result.warnings, "audit_explanation": result.audit_explanation
        }
