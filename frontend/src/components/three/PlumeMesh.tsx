"use client";

import { useMemo } from "react";
import { Smoke } from "react-smoke";
import * as THREE from "three";
import type { PlumeAnnotated } from "@/lib/api/types";
import {
  emissionToParticleDensity,
  emissionToSmokeSize,
  emissionToOpacity,
  windToSmokeStrength,
  gasToColor,
} from "@/lib/plume/plume-physics";

interface PlumeMeshProps {
  plume: PlumeAnnotated;
}

export default function PlumeMesh({ plume }: PlumeMeshProps) {
  const emission = plume.emission_auto ?? 10;
  const windSpeed = plume.wind_speed_avg_auto ?? 2;
  const windDir = plume.wind_direction_avg_auto ?? 0;

  const color = useMemo(
    () => new THREE.Color(gasToColor(plume.gas).hex),
    [plume.gas]
  );

  const density = emissionToParticleDensity(emission);
  const size = emissionToSmokeSize(emission);
  const opacity = emissionToOpacity(emission);
  const windStrength = windToSmokeStrength(windSpeed, windDir);

  return (
    <group position={[0, 80, 0]}>
      <Smoke
        color={color}
        density={density}
        opacity={opacity}
        size={size}
        enableWind
        windStrength={windStrength}
        windDirection={windStrength}
        enableTurbulence
        turbulenceStrength={[0.2, 0.3, 0.2]}
        maxVelocity={[50, 25, 50]}
        enableRotation
        rotation={[0, 0, 0.05]}
      />
    </group>
  );
}
