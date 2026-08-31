import type { TopologyConflict } from '@/types';
import { useBuildingStore } from '@/store/buildingStore';

interface Props { conflict: TopologyConflict; }

export default function ConflictPanel({ conflict }: Props) {
  const setCameraPreset = useBuildingStore((s) => s.setCameraPreset);
  const selectFloor = useBuildingStore((s) => s.selectFloor);
  const selectUnit = useBuildingStore((s) => s.selectUnit);
  const isExploded = useBuildingStore((s) => s.isExploded);
  const toggleExplode = useBuildingStore((s) => s.toggleExplode);

  const focusConflict = () => {
    setCameraPreset('isometric');
    if (!isExploded) toggleExplode();
    if (conflict.affected_unit_ids[0]) selectUnit(conflict.affected_unit_ids[0]);
  };

  return (
    <div className="bg-white rounded-xl p-4 border border-red-200 shadow-sm relative overflow-hidden">
      {/* Decorative red glow */}
      <div className="absolute -top-10 -right-10 w-24 h-24 bg-red-400 rounded-full blur-3xl opacity-20 pointer-events-none" />
      
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-bold uppercase tracking-widest text-red-600 bg-red-50 px-2.5 py-1 rounded-md border border-red-100">
          {conflict.severity} SEVERITY
        </span>
        <button onClick={focusConflict} className="text-[10px] font-bold text-red-700 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-md border border-red-200 transition-colors shadow-sm flex items-center gap-1.5 z-10 relative">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          Show in 3D
        </button>
      </div>

      <div className="font-mono text-[13px] font-bold text-red-900 mb-2 truncate" title={conflict.conflict_type}>{conflict.conflict_type.replace(/_/g, ' ')}</div>
      
      <div className="text-[12px] font-medium text-slate-500 mb-2">
        <span className="text-slate-800">{conflict.affected_unit_ids.join(' ↔ ')}</span>
      </div>

      <div className="bg-red-50/80 rounded-lg p-3 border border-red-100 mb-3 text-[11px] font-medium text-red-800 leading-relaxed shadow-inner">
        {conflict.human_readable_explanation}
      </div>

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-slate-50 border border-slate-200 rounded p-2">
          <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest">Overlap Area</span>
          <span className="block text-xs font-bold text-slate-800">{conflict.horizontal_overlap_area_sqm} m²</span>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded p-2">
          <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest">Volume</span>
          <span className="block text-xs font-bold text-red-600">{conflict.estimated_overlap_volume_cum} m³</span>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded p-2 col-span-2">
          <span className="block text-[9px] font-bold text-slate-400 uppercase tracking-widest">Z Range</span>
          <span className="block text-xs font-bold text-slate-800">{conflict.overlapping_z_min_m}m → {conflict.overlapping_z_max_m}m</span>
        </div>
      </div>

      <div className="text-[10px] text-slate-600 leading-relaxed border-t border-slate-100 pt-3">
        <strong className="text-slate-800 block mb-0.5 tracking-wider uppercase font-bold text-[9px]">Recommended Action</strong>
        {conflict.recommended_action}
      </div>
    </div>
  );
}
