// ── Domain Enums ──────────────────────────────────────────────
export type UnitType = 'apartment' | 'commercial' | 'parking' | 'utility' | 'common_area' | 'easement';
export type UsageType = 'residential' | 'commercial' | 'parking' | 'utility' | 'common_area' | 'easement';
export type Severity = 'low' | 'medium' | 'high';
export type ValidationStatus = 'pending' | 'valid' | 'needs_review' | 'invalid' | 'completed';
export type RightType = 'ownership' | 'lease' | 'parking_right' | 'utility_easement';
export type LevelType = 'basement' | 'above_ground';

// ── Core Domain Models ───────────────────────────────────────
export interface Parcel {
  parcel_id: string;
  parent_ulpin: string;
  area_sqm: number | null;
  land_use: string | null;
  survey_number: string | null;
  boundary?: number[][];
}

export interface Building {
  building_id: string;
  parent_ulpin: string;
  building_name: string | null;
  total_height_m: number;
  num_floors: number;
  construction_year: number | null;
  footprint?: number[][];
}

export interface Level {
  level_id: string;
  building_id: string;
  level_code: string;
  level_number: number;
  z_min_m: number;
  z_max_m: number;
  floor_area_sqm: number | null;
  level_type: LevelType;
}

export interface SpatialUnit {
  unit_id: string;
  vertical_id: string;
  parent_ulpin: string;
  building_id: string;
  level_code: string;
  unit_type: UnitType;
  footprint: number[][];
  z_min_m: number;
  z_max_m: number;
  area_sqm: number;
  usage_type: UsageType;
  status: string;
  model_object_name?: string | null;
}

export interface PropertyRight {
  right_id: string;
  unit_id: string;
  right_type: RightType;
  holder_name_masked: string;
  record_status: string;
  document_reference: string | null;
  start_date?: string;
  end_date?: string | null;
}

export interface TopologyConflict {
  conflict_id: string;
  conflict_type: string;
  severity: Severity;
  affected_unit_ids: string[];
  affected_vertical_ids: string[];
  horizontal_overlap_area_sqm: number;
  overlapping_z_min_m: number;
  overlapping_z_max_m: number;
  estimated_overlap_volume_cum: number;
  recommended_action: string;
  human_readable_explanation: string;
}

export interface SourceMetadata {
  source_id: string;
  source_file_name: string;
  source_type: string;
  timestamp: string;
  confidence: number;
  sha256_hash: string;
}

// ── API Request / Response ───────────────────────────────────
export interface HealthResponse {
  status: string;
  version: string;
  service: string;
}

export interface IdentityGenerateRequest {
  parent_ulpin: string;
  level: string;
  unit_code: string;
  revision?: number;
}
export interface IdentityGenerateResponse {
  vertical_id: string;
  human_readable_label: string | null;
}

export interface IdentityValidateRequest { vertical_id: string; }
export interface IdentityValidateResponse {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface RightsValidateRequest {
  vertical_id: string;
  right_type: string;
  holder_name_masked: string;
  start_date: string;
  end_date?: string | null;
  notes?: string | null;
}
export interface RightsValidateResponse {
  status: string;
  errors: string[];
  warnings: string[];
  audit_explanation: string[];
}

export interface TopologyValidateRequest {
  building_id: string;
  parent_ulpin: string;
  footprint: number[][];
  levels: { level_code: string; z_min_m: number; z_max_m: number }[];
  total_height_m: number;
  spatial_units: {
    unit_id: string; vertical_id: string; parent_ulpin: string;
    building_id: string; level_code: string; unit_type: string;
    footprint: number[][]; z_min_m: number; z_max_m: number;
    area_sqm: number; usage_type: string; status?: string;
  }[];
}
export interface TopologyValidateResponse {
  building_id: string;
  parent_ulpin: string;
  total_units: number;
  total_conflicts: number;
  conflicts_by_severity: Record<string, number>;
  conflicts_by_type: Record<string, number>;
  conflicts: TopologyConflict[];
  is_valid: boolean;
}

export interface GeospatialFloorsResponse {
  parent_ulpin: string;
  coordinate_reference: string;
  detected_slab_elevations_m: number[];
  estimated_floor_height_m: number;
  suggested_levels: {
    level_code: string; level_type: string; is_cadastral_unit_level: boolean;
    slab_z_m: number; z_min_m: number; z_max_m: number;
    point_count: number; confidence_score: number;
    warnings: string[]; human_verification_required: boolean;
  }[];
  method_agreement_score: number;
  warnings: string[];
  human_verification_required: boolean;
}

export interface ReportGenerateResponse {
  html_path: string | null;
  pdf_path: string | null;
  manifest_path: string | null;
  manifest: Record<string, unknown>;
}

// ── Composite view model ─────────────────────────────────────
export interface BuildingData {
  parcel: Parcel;
  building: Building;
  levels: Level[];
  spatialUnits: SpatialUnit[];
  propertyRights: PropertyRight[];
  conflicts: TopologyConflict[];
  sourceMetadata: SourceMetadata[];
  confidence: number;
}
