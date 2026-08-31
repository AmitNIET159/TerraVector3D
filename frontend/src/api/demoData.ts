import type {
  BuildingData, Parcel, Building, Level, SpatialUnit,
  PropertyRight, TopologyConflict, SourceMetadata,
  TopologyValidateResponse, GeospatialFloorsResponse, ReportGenerateResponse,
} from '@/types';

const ULPIN = '7A4B9C2D8E1F6G';

const parcel: Parcel = {
  parcel_id: 'P-0001', parent_ulpin: ULPIN, area_sqm: 300, land_use: 'residential',
  survey_number: 'SUR-2026-GH-001', boundary: [[0,0],[20,0],[20,15],[0,15],[0,0]],
};

const building: Building = {
  building_id: 'BLD001', parent_ulpin: ULPIN, building_name: 'Green Heights Apartment',
  total_height_m: 19, num_floors: 7, construction_year: 2024,
  footprint: [[2,2],[18,2],[18,13],[2,13],[2,2]],
};

const levels: Level[] = [
  { level_id:'L-B1', building_id:'BLD001', level_code:'B1', level_number:-1, z_min_m:-3, z_max_m:0, floor_area_sqm:176, level_type:'basement' },
  { level_id:'L-G',  building_id:'BLD001', level_code:'G',  level_number:0,  z_min_m:0,  z_max_m:4, floor_area_sqm:176, level_type:'above_ground' },
  { level_id:'L-F01',building_id:'BLD001', level_code:'F01',level_number:1,  z_min_m:4,  z_max_m:7, floor_area_sqm:176, level_type:'above_ground' },
  { level_id:'L-F02',building_id:'BLD001', level_code:'F02',level_number:2,  z_min_m:7,  z_max_m:10, floor_area_sqm:176, level_type:'above_ground' },
  { level_id:'L-F03',building_id:'BLD001', level_code:'F03',level_number:3,  z_min_m:10,  z_max_m:13,floor_area_sqm:176, level_type:'above_ground' },
  { level_id:'L-F04',building_id:'BLD001', level_code:'F04',level_number:4,  z_min_m:13, z_max_m:16,floor_area_sqm:176, level_type:'above_ground' },
  { level_id:'L-F05',building_id:'BLD001', level_code:'F05',level_number:5,  z_min_m:16, z_max_m:19,floor_area_sqm:176, level_type:'above_ground' },
];

function u(id:string, vid:string, lc:string, type:string, fp:number[][], zMin:number, zMax:number, area:number, usage:string, status='valid'): SpatialUnit {
  return { unit_id:id, vertical_id:vid, parent_ulpin:ULPIN, building_id:'BLD001',
    level_code:lc, unit_type:type as any, footprint:fp, z_min_m:zMin, z_max_m:zMax,
    area_sqm:area, usage_type:usage as any, status };
}

const spatialUnits: SpatialUnit[] = [
  // B1 - Basement
  u('U001',`${ULPIN}-FB1-UPARK01-R01`,'B1','parking',  [[3,3],[9,3],[9,7],[3,7],[3,3]],     -3,0, 24,'parking'),
  u('U002',`${ULPIN}-FB1-UPARK02-R01`,'B1','parking',  [[10,3],[16,3],[16,7],[10,7],[10,3]], -3,0, 24,'parking'),
  u('U003',`${ULPIN}-FB1-UUTIL01-R01`,'B1','utility',  [[3,8],[16,8],[16,12],[3,12],[3,8]],  -3,0, 52,'utility'),
  u('U007',`${ULPIN}-FB1-UPARK03-R01`,'B1','parking',  [[3,13],[9,13],[9,17],[3,17],[3,13]], -3,0, 24,'parking'),
  u('U008',`${ULPIN}-FB1-UPARK04-R01`,'B1','parking',  [[10,13],[16,13],[16,17],[10,17],[10,13]], -3,0, 24,'parking'),
  // G - Ground
  u('U004',`${ULPIN}-FG-USHOP01-R01`, 'G','commercial',[[3,3],[10,3],[10,7],[3,7],[3,3]],     0,4, 28,'commercial'),
  u('U005',`${ULPIN}-FG-USHOP02-R01`, 'G','commercial',[[11,3],[17,3],[17,7],[11,7],[11,3]],  0,4, 24,'commercial'),
  u('U006',`${ULPIN}-FG-ULOB01-R01`,  'G','common_area',[[3,8],[17,8],[17,12],[3,12],[3,8]],  0,4, 56,'common_area'),
  // F01
  u('U101',`${ULPIN}-F01-UAPT101-R01`,'F01','apartment',[[3,3],[10,3],[10,12],[3,12],[3,3]],  4,7, 63,'residential'),
  u('U102',`${ULPIN}-F01-UAPT102-R01`,'F01','apartment',[[11,3],[17,3],[17,12],[11,12],[11,3]],4,7, 54,'residential'),
  // F02
  u('U201',`${ULPIN}-F02-UAPT201-R01`,'F02','apartment',[[3,3],[10,3],[10,12],[3,12],[3,3]],  7,10, 63,'residential'),
  u('U202',`${ULPIN}-F02-UAPT202-R01`,'F02','apartment',[[11,3],[17,3],[17,12],[11,12],[11,3]],7,10, 54,'residential'),
  // F03
  u('U301',`${ULPIN}-F03-UAPT301-R01`,'F03','apartment',[[3,3],[10,3],[10,12],[3,12],[3,3]],  10,13, 63,'residential'),
  u('U302',`${ULPIN}-F03-UAPT302-R01`,'F03','apartment',[[11,3],[17,3],[17,12],[11,12],[11,3]],10,13, 54,'residential'),
  // F04 - CONFLICT FLOOR
  u('U401',`${ULPIN}-F04-UAPT401-R01`,'F04','apartment',[[3,3],[11,3],[11,12],[3,12],[3,3]],  13,16, 72,'residential'),
  u('U402',`${ULPIN}-F04-UAPT402-R01`,'F04','apartment',[[10,8.6],[17,8.6],[17,12],[10,12],[10,8.6]],13,16, 23.8,'residential','needs_review'),
  // F05
  u('U501',`${ULPIN}-F05-UAPT501-R01`,'F05','apartment',[[3,3],[10,3],[10,12],[3,12],[3,3]],  16,19, 63,'residential'),
  u('U502',`${ULPIN}-F05-UAPT502-R01`,'F05','apartment',[[11,3],[17,3],[17,12],[11,12],[11,3]],16,19, 54,'residential'),
];

