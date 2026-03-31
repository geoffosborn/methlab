"use client";

import { Canvas, type CanvasProps } from "@react-three/fiber";
import { Suspense, type ReactNode } from "react";

interface SceneCanvasProps {
  children: ReactNode;
  className?: string;
  camera?: CanvasProps["camera"];
  gl?: CanvasProps["gl"];
}

/**
 * Scene canvas for atmosphere/clouds pipeline (depth: false).
 * For simple 3D scenes (globe), use Canvas directly with default depth.
 */
export default function SceneCanvas({
  children,
  className,
  camera,
  gl,
}: SceneCanvasProps) {
  return (
    <div className={className ?? "h-full w-full"}>
      <Canvas
        gl={gl ?? {
          depth: true,
          logarithmicDepthBuffer: false,
          antialias: true,
        }}
        camera={camera ?? {
          position: [2000, 800, 2000],
          near: 1,
          far: 4e5,
          fov: 50,
        }}
        frameloop="always"
      >
        <Suspense fallback={null}>{children}</Suspense>
      </Canvas>
    </div>
  );
}
