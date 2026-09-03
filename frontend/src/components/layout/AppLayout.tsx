import TopBar from './TopBar';
import ActionBar from '@/components/actions/ActionBar';
import BuildingScene from '@/three/BuildingScene';
import FloorExplorer from '@/components/panels/FloorExplorer';
import UnitDetailPanel from '@/components/panels/UnitDetailPanel';
import { useBuildingStore } from '@/store/buildingStore';

export default function AppLayout() {
  return (
    <div className="flex flex-col h-screen w-screen bg-slate-100 overflow-hidden text-slate-800 font-sans">
      <TopBar />
      
      <main className="flex-1 flex overflow-hidden relative">
        <section 
          className="flex-1 relative bg-slate-50"
          onPointerDown={(e) => e.target instanceof HTMLCanvasElement && useBuildingStore.getState().selectUnit(null)}
        >
          <BuildingScene />
          <FloorExplorer />
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
