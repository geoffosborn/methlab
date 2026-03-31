"use client";

import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import GlobeView from "@/components/three/GlobeView";
import type { PlumeAnnotated } from "@/lib/api/types";

interface HeroGlobeProps {
  plumes: PlumeAnnotated[];
}

export default function HeroGlobe({ plumes }: HeroGlobeProps) {
  return (
    <div className="h-full w-full">
      <Canvas
        camera={{
          position: [0, 80, 220],
          near: 1,
          far: 2000,
          fov: 45,
        }}
        frameloop="always"
      >
        <Suspense fallback={null}>
          <GlobeView plumes={plumes} autoRotate />
        </Suspense>
      </Canvas>
    </div>
  );
}
