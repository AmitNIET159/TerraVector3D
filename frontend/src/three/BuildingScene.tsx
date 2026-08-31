import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Grid } from '@react-three/drei';
import BuildingModel from './BuildingModel';
import ConflictOverlay from './ConflictOverlay';
import CameraPresets from './CameraPresets';
import { useBuildingStore } from '@/store/buildingStore';

export default function BuildingScene() {
  const data = useBuildingStore((s) => s.data);

  return (
    <Canvas
      camera={{ position: [25, 20, 25], fov: 45, near: 0.1, far: 200 }}
      shadows
      gl={{ antialias: true, alpha: false, preserveDrawingBuffer: true }}
      style={{ background: '#f8fafc' }}
      className="absolute inset-0"
    >
      <color attach="background" args={['#f8fafc']} />
      
      {/* Premium Lighting */}
      <ambientLight intensity={0.6} />
      <directionalLight 
        position={[30, 40, 20]} 
        intensity={1.5} 
        castShadow 
        shadow-mapSize={[4096, 4096]}
        shadow-camera-left={-30}
        shadow-camera-right={30}
        shadow-camera-top={30}
        shadow-camera-bottom={-30}
        shadow-bias={-0.0001}
      />
      <directionalLight position={[-20, 30, -20]} intensity={0.4} color="#e2e8f0" />
      <hemisphereLight intensity={0.4} color="#ffffff" groundColor="#f1f5f9" />

      {/* Environment & Fog */}
      <fog attach="fog" args={['#f8fafc', 50, 150]} />
      <Environment preset="city" />

      {/* Geospatial Grid & Ground */}
      <Grid
        position={[0, -3.02, 0]}
        args={[100, 100]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#e2e8f0"
        sectionSize={10}
        sectionThickness={1.2}
        sectionColor="#cbd5e1"
        fadeDistance={60}
        fadeStrength={1.5}
        infiniteGrid
      />

      <ContactShadows position={[0, -3.01, 0]} opacity={0.6} scale={60} blur={2.5} far={25} color="#0f172a" />

      {/* Building */}
      {data && <BuildingModel />}
      <ConflictOverlay />

      {/* Controls */}
      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.05}
        minDistance={5}
        maxDistance={100}
        maxPolarAngle={Math.PI / 2 - 0.05}
      />
      <CameraPresets />
    </Canvas>
  );
}