const propertyRights: PropertyRight[] = [
  { right_id:'R001', unit_id:'U004', right_type:'ownership', holder_name_masked:'A***t K***r', record_status:'active', document_reference:'DOC-2026-001', start_date:'2024-03-15' },
  { right_id:'R002', unit_id:'U101', right_type:'ownership', holder_name_masked:'S***a M***a', record_status:'active', document_reference:'DOC-2026-002', start_date:'2024-06-01' },
  { right_id:'R003', unit_id:'U201', right_type:'ownership', holder_name_masked:'R***h P***l', record_status:'active', document_reference:'DOC-2026-003', start_date:'2024-06-01' },
  { right_id:'R004', unit_id:'U301', right_type:'ownership', holder_name_masked:'P***a S***h', record_status:'active', document_reference:'DOC-2026-004', start_date:'2024-07-20' },
  { right_id:'R005', unit_id:'U401', right_type:'ownership', holder_name_masked:'M***a G***a', record_status:'active', document_reference:'DOC-2026-005', start_date:'2024-08-10' },
  { right_id:'R006', unit_id:'U402', right_type:'ownership', holder_name_masked:'V***l R***n', record_status:'needs_review', document_reference:'DOC-2026-006', start_date:'2024-08-10' },
  { right_id:'R007', unit_id:'U501', right_type:'ownership', holder_name_masked:'N***a D***i', record_status:'active', document_reference:'DOC-2026-007', start_date:'2024-09-05' },
];

const conflicts: TopologyConflict[] = [
  {
    conflict_id: 'CONF-F04-001', conflict_type: 'VOLUME_OVERLAP', severity: 'high',
    affected_unit_ids: ['U401','U402'],
    affected_vertical_ids: [`${ULPIN}-F04-UAPT401-R01`,`${ULPIN}-F04-UAPT402-R01`],
    horizontal_overlap_area_sqm: 3.4, overlapping_z_min_m: 13, overlapping_z_max_m: 16,
    estimated_overlap_volume_cum: 10.2,
    recommended_action: 'Resurvey unit boundaries on Floor 4 and update geometry records.',
    human_readable_explanation: 'Apartments 401 and 402 have overlapping boundaries on Floor 4. The overlap region of 3.4 m² across the full 3.0 m floor height produces 10.2 m³ of contested volume.',
  },
];

const sourceMetadata: SourceMetadata[] = [
  {
    source_id: 'SRC-001', source_file_name: 'green_heights_scan.ply',
    source_type: 'pointcloud', timestamp: '2026-08-15T10:30:00Z',
    confidence: 0.87,
    sha256_hash: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
  },
];

export const DEMO_BUILDING_DATA: BuildingData = {
  parcel, building, levels, spatialUnits, propertyRights, conflicts, sourceMetadata, confidence: 0.87,
};

// Pre-computed demo responses for actions
export const DEMO_TOPOLOGY_RESULT: TopologyValidateResponse = {
  building_id: 'BLD001', parent_ulpin: ULPIN, total_units: spatialUnits.length,
  total_conflicts: 1, conflicts_by_severity: { low:0, medium:0, high:1 },
  conflicts_by_type: { VOLUME_OVERLAP: 1 }, conflicts, is_valid: false,
};

export const DEMO_FLOOR_DETECTION: GeospatialFloorsResponse = {
  parent_ulpin: ULPIN, coordinate_reference: 'LOCAL_METERS',
  detected_slab_elevations_m: [-3, 0, 4, 7, 10, 13, 16, 19],
  estimated_floor_height_m: 3.0,
  suggested_levels: levels.map((l) => ({
    level_code: l.level_code, level_type: l.level_type === 'basement' ? 'basement' : l.level_number === 0 ? 'ground' : 'floor',
    is_cadastral_unit_level: true, slab_z_m: l.z_min_m,
    z_min_m: l.z_min_m, z_max_m: l.z_max_m, point_count: 12400 + Math.floor(Math.random()*2000),
    confidence_score: 0.82 + Math.random()*0.12,
    warnings: l.level_type === 'basement' ? ['Limited scan coverage in basement area'] : [],
    human_verification_required: l.level_type === 'basement',
  })),
  method_agreement_score: 0.91, warnings: ['Point density below optimal in basement region'],
  human_verification_required: true,
};

export const DEMO_REPORT_RESULT: ReportGenerateResponse = {
  html_path: '/reports/bhudrishti_evidence_7A4B9C2D8E1F6G.html',
  pdf_path: '/reports/bhudrishti_evidence_7A4B9C2D8E1F6G.pdf',
  manifest_path: '/reports/manifest.json',
  manifest: {
    generated_at: new Date().toISOString(), parent_ulpin: ULPIN,
    building_id: 'BLD001', total_units: spatialUnits.length,
    total_conflicts: 1, overall_confidence: 0.87,
    report_type: 'full_evidence', format_version: '1.0.0',
  },
};
