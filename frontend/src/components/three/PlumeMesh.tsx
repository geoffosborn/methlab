"use client";

import { useMemo } from "react";
import { Clouds, CloudLayer } from "@takram/three-clouds/r3f";
import { Vector2 } from "three";
import type { PlumeAnnotated } from "@/lib/api/types";
import { generatePlumeTexture, getPlumeExtentMeters } from "@/lib/plume/plume-texture";
import {
  emissionToDensityScale,
  emissionToCoverage,
  emissionToHeight,
  windToTextureVelocity,
} from "@/lib/plume/plume-physics";

interface PlumeMeshProps {
  plume: PlumeAnnotated;
}

/**
 * Volumetric plume renderer using three-geospatial's cloud ray-marching
 * with a custom weather texture generated from Gaussian plume dispersion.
 */
export default function PlumeMesh({ plume }: PlumeMeshProps) {
  const emission = plume.emission_auto ?? 10;
  const windSpeed = plume.wind_speed_avg_auto ?? 2;
  const windDir = plume.wind_direction_avg_auto ?? 0;

  const weatherTexture = useMemo(
    () =>
      generatePlumeTexture({
        emissionRate: emission,
        windSpeed,
        windDirection: windDir,
        bounds: plume.plume_bounds,
        resolution: 512,
      }),
    [emission, windSpeed, windDir, plume.plume_bounds]
  );

  const extentM = useMemo(
    () => getPlumeExtentMeters(plume.plume_bounds),
    [plume.plume_bounds]
  );

  const velocity = useMemo(() => {
    const [vx, vy] = windToTextureVelocity(windSpeed, windDir, extentM);
    return new Vector2(vx, vy);
  }, [windSpeed, windDir, extentM]);

  const densityScale = emissionToDensityScale(emission);
  const coverage = emissionToCoverage(emission);
  const height = emissionToHeight(emission);

  return (
    <Clouds
      coverage={coverage}
      localWeatherTexture={weatherTexture}
      localWeatherVelocity={velocity}
      scatteringCoefficient={0.04}
      absorptionCoefficient={0.008}
      disableDefaultLayers
      qualityPreset="medium"
      haze={false}
      lightShafts={false}
      shadow-cascadeCount={2}
      shadow-maxFar={5000}
    >
      <CloudLayer
        channel="r"
        altitude={0}
        height={height}
        densityScale={densityScale}
        shapeAmount={0.25}
        shapeDetailAmount={0.08}
        weatherExponent={0.5}
        shapeAlteringBias={0.6}
        coverageFilterWidth={0.7}
        shadow
        densityProfile-expTerm={0.4}
        densityProfile-exponent={-0.003}
        densityProfile-constantTerm={0.35}
        densityProfile-linearTerm={0.25}
      />
    </Clouds>
  );
}
