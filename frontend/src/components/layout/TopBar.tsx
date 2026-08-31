import { useBuildingStore } from '@/store/buildingStore';

export default function TopBar() {
  const data = useBuildingStore((s) => s.data);
  const isDemoMode = useBuildingStore((s) => s.isDemoMode);
  const validationResult = useBuildingStore((s) => s.validationResult);

  const validationBadge = validationResult
    ? validationResult.is_valid
      ? { text: 'VALIDATED', color: 'bg-emerald-100 text-emerald-700 border-emerald-300' }
      : { text: `${validationResult.total_conflicts} CONFLICT${validationResult.total_conflicts > 1 ? 'S' : ''}`, color: 'bg-red-100 text-red-700 border-red-300' }
    : { text: 'NOT VALIDATED', color: 'bg-gray-100 text-gray-500 border-gray-300' };

  return (
    <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-slate-200 shrink-0 z-50 shadow-sm relative">
      {/* Left: Brand */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-600 to-emerald-800 flex items-center justify-center shadow-md border border-emerald-900/10">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12l10-8 10 8"></path><path d="M12 22V12"></path><path d="M22 12l-10 8-10-8"></path></svg>
        </div>
        <div>
          <h1 className="text-[15px] font-bold tracking-tight">
            <span className="text-emerald-700">BhuDrishti</span>{' '}
            <span className="text-slate-700">3D</span>
          </h1>
          <p className="text-[10px] font-medium text-slate-400 uppercase tracking-widest mt-[-2px]">Geospatial Command Center</p>
        </div>
        <span className="ml-2 text-[10px] text-emerald-600 font-bold border border-emerald-200 bg-emerald-50 rounded px-1.5 py-0.5">
          v0.1.0
        </span>
      </div>

      {/* Center: Parcel info */}
      <div className="flex items-center gap-4">
        {data && (
          <>
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-4 py-1.5 shadow-inner">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Active Parcel ULPIN</span>
              <span className="font-mono text-[13px] font-bold text-slate-800">{data.parcel.parent_ulpin}</span>
            </div>
          </>
        )}
      </div>

      {/* Right: Status */}
      <div className="flex items-center gap-3">
        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-md border tracking-wider shadow-sm ${validationBadge.color}`}>
          {validationBadge.text}
        </span>
        {isDemoMode && (
          <span className="text-[10px] font-bold px-2.5 py-1 rounded-md bg-amber-100 text-amber-800 border border-amber-300 tracking-wider shadow-sm flex items-center gap-1.5">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12h4l2-9 4 18 2-9h4"></path></svg>
            DEMO MODE
          </span>
        )}
      </div>
    </header>
  );
}
