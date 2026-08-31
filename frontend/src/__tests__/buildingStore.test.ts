import { describe, it, expect, beforeEach } from 'vitest';
import { useBuildingStore } from '@/store/buildingStore';
import { DEMO_BUILDING_DATA } from '@/api/demoData';

describe('buildingStore', () => {
  beforeEach(() => {
    useBuildingStore.setState({
      data: null, selectedFloor: 'ALL', selectedUnitId: null,
      selectedUnit: null, selectedUnitRights: [], isExploded: false,
      activeConflict: null, validationResult: null,
    });
  });

  it('loads building data', () => {
    useBuildingStore.getState().loadData(DEMO_BUILDING_DATA);
    expect(useBuildingStore.getState().data).toBeTruthy();
    expect(useBuildingStore.getState().data!.building.building_name).toBe('Green Heights Apartment');
  });

  it('selects a floor', () => {
    useBuildingStore.getState().loadData(DEMO_BUILDING_DATA);
    useBuildingStore.getState().selectFloor('F04');
    expect(useBuildingStore.getState().selectedFloor).toBe('F04');
  });

  it('selects a unit and loads rights', () => {
    useBuildingStore.getState().loadData(DEMO_BUILDING_DATA);
    useBuildingStore.getState().selectUnit('U401');
    const state = useBuildingStore.getState();
    expect(state.selectedUnit).toBeTruthy();
    expect(state.selectedUnit!.unit_id).toBe('U401');
    expect(state.selectedUnit!.vertical_id).toContain('F04-UAPT401');
    expect(state.selectedUnitRights.length).toBeGreaterThan(0);
  });

  it('toggles explode view', () => {
    expect(useBuildingStore.getState().isExploded).toBe(false);
    useBuildingStore.getState().toggleExplode();
    expect(useBuildingStore.getState().isExploded).toBe(true);
  });

  it('shows and clears conflict', () => {
    useBuildingStore.getState().loadData(DEMO_BUILDING_DATA);
    const conflict = DEMO_BUILDING_DATA.conflicts[0];
    useBuildingStore.getState().showConflict(conflict);
    expect(useBuildingStore.getState().activeConflict).toBeTruthy();
    useBuildingStore.getState().showConflict(null);
    expect(useBuildingStore.getState().activeConflict).toBeNull();
  });

  it('resets scene', () => {
    useBuildingStore.getState().loadData(DEMO_BUILDING_DATA);
    useBuildingStore.getState().selectFloor('F04');
    useBuildingStore.getState().selectUnit('U401');
    useBuildingStore.getState().toggleExplode();
    useBuildingStore.getState().resetScene();
    const state = useBuildingStore.getState();
    expect(state.selectedFloor).toBe('ALL');
    expect(state.selectedUnitId).toBeNull();
    expect(state.isExploded).toBe(false);
  });

  it('getVisibleUnits filters by floor', async () => {
    await useBuildingStore.getState().loadData(DEMO_BUILDING_DATA);
    useBuildingStore.getState().selectFloor('B1');
    const visible = useBuildingStore.getState().getVisibleUnits();
    expect(visible.every((u) => u.level_code === 'B1')).toBe(true);
    expect(visible.length).toBe(5);
  });
});
