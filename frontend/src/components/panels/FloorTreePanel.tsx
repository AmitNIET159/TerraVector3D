import { useBuildingStore } from '@/store/buildingStore';
import type { FloorFilter } from '@/store/buildingStore';

const LEVEL_LABELS: Record<string, string> = {
  B1: 'Basement 1', G: 'Ground', F01: 'Floor 1', F02: 'Floor 2',
  F03: 'Floor 3', F04: 'Floor 4', F05: 'Floor 5',
};

const LEVEL_ICONS: Record<string, string> = {
  B1: '⬇', G: '🏛', F01: '🏢', F02: '🏢', F03: '🏢', F04: '🏢', F05: '🏢',
};

export default function FloorTreePanel() {
  const data = useBuildingStore((s) => s.data);
  const selectedFloor = useBuildingStore((s) => s.selectedFloor);
  const selectFloor = useBuildingStore((s) => s.selectFloor);
  const isExploded = useBuildingStore((s) => s.isExploded);
  const toggleExplode = useBuildingStore((s) => s.toggleExplode);
  const setCameraPreset = useBuildingStore((s) => s.setCameraPreset);
  const resetScene = useBuildingStore((s) => s.resetScene);
  const activeConflict = useBuildingStore((s) => s.activeConflict);

  if (!data) return null;

  const sortedLevels = [...data.levels].sort((a, b) => b.level_number - a.level_number);

  const handleFloor = (code: FloorFilter) => {
    selectFloor(selectedFloor === code ? 'ALL' : code);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/50">
      {/* Building Info */}
      <div className="p-5 border-b border-slate-200 bg-white">
        <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 21h18"></path><path d="M9 8h1"></path><path d="M9 12h1"></path><path d="M9 16h1"></path><path d="M14 8h1"></path><path d="M14 12h1"></path><path d="M14 16h1"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path></svg>
          Property Context
        </h2>
        <div className="space-y-1.5">
          <p className="text-[15px] font-bold text-slate-800 tracking-tight">{data.building.building_name}</p>
          <div className="flex flex-wrap gap-2 text-[11px] font-medium text-slate-500">
            <span className="bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{data.building.num_floors} Floors</span>
            <span className="bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{data.building.total_height_m}m Height</span>
            <span className="bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{data.spatialUnits.length} Units</span>
          </div>
        </div>
      </div>

      {/* Floor List */}
      <div className="p-5 flex-1 overflow-y-auto">
        <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
          Spatial Hierarchy
        </h2>

        {/* Show All */}
        <button
          onClick={() => selectFloor('ALL')}
          className={`w-full text-left px-4 py-2.5 rounded-lg text-xs font-bold mb-2 transition-all shadow-sm ${
            selectedFloor === 'ALL'
              ? 'bg-emerald-600 text-white shadow-emerald-600/20'
              : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300 hover:bg-slate-50'
          }`}
        >
          View Entire Complex
        </button>

        <div className="space-y-1.5 mt-2">
          {sortedLevels.map((level) => {
            const unitCount = data.spatialUnits.filter((su) => su.level_code === level.level_code).length;
            const isActive = selectedFloor === level.level_code;
            const hasConflict = activeConflict?.affected_unit_ids.some((id) =>
              data.spatialUnits.find((su) => su.unit_id === id && su.level_code === level.level_code)
            );

            return (
              <button
                key={level.level_id}
                onClick={() => handleFloor(level.level_code)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition-all border ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300 shadow-sm'
                    : 'bg-white text-slate-600 hover:bg-slate-50 hover:border-slate-300 border-slate-200 shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded flex items-center justify-center font-bold text-sm ${isActive ? 'bg-emerald-200/50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                      {level.level_code}
                    </div>
                    <div>
                      <span className="font-bold block text-[13px]">{LEVEL_LABELS[level.level_code]}</span>
                      <span className="text-[10px] text-slate-400 font-medium">{level.z_min_m}m → {level.z_max_m}m</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {hasConflict && <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]" title="Conflict Detected" />}
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isActive ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                      {unitCount} units
                    </span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* View Controls */}
      <div className="p-5 border-t border-slate-200 bg-white space-y-3">
        <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1 flex items-center gap-2">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
          Camera & Display
        </h2>
        <div className="grid grid-cols-3 gap-1.5">
          <button onClick={() => setCameraPreset('default')} className="text-[10px] font-bold py-2 rounded-md bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors">
            Default
          </button>
          <button onClick={() => setCameraPreset('top')} className="text-[10px] font-bold py-2 rounded-md bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors">
            Top
          </button>
          <button onClick={() => setCameraPreset('isometric')} className="text-[10px] font-bold py-2 rounded-md bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors">
            Isometric
          </button>
        </div>
        <div className="flex gap-2">
          <button
            onClick={toggleExplode}
            className={`flex-1 text-[11px] font-bold py-2.5 rounded-md transition-all border shadow-sm ${
              isExploded ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            {isExploded ? 'Collapse View' : 'Explode View'}
          </button>
          <button onClick={resetScene} className="px-3 text-[11px] font-bold py-2.5 rounded-md bg-white hover:bg-slate-50 text-slate-500 border border-slate-200 transition-colors shadow-sm" title="Reset View">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
          </button>
        </div>
      </div>
    </div>
  );
}
