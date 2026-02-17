"use client";

import { type ReactNode, useRef, useMemo } from "react";
import { Atmosphere, Sky, AerialPerspective } from "@takram/three-atmosphere/r3f";
import { Clouds, CloudLayer } from "@takram/three-clouds/r3f";
import {
  Dithering,
  LensFlare,
  EffectComposer,
} from "@takram/three-geospatial-effects/r3f";
import { ToneMapping, SMAA } from "@react-three/postprocessing";
import { ToneMappingMode } from "postprocessing";

interface AtmosphereSceneProps {
  children?: ReactNode;
  /** ISO 8601 date string for sun position */
  date?: string;
  /** Show default clouds (false for plume-only scenes) */
  showDefaultClouds?: boolean;
  /** Custom clouds component to replace defaults */
  cloudsElement?: ReactNode;
}

/**
 * Wraps the scene with atmospheric rendering:
 * sky, aerial perspective, and the post-processing chain.
 */
export default function AtmosphereScene({
  children,
  date,
  showDefaultClouds = false,
  cloudsElement,
}: AtmosphereSceneProps) {
  const atmosphereDate = useMemo(() => {
    if (date) return new Date(date);
    return new Date();
  }, [date]);

  return (
    <Atmosphere date={atmosphereDate} correctAltitude>
      <Sky />
      {children}
      <EffectComposer>
        {cloudsElement ?? (
          showDefaultClouds ? <Clouds coverage={0.4} /> : null
        )}
        <AerialPerspective sky ground />
        <LensFlare />
        <ToneMapping mode={ToneMappingMode.AGX} />
        <SMAA />
        <Dithering />
      </EffectComposer>
    </Atmosphere>
  );
}
