"""Pydantic schemas for validation and module integration requests/responses."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator, model_validator
from app.schemas.common import validate_parent_ulpin, validate_holder_masked, validate_z_range

class IdentityGenerateRequest(BaseModel):
    parent_ulpin: str
    level: str
    unit_code: str
    revision: int = 1

    @field_validator("parent_ulpin")
    @classmethod
    def check_ulpin(cls, v: str) -> str:
        return validate_parent_ulpin(v)

class IdentityGenerateResponse(BaseModel):
    vertical_id: str
    human_readable_label: Optional[str] = None

class IdentityValidateRequest(BaseModel):
    vertical_id: str

class IdentityValidateResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []

class RightsValidateRequest(BaseModel):
    vertical_id: str
    right_type: str
    holder_name_masked: str
    start_date: str
    end_date: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("holder_name_masked")
    @classmethod
    def check_holder(cls, v: str) -> str:
        return validate_holder_masked(v)

class RightsValidateResponse(BaseModel):
    status: str
    errors: List[str] = []
    warnings: List[str] = []
    audit_explanation: List[str] = []

class TopologyLevelInput(BaseModel):
    level_code: str
    z_min_m: float
    z_max_m: float

    @model_validator(mode="after")
    def check_z(self) -> "TopologyLevelInput":
        validate_z_range(self.z_min_m, self.z_max_m)
        return self

class TopologySpatialUnitInput(BaseModel):
    unit_id: str
    vertical_id: str
    parent_ulpin: str
    building_id: str
    level_code: str
    unit_type: str
    footprint: List[List[float]]
    z_min_m: float
    z_max_m: float
    area_sqm: float
    usage_type: str
    status: str = "pending"

class TopologyValidateRequest(BaseModel):
    building_id: str
    parent_ulpin: str
    footprint: List[List[float]]
    levels: List[TopologyLevelInput]
    total_height_m: float
    spatial_units: List[TopologySpatialUnitInput]

    @field_validator("parent_ulpin")
    @classmethod
    def check_ulpin(cls, v: str) -> str:
        return validate_parent_ulpin(v)

class TopologyValidateResponse(BaseModel):
    building_id: str
    parent_ulpin: str
    total_units: int
    total_conflicts: int
    conflicts_by_severity: Dict[str, int] = {}
    conflicts_by_type: Dict[str, int] = {}
    conflicts: List[Dict[str, Any]] = []
    is_valid: bool

class GeospatialNormalizeRequest(BaseModel):
    geojson_data: Dict[str, Any]

class GeospatialNormalizeResponse(BaseModel):
    parent_ulpin: str = ""
    footprint: List[Any] = []
    area_sqm: float = 0.0
    bounding_box: Dict[str, Any] = {}
    coordinate_reference: str = "LOCAL_METERS"
    source_type: str = ""
    confidence_score: float = 0.0
    warnings: List[str] = []
    human_verification_required: bool = True

class GeospatialFloorsRequest(BaseModel):
    point_cloud_data: List[List[float]]
    merge_tolerance_m: float = 0.5

class GeospatialFloorsResponse(BaseModel):
    parent_ulpin: str = ""
    coordinate_reference: str = "LOCAL_METERS"
    detected_slab_elevations_m: List[float] = []
    estimated_floor_height_m: float = 0.0
    suggested_levels: List[Dict[str, Any]] = []
    method_agreement_score: float = 0.0
    warnings: List[str] = []
    human_verification_required: bool = True

class ReportGenerateRequest(BaseModel):
    validation_data: Dict[str, Any]
    output_dir: Optional[str] = None

class ReportGenerateResponse(BaseModel):
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    manifest_path: Optional[str] = None
    manifest: Dict[str, Any] = {}
