import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useBuildingStore } from '@/store/buildingStore';
import { CENTER_X, CENTER_Y } from './BuildingModel';

export default function ConflictOverlay() {
  const activeConflict = useBuildingStore((s) => s.activeConflict);
  const data = useBuildingStore((s) => s.data);
  const meshRef = useRef<THREE.Mesh>(null);

  // Calculate overlap region from the two conflicting unit footprints
  const overlapGeometry = useMemo(() => {
    if (!activeConflict || !data) return null;

    const units = activeConflict.affected_unit_ids
      .map((id) => data.spatialUnits.find((su) => su.unit_id === id))
      .filter(Boolean);
    if (units.length < 2) return null;

    const u1 = units[0]!;
    const u2 = units[1]!;

    // Simple AABB overlap for visualization
    const minX1 = Math.min(...u1.footprint.map((p) => p[0]));
    const maxX1 = Math.max(...u1.footprint.map((p) => p[0]));
    const minY1 = Math.min(...u1.footprint.map((p) => p[1]));
    const maxY1 = Math.max(...u1.footprint.map((p) => p[1]));

    const minX2 = Math.min(...u2.footprint.map((p) => p[0]));
    const maxX2 = Math.max(...u2.footprint.map((p) => p[0]));
    const minY2 = Math.min(...u2.footprint.map((p) => p[1]));
    const maxY2 = Math.max(...u2.footprint.map((p) => p[1]));

    const overlapMinX = Math.max(minX1, minX2);
    const overlapMaxX = Math.min(maxX1, maxX2);
    const overlapMinY = Math.max(minY1, minY2);
    const overlapMaxY = Math.min(maxY1, maxY2);

    if (overlapMinX >= overlapMaxX || overlapMinY >= overlapMaxY) return null;

    const width = overlapMaxX - overlapMinX;
    const depth = overlapMaxY - overlapMinY;
    const height = activeConflict.overlapping_z_max_m - activeConflict.overlapping_z_min_m;
    const cx = (overlapMinX + overlapMaxX) / 2 - CENTER_X;
    const cy = (overlapMinY + overlapMaxY) / 2 - CENTER_Y;
    const cz = (activeConflict.overlapping_z_min_m + activeConflict.overlapping_z_max_m) / 2;

    return { width, depth, height, cx, cy, cz };
  }, [activeConflict, data]);

  useFrame((state) => {
    if (meshRef.current) {
      const pulse = Math.sin(state.clock.elapsedTime * 4) * 0.2 + 0.5;
      (meshRef.current.material as THREE.MeshStandardMaterial).opacity = pulse;
    }
  });

  if (!overlapGeometry) return null;
  const { width, depth, height, cx, cy, cz } = overlapGeometry;

  return (
    <group>
      {/* Solid overlap volume */}
      <mesh ref={meshRef} position={[cx, cz, cy]}>
        <boxGeometry args={[width, height, depth]} />
        <meshStandardMaterial 
          color="#ef4444" 
          transparent 
          opacity={0.6} 
          depthWrite={false} 
          emissive="#ef4444"
          emissiveIntensity={0.2}
          side={THREE.DoubleSide}
        />
      </mesh>
      {/* Heavy Wireframe Outline */}
      <mesh position={[cx, cz, cy]}>
        <boxGeometry args={[width + 0.05, height + 0.05, depth + 0.05]} />
        <meshBasicMaterial color="#b91c1c" wireframe transparent opacity={0.8} />
      </mesh>
    </group>
  );
}
