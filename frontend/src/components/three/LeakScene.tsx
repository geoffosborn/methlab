"use client";

import { useRef, useEffect } from "react";
import { useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { PlumeAnnotated } from "@/lib/api/types";
import { getPlumeCoordinates } from "@/lib/api/types";
import type { InterpolatedFrame } from "@/hooks/usePlumePlayback";
import AtmosphereScene from "./AtmosphereScene";
import PlumeMesh from "./PlumeMesh";
import MapTiles, { type TileSource } from "./MapTiles";

export type CameraPreset = "orbit" | "ground" | "overview" | "flyaround";

const CAMERA_PRESETS: Record<CameraPreset, { position: [number, number, number]; target: [number, number, number] }> = {
  orbit: { position: [2000, 800, 2000], target: [0, 300, 0] },
  ground: { position: [600, 30, 600], target: [0, 200, 0] },
  overview: { position: [200, 3500, 200], target: [0, 0, 0] },
  flyaround: { position: [2000, 800, 2000], target: [0, 300, 0] },
};

interface LeakSceneProps {
  plume: PlumeAnnotated;
  cameraPreset?: CameraPreset;
  tileSource?: TileSource;
  animationFrame?: InterpolatedFrame;
}

function CameraController({ preset }: { preset: CameraPreset }) {
  const { camera } = useThree();
  const controlsRef = useRef<any>(null);

  useEffect(() => {
    const cfg = CAMERA_PRESETS[preset];
    camera.position.set(...cfg.position);
    if (controlsRef.current) {
      controlsRef.current.target.set(...cfg.target);
      controlsRef.current.update();
    }
  }, [preset, camera]);

  return (
    <OrbitControls
      ref={controlsRef}
      minDistance={50}
      maxDistance={20000}
      enableDamping
      dampingFactor={0.05}
      target={CAMERA_PRESETS[preset].target}
      autoRotate={preset === "flyaround"}
      autoRotateSpeed={0.8}
    />
  );
}

export default function LeakScene({ plume, cameraPreset = "orbit", tileSource = "satellite", animationFrame }: LeakSceneProps) {
  const { latitude, longitude } = getPlumeCoordinates(plume);

  // Build a plume object with animation frame overrides applied
  const effectivePlume: PlumeAnnotated = animationFrame
    ? {
        ...plume,
        emission_auto: animationFrame.emission,
        wind_speed_avg_auto: animationFrame.windSpeed,
        wind_direction_avg_auto: animationFrame.windDirection,
        plume_bounds: animationFrame.bounds,
      }
    : plume;

  return (
    <>
      <CameraController preset={cameraPreset} />
      <ambientLight intensity={0.6} />
      <directionalLight position={[100, 200, 50]} intensity={1.0} />

      <AtmosphereScene date={plume.scene_timestamp}>
        {/* Satellite/map tile ground */}
        <MapTiles
          latitude={latitude}
          longitude={longitude}
          worldSize={4000}
          zoom={14}
          gridRadius={2}
          source={tileSource}
        />

        {/* Fallback ground beyond tiles */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]}>
          <planeGeometry args={[20000, 20000]} />
          <meshStandardMaterial color="#1a2a1a" roughness={0.9} metalness={0} />
        </mesh>

        {/* Ground shadow under plume */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.3, 0]}>
          <circleGeometry args={[150, 32]} />
          <meshBasicMaterial color="#000000" transparent opacity={0.15} depthWrite={false} />
        </mesh>

        {/* Emission source marker */}
        <mesh position={[0, 10, 0]}>
          <cylinderGeometry args={[4, 6, 20, 8]} />
          <meshStandardMaterial color="#cc3300" roughness={0.6} />
        </mesh>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.2, 0]}>
          <ringGeometry args={[8, 12, 16]} />
          <meshStandardMaterial
            color="#ff4400"
            emissive="#ff4400"
            emissiveIntensity={0.5}
          />
        </mesh>

        {/* Smoke plume */}
        <PlumeMesh plume={effectivePlume} />
      </AtmosphereScene>
    </>
  );
}
