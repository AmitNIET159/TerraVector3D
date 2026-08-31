interface Props {
  score: number; // 0–1
  humanVerificationRequired?: boolean;
}

export default function ConfidenceIndicator({ score, humanVerificationRequired }: Props) {
  const percentage = (score * 100).toFixed(1);
  const isHigh = score >= 0.8;
  const isMedium = score >= 0.5 && score < 0.8;

  const barColor = isHigh ? 'bg-emerald-500' : isMedium ? 'bg-amber-500' : 'bg-red-500';
  const textColor = isHigh ? 'text-emerald-700' : isMedium ? 'text-amber-700' : 'text-red-700';
  const label = isHigh ? 'HIGH' : isMedium ? 'MEDIUM' : 'LOW';

  return (
    <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm space-y-3">
      <div className="flex items-end justify-between">
        <span className={`text-2xl font-bold font-mono tracking-tight ${textColor}`}>{percentage}%</span>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-widest border ${
          isHigh ? 'bg-emerald-50 border-emerald-200 text-emerald-700' :
          isMedium ? 'bg-amber-50 border-amber-200 text-amber-700' :
          'bg-red-50 border-red-200 text-red-700'
        }`}>{label}</span>
      </div>

      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-1000 ${barColor}`} style={{ width: `${percentage}%` }} />
      </div>

      {humanVerificationRequired && (
        <div className="flex items-start gap-2 text-[11px] font-bold text-amber-700 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          <p>Human Verification Required. AI output must not be used as final legal approval.</p>
        </div>
      )}
    </div>
  );
}
