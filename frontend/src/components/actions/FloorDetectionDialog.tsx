import type { GeospatialFloorsResponse } from '@/types';
import ConfidenceIndicator from '@/components/panels/ConfidenceIndicator';
import LoadingState from '@/components/common/LoadingState';

interface Props {
  data: GeospatialFloorsResponse | null;
  loading: boolean;
  onClose: () => void;
}

export default function FloorDetectionDialog({ data, loading, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-[500px] max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">AI Floor Detection</h2>
            <p className="text-[10px] text-gray-400 mt-0.5">Point cloud analysis → suggested floor levels</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">✕</button>
        </div>

        <div className="p-4">
          {loading && <LoadingState message="Analyzing point cloud data..." />}

          {!loading && data && (
            <div className="space-y-3">
              {/* Pipeline */}
              <div className="flex items-center gap-2 text-[10px] text-gray-500">
                <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded border border-blue-100">Point Cloud</span>
                <span>→</span>
                <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded border border-blue-100">AI Processing</span>
                <span>→</span>
                <span className="bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded border border-emerald-100">Suggested Floors</span>
              </div>

              {/* Confidence */}
              <ConfidenceIndicator
                score={data.method_agreement_score}
                humanVerificationRequired={data.human_verification_required}
              />

              {/* Detected elevations */}
              <div>
                <h3 className="text-[10px] font-semibold text-gray-400 uppercase mb-1">Detected Slab Elevations</h3>
                <div className="flex flex-wrap gap-1">
                  {data.detected_slab_elevations_m.map((z) => (
                    <span key={z} className="text-[10px] font-mono bg-gray-100 px-2 py-0.5 rounded">{z}m</span>
                  ))}
                </div>
                <p className="text-[10px] text-gray-400 mt-1">
                  Estimated floor height: <strong>{data.estimated_floor_height_m}m</strong>
                </p>
              </div>

              {/* Suggested levels */}
              <div>
                <h3 className="text-[10px] font-semibold text-gray-400 uppercase mb-1">Suggested Levels</h3>
                <div className="space-y-1">
                  {data.suggested_levels.map((level) => (
                    <div key={level.level_code} className="flex items-center justify-between bg-gray-50 rounded px-2.5 py-1.5 border border-gray-100 text-[11px]">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-800 w-8">{level.level_code}</span>
                        <span className="text-gray-500">{level.z_min_m}m → {level.z_max_m}m</span>
                        <span className="text-gray-400 capitalize">{level.level_type}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className={`font-semibold ${level.confidence_score >= 0.8 ? 'text-emerald-600' : 'text-amber-600'}`}>
                          {Math.round(level.confidence_score * 100)}%
                        </span>
                        {level.human_verification_required && <span className="text-amber-500 text-[9px]">⚠</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Warnings */}
              {data.warnings.length > 0 && (
                <div className="bg-amber-50 rounded-lg p-2.5 border border-amber-100">
                  <h3 className="text-[10px] font-semibold text-amber-600 uppercase mb-1">Warnings</h3>
                  {data.warnings.map((w, i) => (
                    <p key={i} className="text-[11px] text-amber-700">• {w}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
