import type { BuildingData, TopologyValidateResponse, GeospatialFloorsResponse, ReportGenerateResponse } from '@/types';
import { DEMO_BUILDING_DATA, DEMO_TOPOLOGY_RESULT, DEMO_FLOOR_DETECTION, DEMO_REPORT_RESULT } from './demoData';
import * as api from './endpoints';

let _backendAvailable: boolean | null = null;

export async function checkBackend(): Promise<boolean> {
  if (_backendAvailable !== null) return _backendAvailable;
  try {
    await api.getHealth();
    _backendAvailable = true;
  } catch {
    _backendAvailable = false;
  }
  return _backendAvailable;
}

export async function loadBuildingData(): Promise<BuildingData> {
  // Always start with demo data; live data can augment later
  return DEMO_BUILDING_DATA;
}

export async function runTopologyValidation(): Promise<TopologyValidateResponse> {
  const isLive = await checkBackend();
  if (isLive) {
    try {
      const data = DEMO_BUILDING_DATA;
      return await api.validateTopology({
        building_id: data.building.building_id,
        parent_ulpin: data.building.parent_ulpin,
        footprint: data.building.footprint!,
        levels: data.levels.map((l) => ({ level_code: l.level_code, z_min_m: l.z_min_m, z_max_m: l.z_max_m })),
        total_height_m: data.building.total_height_m,
        spatial_units: data.spatialUnits.map((su) => ({
          unit_id: su.unit_id, vertical_id: su.vertical_id,
          parent_ulpin: su.parent_ulpin, building_id: su.building_id,
          level_code: su.level_code, unit_type: su.unit_type,
          footprint: su.footprint, z_min_m: su.z_min_m, z_max_m: su.z_max_m,
          area_sqm: su.area_sqm, usage_type: su.usage_type, status: su.status,
        })),
      });
    } catch { /* fall through to demo */ }
  }
  // Simulate processing delay
  await new Promise((r) => setTimeout(r, 1500));
  return DEMO_TOPOLOGY_RESULT;
}

export async function runFloorDetection(): Promise<GeospatialFloorsResponse> {
  const isLive = await checkBackend();
  if (isLive) {
    try {
      // Generate synthetic point cloud for demo
      const points: number[][] = [];
      for (let z = -3; z <= 18; z += 0.3) {
        for (let i = 0; i < 20; i++) {
          points.push([Math.random()*16+2, Math.random()*11+2, z + (Math.random()-0.5)*0.1]);
        }
      }
      return await api.detectFloors(points);
    } catch { /* fall through */ }
  }
  await new Promise((r) => setTimeout(r, 2000));
  return DEMO_FLOOR_DETECTION;
}

export async function runReportGeneration(): Promise<ReportGenerateResponse> {
  const isLive = await checkBackend();
  if (isLive) {
    try {
      const d = DEMO_BUILDING_DATA;
      return await api.generateReport({
        parent_ulpin: d.parcel.parent_ulpin,
        timestamp: new Date().toISOString(),
        generated_by: 'BhuDrishti 3D Frontend',
        confidence_scores: { overall: d.confidence },
        parcel: d.parcel, building: d.building,
        levels: d.levels, spatial_units: d.spatialUnits,
        property_rights: d.propertyRights,
        topology_conflicts: d.conflicts,
        source_metadata: d.sourceMetadata,
      });
    } catch { /* fall through */ }
  }
  await new Promise((r) => setTimeout(r, 1800));
  return DEMO_REPORT_RESULT;
}
