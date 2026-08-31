import type { PropertyRight } from '@/types';

interface Props { rights: PropertyRight[]; }

export default function RightsCard({ rights }: Props) {
  if (rights.length === 0) {
    return <div className="text-[10px] text-slate-400 font-medium bg-slate-50 p-3 rounded-lg border border-slate-100">No registered rights found.</div>;
  }

  return (
    <div className="space-y-3">
      {rights.map((r) => (
        <div key={r.right_id} className="bg-white rounded-lg p-3 border border-slate-200 shadow-sm relative overflow-hidden">
          {/* subtle left colored border based on status */}
          <div className={`absolute left-0 top-0 bottom-0 w-1 ${r.record_status === 'active' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
          
          <div className="flex items-center justify-between mb-2 ml-1">
            <span className="text-[11px] font-bold text-slate-800 capitalize tracking-wide">{r.right_type.replace(/_/g, ' ')}</span>
            <span className={`text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded-sm ${
              r.record_status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
            }`}>
              {r.record_status}
            </span>
          </div>

          <div className="ml-1 space-y-1.5">
            <div className="text-[12px] font-mono font-semibold text-slate-600 bg-slate-50 px-2 py-1 rounded border border-slate-100">
              {r.holder_name_masked}
            </div>
            <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
              <div className="font-mono bg-slate-50 px-1.5 rounded" title="Document Reference">{r.document_reference}</div>
              <div className="font-medium">Since: {r.start_date}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
