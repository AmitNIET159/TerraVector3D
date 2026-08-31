import { useBuildingStore } from '@/store/buildingStore';
import VerticalIdDisplay from './VerticalIdDisplay';
import RightsCard from './RightsCard';
import ConfidenceIndicator from './ConfidenceIndicator';
import ConflictPanel from './ConflictPanel';
import StatusBadge from '@/components/common/StatusBadge';
import EmptyState from '@/components/common/EmptyState';

const UNIT_TYPE_LABELS: Record<string, string> = {
  apartment: 'Apartment', commercial: 'Commercial', parking: 'Parking',
  utility: 'Utility', common_area: 'Common Area', easement: 'Easement',
};

export default function UnitDetailPanel() {
  const selectedUnit = useBuildingStore((s) => s.selectedUnit);
  const rights = useBuildingStore((s) => s.selectedUnitRights);
  const data = useBuildingStore((s) => s.data);
  const activeConflict = useBuildingStore((s) => s.activeConflict);

  if (!selectedUnit) {
    return <EmptyState icon="🏗️" message="Select a spatial unit in the 3D view to see details" />;
  }

  const isConflict = activeConflict?.affected_unit_ids.includes(selectedUnit.unit_id);

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full bg-slate-50/30">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <h2 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          Spatial Unit Details
        </h2>
        <StatusBadge status={
          isConflict ? 'conflict'
            : selectedUnit.status === 'valid' ? 'valid'
              : selectedUnit.status === 'needs_review' ? 'warning'
                : 'pending'
        } />
      </div>

      {/* Vertical ID (Hero element of the panel) */}
      <VerticalIdDisplay verticalId={selectedUnit.vertical_id} />

      {/* Properties */}
      <div>
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Unit Properties</h3>
        <div className="grid grid-cols-2 gap-3">
          <InfoField label="Unit ID" value={selectedUnit.unit_id} />
          <InfoField label="Type" value={UNIT_TYPE_LABELS[selectedUnit.unit_type] || selectedUnit.unit_type} />
          <InfoField label="Floor" value={selectedUnit.level_code} />
          <InfoField label="Area" value={`${selectedUnit.area_sqm} m²`} />
          <InfoField label="Z Range" value={`${selectedUnit.z_min_m}m → ${selectedUnit.z_max_m}m`} />
          <InfoField label="Usage" value={selectedUnit.usage_type} />
          <InfoField label="Status" value={selectedUnit.status} />
          <InfoField label="Building" value={selectedUnit.building_id} />
        </div>
      </div>

      {/* Confidence */}
      {data && (
        <div>
          <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">AI Confidence Analysis</h3>
          <ConfidenceIndicator score={data.confidence} humanVerificationRequired />
        </div>
      )}

      {/* Rights */}
      <div>
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Registered Property Rights</h3>
        <RightsCard rights={rights} />
      </div>

      {/* Conflict */}
      {isConflict && activeConflict && (
        <div className="pt-2">
          <h3 className="text-[10px] font-bold text-red-500 uppercase tracking-widest mb-3 flex items-center gap-1.5">
             <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
             Active Spatial Conflict
          </h3>
          <ConflictPanel conflict={activeConflict} />
        </div>
      )}
    </div>
  );
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white rounded-lg px-3 py-2 border border-slate-200 shadow-sm">
      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">{label}</span>
      <span className="text-[13px] text-slate-800 font-semibold capitalize block truncate" title={value}>{value}</span>
    </div>
  );
}
