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
  const { camera } = useThree();

  useEffect(() => {
    const target = PRESETS[preset].position;
    const targetVec = new THREE.Vector3(target[0], target[1], target[2]);
    // Smooth lerp via animation frame
    let frame: number;
    const animate = () => {
      camera.position.lerp(targetVec, 0.08);
      camera.lookAt(0, 6, 0);
      camera.updateProjectionMatrix();
      if (camera.position.distanceTo(targetVec) > 0.3) {
        frame = requestAnimationFrame(animate);
      } else {
        // Snap to final position
        camera.position.copy(targetVec);
        camera.lookAt(0, 6, 0);
        camera.updateProjectionMatrix();
      }
    };
    animate();

    return () => cancelAnimationFrame(frame);
  }, [preset, camera]);

  return null;
}
