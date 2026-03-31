"use client";

import { useRef } from "react";
import { OrbitControls } from "@react-three/drei";
import { EastNorthUpFrame } from "@takram/three-geospatial/r3f";
import { radians } from "@takram/three-geospatial";
import type { PlumeAnnotated } from "@/lib/api/types";
import { getPlumeCoordinates } from "@/lib/api/types";
import AtmosphereScene from "./AtmosphereScene";
import PlumeMesh from "./PlumeMesh";

interface LeakSceneProps {
  plume: PlumeAnnotated;
}

/**
 * Full leak visualization scene combining terrain, plume, and atmosphere.
 * This is the flagship 3D view for individual leak pages.
 */
export default function LeakScene({ plume }: LeakSceneProps) {
  const { longitude, latitude } = getPlumeCoordinates(plume);

  const plumeElement = <PlumeMesh plume={plume} />;

  return (
    <>
      <OrbitControls
        minDistance={200}
        maxDistance={50000}
        enableDamping
        dampingFactor={0.05}
        target={[0, 0, 100]}
      />
      <ambientLight intensity={0.3} />

      <AtmosphereScene
        date={plume.scene_timestamp}
        cloudsElement={plumeElement}
      >
        <EastNorthUpFrame
          longitude={radians(longitude)}
          latitude={radians(latitude)}
        >
          {/* Ground plane as placeholder for terrain */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
            <planeGeometry args={[10000, 10000]} />
            <meshStandardMaterial
              color="#2d4a2e"
              roughness={0.9}
              metalness={0}
            />
          </mesh>

          {/* Emission source marker */}
          <mesh position={[0, 0, 5]}>
            <cylinderGeometry args={[3, 3, 10, 8]} />
            <meshStandardMaterial color="#666" roughness={0.7} />
          </mesh>
        </EastNorthUpFrame>
      </AtmosphereScene>
    </>
  );
}
