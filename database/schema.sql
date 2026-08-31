CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. parcels
CREATE TABLE parcels (
    parcel_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_ulpin VARCHAR(14) NOT NULL UNIQUE,
    area_sqm DOUBLE PRECISION,
    land_use VARCHAR(100),
    survey_number VARCHAR(100),
    boundary GEOMETRY(POLYGON, 0),  -- SRID 0 = local Cartesian metres
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. buildings
CREATE TABLE buildings (
    building_id VARCHAR(50) PRIMARY KEY,
    parent_ulpin VARCHAR(14) NOT NULL REFERENCES parcels(parent_ulpin) ON DELETE CASCADE,
    building_name VARCHAR(200),
    total_height_m DOUBLE PRECISION NOT NULL,
    num_floors INTEGER NOT NULL,
    construction_year INTEGER,
    footprint GEOMETRY(POLYGON, 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. levels
CREATE TABLE levels (
    level_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    building_id VARCHAR(50) NOT NULL REFERENCES buildings(building_id) ON DELETE CASCADE,
    level_code VARCHAR(10) NOT NULL,
    level_number INTEGER NOT NULL,
    z_min_m DOUBLE PRECISION NOT NULL,
    z_max_m DOUBLE PRECISION NOT NULL,
    floor_area_sqm DOUBLE PRECISION,
    level_type VARCHAR(50) NOT NULL DEFAULT 'above_ground',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_level_z CHECK (z_min_m < z_max_m)
);

-- 4. spatial_units
CREATE TABLE spatial_units (
    unit_id VARCHAR(50) PRIMARY KEY,
    vertical_id VARCHAR(100) NOT NULL UNIQUE,
    parent_ulpin VARCHAR(14) NOT NULL REFERENCES parcels(parent_ulpin),
    building_id VARCHAR(50) NOT NULL REFERENCES buildings(building_id),
    level_code VARCHAR(10) NOT NULL,
    unit_type VARCHAR(50) NOT NULL,
    footprint GEOMETRY(POLYGON, 0),
    z_min_m DOUBLE PRECISION NOT NULL,
    z_max_m DOUBLE PRECISION NOT NULL,
    area_sqm DOUBLE PRECISION NOT NULL,
    usage_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    model_object_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_unit_z CHECK (z_min_m < z_max_m)
);

-- 5. property_rights
CREATE TABLE property_rights (
    right_id VARCHAR(50) PRIMARY KEY,
    unit_id VARCHAR(50) NOT NULL REFERENCES spatial_units(unit_id) ON DELETE CASCADE,
    right_type VARCHAR(50) NOT NULL,
    holder_name_masked VARCHAR(200) NOT NULL,
    record_status VARCHAR(20) NOT NULL DEFAULT 'active',
    document_reference VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. topology_conflicts
CREATE TABLE topology_conflicts (
    conflict_id VARCHAR(50) PRIMARY KEY,
    conflict_type VARCHAR(50) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    affected_unit_ids JSONB NOT NULL DEFAULT '[]',
    affected_vertical_ids JSONB NOT NULL DEFAULT '[]',
    horizontal_overlap_area_sqm DOUBLE PRECISION NOT NULL DEFAULT 0,
    overlapping_z_min_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    overlapping_z_max_m DOUBLE PRECISION NOT NULL DEFAULT 0,
    estimated_overlap_volume_cum DOUBLE PRECISION NOT NULL DEFAULT 0,
    recommended_action TEXT NOT NULL,
    human_readable_explanation TEXT NOT NULL,
    validation_run_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_severity CHECK (severity IN ('low', 'medium', 'high'))
);

-- 7. source_metadata
CREATE TABLE source_metadata (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file_name VARCHAR(500) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_sha256 CHECK (sha256_hash ~ '^[a-f0-9]{64}$')
);

-- 8. validation_runs
CREATE TABLE validation_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_ulpin VARCHAR(14) NOT NULL,
    building_id VARCHAR(50),
    run_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    result_summary JSONB,
    source_metadata_id UUID REFERENCES source_metadata(source_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add FK from topology_conflicts to validation_runs
ALTER TABLE topology_conflicts
    ADD CONSTRAINT fk_conflict_validation_run
    FOREIGN KEY (validation_run_id) REFERENCES validation_runs(run_id);

-- INDEXES
CREATE INDEX idx_parcels_parent_ulpin ON parcels(parent_ulpin);
CREATE INDEX idx_buildings_parent_ulpin ON buildings(parent_ulpin);
CREATE INDEX idx_levels_building_id ON levels(building_id);
CREATE INDEX idx_levels_level_code ON levels(level_code);
CREATE INDEX idx_spatial_units_vertical_id ON spatial_units(vertical_id);
CREATE INDEX idx_spatial_units_parent_ulpin ON spatial_units(parent_ulpin);
CREATE INDEX idx_spatial_units_building_id ON spatial_units(building_id);
CREATE INDEX idx_spatial_units_level_code ON spatial_units(level_code);
CREATE INDEX idx_spatial_units_building_level ON spatial_units(building_id, level_code);
CREATE INDEX idx_property_rights_unit_id ON property_rights(unit_id);
CREATE INDEX idx_topology_conflicts_severity ON topology_conflicts(severity);
CREATE INDEX idx_topology_conflicts_type ON topology_conflicts(conflict_type);
CREATE INDEX idx_validation_runs_parent_ulpin ON validation_runs(parent_ulpin);
CREATE INDEX idx_validation_runs_building_id ON validation_runs(building_id);
