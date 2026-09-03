import { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { useBuildingStore } from '@/store/buildingStore';

const PRESETS = {
  default: { position: [25, 20, 25] as [number, number, number] },
  top: { position: [0, 40, 0.01] as [number, number, number] },
  isometric: { position: [30, 25, 30] as [number, number, number] },
};

export default function CameraPresets() {
  const preset = useBuildingStore((s) => s.cameraPreset);
  const selectedFloor = useBuildingStore((s) => s.selectedFloor);
  const data = useBuildingStore((s) => s.data);
  const { camera, controls } = useThree();

  useEffect(() => {
    let targetPos = new THREE.Vector3(...PRESETS[preset].position);
    let targetLookAt = new THREE.Vector3(0, 6, 0);

    // If a specific floor is selected, move camera closer to that floor
    if (selectedFloor !== 'ALL' && data) {
      const level = data.levels.find(l => l.level_code === selectedFloor);
      if (level) {
        const yCenter = (level.z_min_m + level.z_max_m) / 2;
        targetPos = new THREE.Vector3(20, yCenter + 15, 20); // slightly offset
        targetLookAt = new THREE.Vector3(0, yCenter, 0);
      }
    }

    // Smooth lerp via animation frame
    let frame: number;
    const animate = () => {
      camera.position.lerp(targetPos, 0.08);
      if (controls && (controls as any).target) {
        (controls as any).target.lerp(targetLookAt, 0.08);
        (controls as any).update();
      } else {
        camera.lookAt(targetLookAt);
      }
      camera.updateProjectionMatrix();

      const distPos = camera.position.distanceTo(targetPos);
      let distLookAt = 0;
      if (controls && (controls as any).target) {
        distLookAt = (controls as any).target.distanceTo(targetLookAt);
      }
      
      if (distPos > 0.3 || distLookAt > 0.1) {
        frame = requestAnimationFrame(animate);
      } else {
        // Snap to final position
        camera.position.copy(targetPos);
        if (controls && (controls as any).target) {
          (controls as any).target.copy(targetLookAt);
          (controls as any).update();
        } else {
          camera.lookAt(targetLookAt);
        }
        camera.updateProjectionMatrix();
      }
    };
    animate();

    return () => cancelAnimationFrame(frame);
  }, [preset, selectedFloor, data, camera, controls]);

  return null;
}
