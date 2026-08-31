import { useState } from 'react';
import { useBuildingStore } from '@/store/buildingStore';
import { runTopologyValidation, runFloorDetection, runReportGeneration } from '@/api/dataService';
import FloorDetectionDialog from './FloorDetectionDialog';
import ReportDialog from './ReportDialog';

export default function ActionBar() {
  const data = useBuildingStore((s) => s.data);
  const isValidating = useBuildingStore((s) => s.isValidating);
  const setIsValidating = useBuildingStore((s) => s.setIsValidating);
  const setValidationResult = useBuildingStore((s) => s.setValidationResult);
  const showConflict = useBuildingStore((s) => s.showConflict);
  const validationResult = useBuildingStore((s) => s.validationResult);
  const activeConflict = useBuildingStore((s) => s.activeConflict);

  const isDetectingFloors = useBuildingStore((s) => s.isDetectingFloors);
  const setIsDetectingFloors = useBuildingStore((s) => s.setIsDetectingFloors);
  const setFloorDetection = useBuildingStore((s) => s.setFloorDetection);
  const floorDetection = useBuildingStore((s) => s.floorDetection);

  const isGeneratingReport = useBuildingStore((s) => s.isGeneratingReport);
  const setIsGeneratingReport = useBuildingStore((s) => s.setIsGeneratingReport);
  const setReportResult = useBuildingStore((s) => s.setReportResult);
  const reportResult = useBuildingStore((s) => s.reportResult);

  const [showFloorDialog, setShowFloorDialog] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const result = await runTopologyValidation();
      setValidationResult(result);
      if (result.conflicts.length > 0) {
        showConflict(result.conflicts[0]);
      }
    } catch (err) {
      console.error('Validation failed:', err);
    } finally {
      setIsValidating(false);
    }
  };

  const handleFloorDetection = async () => {
    setIsDetectingFloors(true);
    setShowFloorDialog(true);
    try {
      const result = await runFloorDetection();
      setFloorDetection(result);
    } catch (err) {
      console.error('Floor detection failed:', err);
    } finally {
      setIsDetectingFloors(false);
    }
  };

  const handleReport = async () => {
    setIsGeneratingReport(true);
    setShowReportDialog(true);
    try {
      const result = await runReportGeneration();
      setReportResult(result);
    } catch (err) {
      console.error('Report generation failed:', err);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  if (!data) return null;

  return (
    <>
      <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.08)] border border-slate-200 p-2 flex gap-3 items-center pointer-events-auto transition-all">
        {/* Validation */}
        <button
          onClick={handleValidate}
          disabled={isValidating}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs transition-colors border border-slate-200 disabled:opacity-50"
        >
          {isValidating ? (
            <span className="w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          )}
          Run Topology Validation
        </button>

        {/* Show/Clear Conflict */}
        {validationResult && validationResult.total_conflicts > 0 && (
          <button
            onClick={() => {
              if (activeConflict) {
                showConflict(null);
              } else {
                showConflict(validationResult.conflicts[0]);
              }
            }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold border transition-all ${
              activeConflict
                ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
                : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
            }`}
          >
            {activeConflict ? '✕ Clear Conflict' : '⚠ View Detected Conflict'}
          </button>
        )}

        {/* Validation result badge */}
        {validationResult && (
          <div className="flex items-center gap-2 px-4 py-2.5 border-l border-slate-200">
            <span className={`text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-widest ${
              validationResult.is_valid
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-red-50 text-red-700'
            }`}>
              {validationResult.total_units} units · {validationResult.total_conflicts} conflicts
            </span>
          </div>
        )}

        <div className="w-4" /> {/* Spacer */}

        {/* AI Floor Detection */}
        <button
          onClick={handleFloorDetection}
          disabled={isDetectingFloors}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs transition-colors border border-slate-200 disabled:opacity-50"
        >
          {isDetectingFloors ? (
            <span className="w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
          )}
          AI Floor Detection
        </button>

        {/* Generate Report */}
        <button
          onClick={handleReport}
          disabled={isGeneratingReport}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-[0_4px_12px_rgba(5,150,105,0.2)] transition-all border border-emerald-500 disabled:opacity-50"
        >
          {isGeneratingReport ? (
            <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          )}
          Generate Evidence Report
        </button>
      </div>

      {/* Dialogs */}
      {showFloorDialog && (
        <FloorDetectionDialog
          data={floorDetection}
          loading={isDetectingFloors}
          onClose={() => setShowFloorDialog(false)}
        />
      )}
      {showReportDialog && (
        <ReportDialog
          data={reportResult}
          loading={isGeneratingReport}
          onClose={() => setShowReportDialog(false)}
        />
      )}
    </>
  );
}
