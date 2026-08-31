import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useBuildingStore } from '@/store/buildingStore';
import SpatialUnitMesh from './SpatialUnitMesh';
import type { Level } from '@/types';

// Building centroid for centering
const CENTER_X = 10;
const CENTER_Y = 7.5;

const EXPLODE_GAP = 2.0; // metres gap per floor in exploded view

function FloorSlab({ level }: { level: Level }) {
  const y = level.z_min_m;
  return (
    <mesh position={[0, y, 0]} receiveShadow>
      <boxGeometry args={[16, 0.12, 11]} />
      <meshStandardMaterial color="#e5e7eb" transparent opacity={0.6} />
    </mesh>
  );
}

function BuildingShell({ yOffset }: { yOffset: number }) {
  const data = useBuildingStore((s) => s.data);
  if (!data?.building.footprint) return null;

  const geometry = useMemo(() => {
    const fp = data.building.footprint!;
    const shape = new THREE.Shape();
    shape.moveTo(fp[0][0] - CENTER_X, fp[0][1] - CENTER_Y);
    for (let i = 1; i < fp.length; i++) {
      shape.lineTo(fp[i][0] - CENTER_X, fp[i][1] - CENTER_Y);
    }
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, {
      depth: data.building.total_height_m + 3, // +3 for basement
      bevelEnabled: false,
    });
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, [data]);

  return (
    <mesh geometry={geometry} position={[0, -3 + yOffset, 0]}>
      <meshStandardMaterial
        color="#10b981"
        transparent
        opacity={0.04}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}

function ParcelBoundary() {
  const data = useBuildingStore((s) => s.data);
  if (!data?.parcel.boundary) return null;

  const points = useMemo(() => {
    return data.parcel.boundary!.map(
      (p) => new THREE.Vector3(p[0] - CENTER_X, -3, p[1] - CENTER_Y)
    );
  }, [data]);

  return (
    <line>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={points.length}
          array={new Float32Array(points.flatMap((p) => [p.x, p.y, p.z]))}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial color="#059669" linewidth={2} transparent opacity={0.5} />
    </line>
  );
}

export default function BuildingModel() {
  const data = useBuildingStore((s) => s.data);
  const selectedFloor = useBuildingStore((s) => s.selectedFloor);
  const isExploded = useBuildingStore((s) => s.isExploded);
  const groupRef = useRef<THREE.Group>(null);

  // Gentle floating animation
  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.15;
    }
  });

  if (!data) return null;

  const sortedLevels = [...data.levels].sort((a, b) => a.level_number - b.level_number);

  return (
    <group ref={groupRef}>
      <ParcelBoundary />
      {!isExploded && <BuildingShell yOffset={0} />}

      {sortedLevels.map((level, idx) => {
        const explodeOffset = isExploded ? idx * EXPLODE_GAP : 0;
        const isFiltered = selectedFloor !== 'ALL' && selectedFloor !== level.level_code;
        const levelUnits = data.spatialUnits.filter((su) => su.level_code === level.level_code);

        return (
          <group key={level.level_id} position={[0, explodeOffset, 0]}>
            <FloorSlab level={level} />
            {levelUnits.map((unit) => (
              <SpatialUnitMesh
                key={unit.unit_id}
                unit={unit}
                centerX={CENTER_X}
                centerY={CENTER_Y}
                yOffset={explodeOffset}
                dimmed={isFiltered}
              />
            ))}
          </group>
        );
      })}
    </group>
  );
}

export { CENTER_X, CENTER_Y };
