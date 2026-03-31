"use client";

import { type ReactNode } from "react";
import { Sky } from "@react-three/drei";

interface AtmosphereSceneProps {
  children?: ReactNode;
  date?: string;
}

/**
 * Simple atmospheric sky wrapper using drei's Preetham sky model.
 */
export default function AtmosphereScene({
  children,
}: AtmosphereSceneProps) {
  return (
    <>
      <Sky
        distance={450000}
        sunPosition={[1, 0.4, 0.2]}
        inclination={0.49}
        azimuth={0.25}
        turbidity={4}
        rayleigh={1.5}
        mieCoefficient={0.005}
        mieDirectionalG={0.8}
      />
      {children}
    </>
  );
}
