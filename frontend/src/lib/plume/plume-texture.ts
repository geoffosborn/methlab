import * as THREE from "three";
import { getDispersionCoefficients } from "./plume-physics";

interface PlumeTextureParams {
  /** Emission rate in kg/hr */
  emissionRate: number;
  /** Wind speed in m/s */
  windSpeed: number;
  /** Wind direction in degrees (meteorological: 0=N, clockwise) */
  windDirection: number;
  /** Plume bounds [west, south, east, north] in degrees */
  bounds: [number, number, number, number];
  /** Texture resolution (default 512) */
  resolution?: number;
}

/**
 * Generate a weather texture for the volumetric cloud renderer
 * that encodes a Gaussian plume dispersion shape.
 *
 * The R channel stores plume density (used by CloudLayer channel='r').
 * The source is placed near the upwind edge of the texture.
 * Density spreads downwind following the Gaussian plume model.
 */
export function generatePlumeTexture(
  params: PlumeTextureParams
): THREE.DataTexture {
  const {
    emissionRate,
    windSpeed,
    windDirection,
    bounds,
    resolution = 512,
  } = params;

  const [west, south, east, north] = bounds;
  const midLat = (south + north) / 2;

  // Approximate meters per degree at this latitude
  const mPerDegLon = 111320 * Math.cos((midLat * Math.PI) / 180);
  const mPerDegLat = 111320;

  const widthDeg = east - west;
  const heightDeg = north - south;
  const widthM = widthDeg * mPerDegLon;
  const heightM = heightDeg * mPerDegLat;

  // Extend the texture area beyond bounds to capture plume spread
  const extentM = Math.max(widthM, heightM, 500) * 2;

  // Source position: center of bounds (where the emission originates)
  const sourceLon = (west + east) / 2;
  const sourceLat = (south + north) / 2;

  // Wind direction: meteorological (comes FROM), plume goes opposite
  const fromRad = (windDirection * Math.PI) / 180;
  const plumeEastward = -Math.sin(fromRad); // unit vector, east component
  const plumenNorthward = -Math.cos(fromRad); // unit vector, north component

  // Perpendicular direction (crosswind)
  const crossEastward = plumenNorthward; // rotated 90 degrees
  const crossNorthward = -plumeEastward;

  const data = new Uint8Array(resolution * resolution * 4);

  // Emission strength scaling
  const Q = Math.max(emissionRate, 0.1); // kg/hr
  const u = Math.max(windSpeed, 0.5); // m/s

  // Peak concentration scaling factor for normalization
  const peakC = Q / (2 * Math.PI * u * 10 * 10); // sigma_y=sigma_z=10 at near-source
  const invPeakC = 1 / Math.max(peakC, 0.001);

  for (let py = 0; py < resolution; py++) {
    for (let px = 0; px < resolution; px++) {
      const i = (py * resolution + px) * 4;

      // Map pixel to physical position relative to source
      const u_frac = (px / resolution - 0.5) * extentM; // east offset in meters
      const v_frac = (py / resolution - 0.5) * extentM; // north offset in meters

      // Project onto downwind (x) and crosswind (y) axes
      const downwind = u_frac * plumeEastward + v_frac * plumenNorthward;
      const crosswind = u_frac * crossEastward + v_frac * crossNorthward;

      let density = 0;

      if (downwind > 0) {
        // Only has density downwind of source
        const { sigmaY, sigmaZ } = getDispersionCoefficients(downwind);

        // Gaussian plume model (ground-level concentration, z=0, H=0)
        const C =
          (Q / (Math.PI * u * sigmaY * sigmaZ)) *
          Math.exp(-(crosswind * crosswind) / (2 * sigmaY * sigmaY));

        // Normalize to 0-1 range
        density = C * invPeakC;
        density = Math.min(density, 1);

        // Apply a soft falloff at the source to avoid hard edge
        if (downwind < 50) {
          density *= downwind / 50;
        }
      } else if (downwind > -30) {
        // Small amount of density upwind of source (thermal plume rise)
        const dist = Math.sqrt(downwind * downwind + crosswind * crosswind);
        density = Math.max(0, 1 - dist / 30) * 0.3;
      }

      // Add some turbulent noise variation
      const noise =
        0.8 +
        0.2 *
          Math.sin(px * 0.1 + py * 0.15) *
          Math.cos(px * 0.07 - py * 0.13);
      density *= noise;

      // R channel = primary plume density
      const val = Math.round(Math.min(Math.max(density * 255, 0), 255));
      data[i] = val; // R
      data[i + 1] = 0; // G (unused)
      data[i + 2] = 0; // B (unused)
      data[i + 3] = 255; // A
    }
  }

  const texture = new THREE.DataTexture(
    data,
    resolution,
    resolution,
    THREE.RGBAFormat
  );
  texture.needsUpdate = true;
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearFilter;

  return texture;
}

/**
 * Calculate the physical extent in meters that the plume texture covers.
 * Used to set localWeatherRepeat on the Clouds component.
 */
export function getPlumeExtentMeters(
  bounds: [number, number, number, number]
): number {
  const [west, south, east, north] = bounds;
  const midLat = (south + north) / 2;
  const mPerDegLon = 111320 * Math.cos((midLat * Math.PI) / 180);
  const mPerDegLat = 111320;
  const widthM = (east - west) * mPerDegLon;
  const heightM = (north - south) * mPerDegLat;
  return Math.max(widthM, heightM, 500) * 2;
}
