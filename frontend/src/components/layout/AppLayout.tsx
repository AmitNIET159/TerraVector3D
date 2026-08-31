import TopBar from './TopBar';
import ActionBar from '@/components/actions/ActionBar';
import BuildingScene from '@/three/BuildingScene';
import FloorTreePanel from '@/components/panels/FloorTreePanel';
import UnitDetailPanel from '@/components/panels/UnitDetailPanel';
import { useBuildingStore } from '@/store/buildingStore';

export default function AppLayout() {
  return (
    <div className="flex flex-col h-screen w-screen bg-slate-100 overflow-hidden text-slate-800 font-sans">
      <TopBar />
      
      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Panel - Property Hierarchy */}
        <aside className="w-80 bg-white border-r border-slate-200 z-10 shadow-[4px_0_24px_rgba(0,0,0,0.02)] flex flex-col shrink-0">
          <FloorTreePanel />
        </aside>

        {/* Center - 3D Viewer */}
        <section 
          className="flex-1 relative bg-slate-50"
          onPointerDown={(e) => {
            if (e.target instanceof HTMLCanvasElement) {
              useBuildingStore.getState().selectUnit(null);
            }
          }}
        >
          <BuildingScene />
          
          {/* Action Bar Floating Bottom Center */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20">
            <ActionBar />
          </div>
        </section>

        {/* Right Panel - Context & Details */}
        <aside className="w-96 bg-white border-l border-slate-200 z-10 shadow-[-4px_0_24px_rgba(0,0,0,0.02)] flex flex-col shrink-0">
          <UnitDetailPanel />
        </aside>
      </main>
    </div>
  );
}
