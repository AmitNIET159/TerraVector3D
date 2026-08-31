-- Demo data for BhuDrishti 3D using canonical ULPIN 7A4B9C2D8E1F6G

INSERT INTO parcels (parent_ulpin, area_sqm, land_use, boundary)
VALUES (
    '7A4B9C2D8E1F6G',
    300.0,
    'residential',
    ST_GeomFromText('POLYGON((0 0, 20 0, 20 15, 0 15, 0 0))', 0)
);

INSERT INTO buildings (building_id, parent_ulpin, building_name, total_height_m, num_floors, footprint)
VALUES (
    'BLD001',
    '7A4B9C2D8E1F6G',
    'Demo Building',
    15.0,
    5,
    ST_GeomFromText('POLYGON((2 2, 18 2, 18 13, 2 13, 2 2))', 0)
);

-- Insert Levels
INSERT INTO levels (level_id, building_id, level_code, level_number, z_min_m, z_max_m, floor_area_sqm, level_type)
VALUES 
    (gen_random_uuid(), 'BLD001', 'B1', -1, -3.0, 0.0, 176.0, 'basement'),
    (gen_random_uuid(), 'BLD001', 'G', 0, 0.0, 3.0, 176.0, 'above_ground'),
    (gen_random_uuid(), 'BLD001', 'F01', 1, 3.0, 6.0, 176.0, 'above_ground');

-- Insert Spatial Units
INSERT INTO spatial_units (unit_id, vertical_id, parent_ulpin, building_id, level_code, unit_type, z_min_m, z_max_m, area_sqm, usage_type, footprint)
VALUES 
    ('U001', '7A4B9C2D8E1F6G-FB1-UPARK01-R01', '7A4B9C2D8E1F6G', 'BLD001', 'B1', 'parking', -3.0, 0.0, 15.0, 'parking', ST_GeomFromText('POLYGON((3 3, 6 3, 6 8, 3 8, 3 3))', 0)),
    ('U002', '7A4B9C2D8E1F6G-FG-USHOP01-R01', '7A4B9C2D8E1F6G', 'BLD001', 'G', 'commercial', 0.0, 3.0, 50.0, 'commercial', ST_GeomFromText('POLYGON((3 3, 10 3, 10 10, 3 10, 3 3))', 0)),
    ('U003', '7A4B9C2D8E1F6G-FF01-UAPT101-R01', '7A4B9C2D8E1F6G', 'BLD001', 'F01', 'apartment', 3.0, 6.0, 80.0, 'residential', ST_GeomFromText('POLYGON((3 3, 12 3, 12 12, 3 12, 3 3))', 0)),
    ('U004', '7A4B9C2D8E1F6G-FF01-UAPT102-R01', '7A4B9C2D8E1F6G', 'BLD001', 'F01', 'apartment', 3.0, 6.0, 80.0, 'residential', ST_GeomFromText('POLYGON((5 5, 15 5, 15 15, 5 15, 5 5))', 0)); -- Overlaps with U003

-- Insert Property Rights
INSERT INTO property_rights (right_id, unit_id, right_type, holder_name_masked, document_reference)
VALUES 
    ('R001', 'U002', 'ownership', 'A***t K***r', 'DOC-2026-001'),
    ('R002', 'U003', 'ownership', 'S***a M***a', 'DOC-2026-002');

-- Insert Source Metadata
INSERT INTO source_metadata (source_id, source_file_name, source_type, timestamp, confidence, sha256_hash)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'demo_scan.ply', 'pointcloud', NOW(), 0.95, 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2');

-- Insert Validation Run
INSERT INTO validation_runs (run_id, parent_ulpin, building_id, run_type, status, source_metadata_id)
VALUES 
    ('00000000-0000-0000-0000-000000000002', '7A4B9C2D8E1F6G', 'BLD001', 'topology', 'completed', '00000000-0000-0000-0000-000000000001');

-- Insert Topology Conflict
INSERT INTO topology_conflicts (conflict_id, conflict_type, severity, affected_unit_ids, affected_vertical_ids, horizontal_overlap_area_sqm, overlapping_z_min_m, overlapping_z_max_m, estimated_overlap_volume_cum, recommended_action, human_readable_explanation, validation_run_id)
VALUES 
    ('CONF001', 'VOLUME_OVERLAP', 'medium', '["U003", "U004"]', '["7A4B9C2D8E1F6G-FF01-UAPT101-R01", "7A4B9C2D8E1F6G-FF01-UAPT102-R01"]', 49.0, 3.0, 6.0, 147.0, 'Review unit boundaries', 'Apartments 101 and 102 have overlapping boundaries on Floor 1.', '00000000-0000-0000-0000-000000000002');
