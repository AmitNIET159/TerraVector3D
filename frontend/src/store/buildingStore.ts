import { create } from 'zustand';
import type {
  BuildingData, Level, SpatialUnit, PropertyRight, TopologyConflict,
  TopologyValidateResponse, GeospatialFloorsResponse, ReportGenerateResponse,
} from '@/types';

export type FloorFilter = 'ALL' | string; // level_code or 'ALL'

interface BuildingStore {
  // Data
  data: BuildingData | null;
  isDemoMode: boolean;

  // Selection
  selectedFloor: FloorFilter;
  selectedUnitId: string | null;
  selectedUnit: SpatialUnit | null;
  selectedUnitRights: PropertyRight[];

  // View
  isExploded: boolean;
  cameraPreset: 'default' | 'top' | 'isometric';

  // Validation
  validationResult: TopologyValidateResponse | null;
  isValidating: boolean;

  // Conflict
  activeConflict: TopologyConflict | null;

  // Floor detection
  floorDetection: GeospatialFloorsResponse | null;
  isDetectingFloors: boolean;

  // Report
  reportResult: ReportGenerateResponse | null;
  isGeneratingReport: boolean;

  // Actions
  loadData: (data: BuildingData) => void;
  selectFloor: (floor: FloorFilter) => void;
  selectUnit: (unitId: string | null) => void;
  toggleExplode: () => void;
  setCameraPreset: (preset: 'default' | 'top' | 'isometric') => void;
  setValidationResult: (result: TopologyValidateResponse | null) => void;
  setIsValidating: (v: boolean) => void;
  showConflict: (conflict: TopologyConflict | null) => void;
  setFloorDetection: (result: GeospatialFloorsResponse | null) => void;
  setIsDetectingFloors: (v: boolean) => void;
  setReportResult: (result: ReportGenerateResponse | null) => void;
  setIsGeneratingReport: (v: boolean) => void;
  resetScene: () => void;

  // Derived helpers
  getVisibleUnits: () => SpatialUnit[];
  getLevelUnits: (levelCode: string) => SpatialUnit[];
  getUnitRight: (unitId: string) => PropertyRight | undefined;
}

export const useBuildingStore = create<BuildingStore>((set, get) => ({
  data: null,
  isDemoMode: true,
  selectedFloor: 'ALL',
  selectedUnitId: null,
  selectedUnit: null,
  selectedUnitRights: [],
  isExploded: false,
  cameraPreset: 'default',
  validationResult: null,
  isValidating: false,
  activeConflict: null,
  floorDetection: null,
  isDetectingFloors: false,
  reportResult: null,
  isGeneratingReport: false,

  loadData: (data) => set({ data, isDemoMode: true }),

  selectFloor: (floor) => {
    const state = get();
    // If a unit is selected but not on this floor, deselect
    if (state.selectedUnit && floor !== 'ALL' && state.selectedUnit.level_code !== floor) {
      set({ selectedFloor: floor, selectedUnitId: null, selectedUnit: null, selectedUnitRights: [] });
    } else {
      set({ selectedFloor: floor });
    }
  },

  selectUnit: (unitId) => {
    const state = get();
    if (!unitId || !state.data) {
      set({ selectedUnitId: null, selectedUnit: null, selectedUnitRights: [] });
      return;
    }
    const unit = state.data.spatialUnits.find((su) => su.unit_id === unitId) ?? null;
    const rights = unit ? state.data.propertyRights.filter((r) => r.unit_id === unitId) : [];
    set({ selectedUnitId: unitId, selectedUnit: unit, selectedUnitRights: rights });
  },

  toggleExplode: () => set((s) => ({ isExploded: !s.isExploded })),
  setCameraPreset: (preset) => set({ cameraPreset: preset }),
  setValidationResult: (result) => set({ validationResult: result }),
  setIsValidating: (v) => set({ isValidating: v }),
  showConflict: (conflict) => set({ activeConflict: conflict }),
  setFloorDetection: (result) => set({ floorDetection: result }),
  setIsDetectingFloors: (v) => set({ isDetectingFloors: v }),
  setReportResult: (result) => set({ reportResult: result }),
  setIsGeneratingReport: (v) => set({ isGeneratingReport: v }),

  resetScene: () => set({
    selectedFloor: 'ALL', selectedUnitId: null, selectedUnit: null,
    selectedUnitRights: [], isExploded: false, cameraPreset: 'default',
    activeConflict: null, validationResult: null, floorDetection: null, reportResult: null,
  }),

  getVisibleUnits: () => {
    const { data, selectedFloor } = get();
    if (!data) return [];
    if (selectedFloor === 'ALL') return data.spatialUnits;
    return data.spatialUnits.filter((su) => su.level_code === selectedFloor);
  },

  getLevelUnits: (levelCode) => {
    const { data } = get();
    return data?.spatialUnits.filter((su) => su.level_code === levelCode) ?? [];
  },

  getUnitRight: (unitId) => {
    const { data } = get();
    return data?.propertyRights.find((r) => r.unit_id === unitId);
  },
}));
