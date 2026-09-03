import { useBuildingStore } from '@/store/buildingStore';
import type { FloorFilter } from '@/store/buildingStore';

export default function FloorExplorer() {
  const data = useBuildingStore((s) => s.data);
  const selectedFloor = useBuildingStore((s) => s.selectedFloor);
  const selectFloor = useBuildingStore((s) => s.selectFloor);
  const isExploded = useBuildingStore((s) => s.isExploded);
  const toggleExplode = useBuildingStore((s) => s.toggleExplode);
  const activeConflict = useBuildingStore((s) => s.activeConflict);
  const showConflict = useBuildingStore((s) => s.showConflict);
  
  if (!data) return null;

  const floorOrder = ['F05', 'F04', 'F03', 'F02', 'F01', 'G', 'B1'];

  const handleFloorClick = (floor: string) => {
    const newFloor = selectedFloor === floor ? 'ALL' : floor;
    selectFloor(newFloor);
    
    if (newFloor === 'F04' && data.conflicts.length > 0) {
      showConflict(data.conflicts[0]);
    } else if (newFloor !== 'F04') {
      showConflict(null);
    }
  };

  const selectedLevel = data.levels.find(l => l.level_code === selectedFloor);
  const selectedUnitsCount = selectedLevel ? data.spatialUnits.filter(u => u.level_code === selectedFloor).length : 0;
  const selectedFloorHeight = selectedLevel ? selectedLevel.z_max_m - selectedLevel.z_min_m : 0;
  
  const hasConflict = (levelCode: string) => {
    return data.conflicts.some(c => 
      c.affected_unit_ids.some(id => data.spatialUnits.find(su => su.unit_id === id && su.level_code === levelCode))
    );
  };
  const selectedFloorConflicts = selectedLevel ? data.conflicts.filter(c => 
    c.affected_unit_ids.some(id => data.spatialUnits.find(su => su.unit_id === id && su.level_code === selectedFloor))
  ).length : 0;

  return (
    <div className="absolute left-6 top-6 bottom-6 z-20 flex gap-4 pointer-events-auto h-fit">
      {/* Floor Selector */}
      <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.08)] border border-slate-200 p-2 flex flex-col justify-between gap-1 w-16">
        <div className="flex flex-col gap-1">
          {floorOrder.map((f) => {
            const isSelected = selectedFloor === f;
            const conflict = hasConflict(f);
            return (
              <button
                key={f}
                onClick={() => handleFloorClick(f)}
                className={`relative py-3 rounded-xl font-bold text-xs transition-all flex justify-center items-center ${
                  isSelected ? 'bg-emerald-600 text-white shadow-md' : 'bg-transparent text-slate-600 hover:bg-slate-100'
                }`}
              >
                {f}
                {conflict && (
                  <span className={`absolute top-1 right-1 w-2 h-2 rounded-full ${isSelected ? 'bg-white' : 'bg-red-500'} shadow-sm`} />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Info Card & Controls */}
      <div className="flex flex-col gap-4">
        {selectedLevel && (
          <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.08)] border border-slate-200 p-4 w-64 animate-in fade-in slide-in-from-left-4">
            <h3 className="text-sm font-bold text-slate-800 mb-3 uppercase tracking-widest">{selectedLevel.level_type === 'basement' ? 'Basement' : 'Floor'} {selectedLevel.level_code}</h3>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Spatial Units</span>
                <span className="font-bold text-slate-800">{selectedUnitsCount}</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Approx. Height</span>
                <span className="font-bold text-slate-800">{selectedFloorHeight.toFixed(1)}m</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Conflicts</span>
                <span className={`font-bold ${selectedFloorConflicts > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  {selectedFloorConflicts}
                </span>
              </div>
            </div>

            {selectedFloorConflicts > 0 && selectedFloor === 'F04' && (
              <div className="p-2 bg-amber-50 rounded-lg border border-amber-200">
                 <p className="text-[10px] text-amber-800 font-bold mb-1">⚠ Conflict Detected</p>
                 <p className="text-[10px] text-amber-700">Units U401 and U402 overlap. Highlighted in 3D view.</p>
              </div>
            )}
          </div>
        )}

        <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.08)] border border-slate-200 p-2 flex flex-col gap-2 w-64 mt-auto">
          <button
            onClick={toggleExplode}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors border ${
              isExploded 
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            {isExploded ? 'Collapse View' : 'Exploded View'}
          </button>
          
          <button
            onClick={() => showConflict(activeConflict ? null : data.conflicts[0])}
            disabled={data.conflicts.length === 0}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-colors border ${
              activeConflict
                ? 'bg-red-50 text-red-700 border-red-200'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            } disabled:opacity-50`}
          >
            {activeConflict ? 'Hide Conflicts' : 'Show Conflicts'}
          </button>
        </div>
      </div>
    </div>
  );
}
