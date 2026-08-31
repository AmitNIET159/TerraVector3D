import { describe, it, expect } from 'vitest';
import { DEMO_BUILDING_DATA, DEMO_TOPOLOGY_RESULT, DEMO_FLOOR_DETECTION } from '@/api/demoData';

describe('demoData', () => {
  it('has correct ULPIN', () => {
    expect(DEMO_BUILDING_DATA.parcel.parent_ulpin).toBe('7A4B9C2D8E1F6G');
    expect(DEMO_BUILDING_DATA.parcel.parent_ulpin).toMatch(/^[A-Z0-9]{14}$/);
  });

  it('has 7 levels', () => {
    expect(DEMO_BUILDING_DATA.levels.length).toBe(7);
  });

  it('has correct level codes', () => {
    const codes = DEMO_BUILDING_DATA.levels.map((l) => l.level_code).sort();
    expect(codes).toEqual(['B1', 'F01', 'F02', 'F03', 'F04', 'F05', 'G']);
  });

  it('has conflict on F04', () => {
    const conflict = DEMO_BUILDING_DATA.conflicts[0];
    expect(conflict.conflict_type).toBe('VOLUME_OVERLAP');
    expect(conflict.affected_unit_ids).toContain('U401');
    expect(conflict.affected_unit_ids).toContain('U402');
    expect(conflict.estimated_overlap_volume_cum).toBe(10.2);
  });

  it('vertical IDs match pattern', () => {
    const pattern = /^[A-Z0-9]{14}-F(G|B[1-9]|[0-9]{2})-U[A-Z0-9]{1,16}-R[0-9]{2}$/;
    DEMO_BUILDING_DATA.spatialUnits.forEach((u) => {
      expect(u.vertical_id).toMatch(pattern);
    });
  });

  it('topology result reflects conflict', () => {
    expect(DEMO_TOPOLOGY_RESULT.is_valid).toBe(false);
    expect(DEMO_TOPOLOGY_RESULT.total_conflicts).toBe(1);
  });

  it('floor detection has correct slab count', () => {
    expect(DEMO_FLOOR_DETECTION.detected_slab_elevations_m.length).toBe(8);
    expect(DEMO_FLOOR_DETECTION.estimated_floor_height_m).toBe(3.0);
  });
});
