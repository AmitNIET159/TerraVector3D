import type { ReportGenerateResponse } from '@/types';
import LoadingState from '@/components/common/LoadingState';

interface Props {
  data: ReportGenerateResponse | null;
  loading: boolean;
  onClose: () => void;
}

export default function ReportDialog({ data, loading, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-[420px]" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Evidence Report</h2>
            <p className="text-[10px] text-gray-400 mt-0.5">Comprehensive cadastral evidence package</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">✕</button>
        </div>

        <div className="p-4">
          {loading && <LoadingState message="Generating evidence report..." />}

          {!loading && data && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 bg-emerald-50 rounded-lg p-3 border border-emerald-100">
                <span className="text-xl">✅</span>
                <div>
                  <p className="text-sm font-semibold text-emerald-700">Report Generated</p>
                  <p className="text-[10px] text-emerald-600">Evidence package ready for review</p>
                </div>
              </div>

              {data.html_path && (
                <div className="bg-gray-50 rounded px-3 py-2 border border-gray-100">
                  <span className="text-[10px] text-gray-400 block">HTML Report</span>
                  <span className="text-xs text-gray-700 font-mono truncate block">{data.html_path}</span>
                </div>
              )}

              {data.pdf_path && (
                <div className="bg-gray-50 rounded px-3 py-2 border border-gray-100">
                  <span className="text-[10px] text-gray-400 block">PDF Report</span>
                  <span className="text-xs text-gray-700 font-mono truncate block">{data.pdf_path}</span>
                </div>
              )}

              {data.manifest && Object.keys(data.manifest).length > 0 && (
                <div className="bg-gray-50 rounded px-3 py-2 border border-gray-100">
                  <span className="text-[10px] text-gray-400 block mb-1">Manifest</span>
                  <div className="grid grid-cols-2 gap-1 text-[10px]">
                    {Object.entries(data.manifest).map(([k, v]) => (
                      <div key={k}>
                        <span className="text-gray-400">{k}: </span>
                        <span className="text-gray-700 font-medium">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
