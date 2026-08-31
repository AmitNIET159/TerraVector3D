import { useEffect } from 'react';
import { useBuildingStore } from '@/store/buildingStore';
import { loadBuildingData } from '@/api/dataService';
import AppLayout from '@/components/layout/AppLayout';
import LoadingState from '@/components/common/LoadingState';

export default function Dashboard() {
  const data = useBuildingStore((s) => s.data);
  const loadData = useBuildingStore((s) => s.loadData);

  useEffect(() => {
    loadBuildingData().then(loadData);
  }, [loadData]);

  if (!data) return <LoadingState message="Initializing BhuDrishti 3D Spatial Environment..." />;

  return <AppLayout />;
}
