interface Props { verticalId: string; }

export default function VerticalIdDisplay({ verticalId }: Props) {
  // Parse: <ULPIN>-F<level>-U<unit>-R<rev>
  const parts = verticalId.split('-');
  const ulpin = parts[0] || '';
  const floorPart = parts[1] || '';
  const unitPart = parts[2] || '';
  const revPart = parts[3] || '';

  const floorLabel = floorPart.startsWith('F')
    ? floorPart.slice(1) === 'G' ? 'Ground' : floorPart.slice(1).startsWith('B') ? `Basement ${floorPart.slice(2)}` : `Floor ${parseInt(floorPart.slice(1), 10)}`
    : floorPart;
  const unitCode = unitPart.startsWith('U') ? unitPart.slice(1) : unitPart;
  const rev = revPart.startsWith('R') ? revPart.slice(1) : revPart;

  const copyToClipboard = () => navigator.clipboard?.writeText(verticalId);

  return (
    <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Vertical ID</span>
        <button onClick={copyToClipboard} className="text-slate-400 hover:text-emerald-600 transition-colors bg-white p-1.5 rounded-md shadow-sm border border-slate-200" title="Copy to clipboard">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        </button>
      </div>

      {/* Official structured display */}
      <div className="flex flex-wrap gap-1 mb-3">
        <span className="bg-emerald-100 text-emerald-800 font-mono text-sm px-2 py-1 rounded border border-emerald-200 font-bold tracking-wide">{ulpin}</span>
        <span className="text-slate-300 self-center font-bold">-</span>
        <span className="bg-blue-100 text-blue-800 font-mono text-sm px-2 py-1 rounded border border-blue-200 font-bold tracking-wide">{floorPart}</span>
        <span className="text-slate-300 self-center font-bold">-</span>
        <span className="bg-amber-100 text-amber-800 font-mono text-sm px-2 py-1 rounded border border-amber-200 font-bold tracking-wide">{unitPart}</span>
        <span className="text-slate-300 self-center font-bold">-</span>
        <span className="bg-slate-200 text-slate-700 font-mono text-sm px-2 py-1 rounded border border-slate-300 font-bold tracking-wide">{revPart}</span>
      </div>

      {/* Breakdown Legend */}
      <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-[10px] font-medium text-slate-500 bg-white p-2.5 rounded-lg border border-slate-100">
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-emerald-400"></div>Parent Parcel</div>
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-blue-400"></div>{floorLabel}</div>
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-amber-400"></div>Unit {unitCode}</div>
        <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-slate-400"></div>Revision {rev}</div>
      </div>
    </div>
  );
}
