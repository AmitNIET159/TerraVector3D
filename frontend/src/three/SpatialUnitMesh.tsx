import { useMemo, useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Html, Edges } from '@react-three/drei';
import { useBuildingStore } from '@/store/buildingStore';
import type { SpatialUnit } from '@/types';

// Sophisticated command-center colors (restrained accents)
const UNIT_COLORS: Record<string, string> = {
  apartment: '#cbd5e1',     // Light slate
  commercial: '#fcd34d',    // Subdued amber
  parking: '#94a3b8',       // Slate
  utility: '#c4b5fd',       // Subtle purple/indigo hint
  common_area: '#99f6e4',   // Mint/Teal
  easement: '#bfdbfe',      // Light blue
};

const CONFLICT_COLOR = '#ef4444'; // Red for conflict
const SELECTED_COLOR = '#10b981'; // Green for selected

interface Props {
  unit: SpatialUnit;
  centerX: number;
  centerY: number;
  yOffset: number;
  dimmed: boolean;
}

export default function SpatialUnitMesh({ unit, centerX, centerY, yOffset, dimmed }: Props) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const selectedUnitId = useBuildingStore((s) => s.selectedUnitId);
  const activeConflict = useBuildingStore((s) => s.activeConflict);
  const selectUnit = useBuildingStore((s) => s.selectUnit);

  const isSelected = selectedUnitId === unit.unit_id;
  const isConflict = activeConflict?.affected_unit_ids.includes(unit.unit_id) ?? false;

  const geometry = useMemo(() => {
    const shape = new THREE.Shape();
    const fp = unit.footprint;
    if (!fp || fp.length < 3) return new THREE.BoxGeometry(1, 1, 1);

    shape.moveTo(fp[0][0] - centerX, fp[0][1] - centerY);
    for (let i = 1; i < fp.length; i++) {
      shape.lineTo(fp[i][0] - centerX, fp[i][1] - centerY);
    }
    shape.closePath();

    const height = unit.z_max_m - unit.z_min_m;
    const geo = new THREE.ExtrudeGeometry(shape, {
      depth: height - 0.08, // slight gap for floor slab
      bevelEnabled: false,
    });
    geo.rotateX(-Math.PI / 2);
    return geo;
  }, [unit, centerX, centerY]);

  // Pulse effect for conflicts
  useFrame((state) => {
    if (meshRef.current && isConflict) {
      const pulse = Math.sin(state.clock.elapsedTime * 4) * 0.2 + 0.8;
      (meshRef.current.material as THREE.MeshStandardMaterial).opacity = pulse * 0.85;
      (meshRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity = Math.sin(state.clock.elapsedTime * 4) * 0.3 + 0.2;
    }
  });

  const baseColor = isConflict ? CONFLICT_COLOR : isSelected ? SELECTED_COLOR : (UNIT_COLORS[unit.unit_type] || '#cbd5e1');
  const opacity = dimmed ? 0.05 : isSelected ? 0.9 : hovered ? 0.85 : 0.65;
  const roughness = isSelected || isConflict ? 0.2 : 0.6;
  const metalness = isSelected || isConflict ? 0.4 : 0.1;
  const emissive = isConflict ? CONFLICT_COLOR : isSelected ? SELECTED_COLOR : '#000000';
  const emissiveIntensity = isSelected ? 0.3 : 0;

  // Label position
  const fpCenter = useMemo(() => {
    const fp = unit.footprint;
    if (!fp || fp.length < 3) return [0, 0];
    const cx = fp.reduce((s, p) => s + p[0], 0) / fp.length - centerX;
    const cy = fp.reduce((s, p) => s + p[1], 0) / fp.length - centerY;
    return [cx, cy];
  }, [unit, centerX, centerY]);

  return (
    <group>
      <mesh
        ref={meshRef}
        geometry={geometry}
        position={[0, unit.z_min_m + 0.04, 0]}
        onClick={(e) => { e.stopPropagation(); selectUnit(unit.unit_id); }}
        onPointerOver={(e) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'pointer'; }}
        onPointerOut={() => { setHovered(false); document.body.style.cursor = 'auto'; }}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial
          color={baseColor}
          transparent
          opacity={opacity}
          roughness={roughness}
          metalness={metalness}
          emissive={emissive}
          emissiveIntensity={emissiveIntensity}
          side={THREE.DoubleSide}
          polygonOffset
          polygonOffsetFactor={1}
        />
        {/* Adds crisp CAD lines to the unit boundaries */}
        {!dimmed && (
           <Edges 
             linewidth={isSelected || isConflict ? 2 : 1} 
             color={isConflict ? '#7f1d1d' : isSelected ? '#064e3b' : '#64748b'} 
             transparent
             opacity={hovered || isSelected || isConflict ? 0.9 : 0.3}
           />
        )}
      </mesh>

      {/* Floating label */}
      {(isSelected || hovered) && !dimmed && (
        <Html
          position={[fpCenter[0], unit.z_max_m + 0.2, fpCenter[1]]}
          center
          distanceFactor={15}
          style={{ pointerEvents: 'none', zIndex: isSelected ? 10 : 1 }}
        >
          <div className={`px-2.5 py-1.5 rounded-md shadow-xl backdrop-blur-md border font-sans text-xs font-semibold whitespace-nowrap transition-all ${
            isConflict 
              ? 'bg-red-900/90 border-red-500/50 text-red-50' 
              : isSelected 
                ? 'bg-emerald-900/90 border-emerald-500/50 text-emerald-50' 
                : 'bg-white/95 border-gray-200/50 text-gray-700'
          }`}>
            <span>{unit.unit_id}</span>
            <span className={`mx-1.5 ${isSelected || isConflict ? 'text-white/40' : 'text-gray-300'}`}>|</span>
            <span className={`capitalize ${isConflict ? 'text-red-300' : isSelected ? 'text-emerald-300' : 'text-emerald-600'}`}>{unit.unit_type}</span>
            {isConflict && <span className="ml-1.5 text-red-400">⚠ CONFLICT</span>}
          </div>
        </Html>
      )}
    </group>
  );
}
