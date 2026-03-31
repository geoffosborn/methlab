/**
 * Maps real-world emission data to smoke particle parameters.
 *
 * Used by PlumeMesh to drive the react-smoke library:
 * - density: particle count
 * - size: spatial extent of the particle cloud
 * - windStrength: directional force on particles
 */

type ThreeAxisValue = [number, number, number];

/**
 * Map emission rate (kg/hr) to particle count.
 * Larger emissions = more particles = denser smoke.
 */
export function emissionToParticleDensity(emissionKgHr: number): number {
  const clamped = Math.max(emissionKgHr, 0.1);
  const normalized = Math.log10(clamped) / Math.log10(1500);
  const t = Math.min(Math.max(normalized, 0), 1);
  // Range: 15 particles (tiny leak) to 120 (massive)
  return Math.round(15 + t * 105);
}

/**
 * Map emission rate to smoke cloud size [width, height, depth].
 * Larger emissions produce taller, wider plumes.
 * Small leaks should be visually compact, large leaks should dominate the scene.
 */
export function emissionToSmokeSize(emissionKgHr: number): ThreeAxisValue {
  const clamped = Math.max(emissionKgHr, 1);
  const t = Math.log10(clamped) / Math.log10(1500);
  const width = 100 + t * 600;   // 100-700
  const height = 150 + t * 700;  // 150-850 (taller than wide)
  const depth = 100 + t * 600;   // 100-700
  return [width, height, depth];
}

/**
 * Map emission rate to smoke opacity.
 * Small leaks are wispy/faint, large leaks are dense and opaque.
 */
export function emissionToOpacity(emissionKgHr: number): number {
  const clamped = Math.max(emissionKgHr, 0.1);
  const normalized = Math.log10(clamped) / Math.log10(1500);
  const t = Math.min(Math.max(normalized, 0), 1);
  // Range: 0.15 (faint wisp) to 0.55 (dense cloud)
  return 0.15 + t * 0.4;
}

/**
 * Convert wind speed/direction to smoke windStrength vector.
 * Meteorological convention: direction is where wind comes FROM.
 * Plume moves in opposite direction.
 * Stronger wind = more visible drift.
 */
export function windToSmokeStrength(
  windSpeedMs: number,
  windDirectionDeg: number
): ThreeAxisValue {
  const fromRad = (windDirectionDeg * Math.PI) / 180;
  // Stronger scaling so wind direction changes are visually obvious
  const scale = windSpeedMs * 0.04;
  return [
    -Math.sin(fromRad) * scale,
    0.01, // slight upward drift
    -Math.cos(fromRad) * scale,
  ];
}

// --- Legacy functions kept for compatibility ---

/**
 * Map emission rate (kg/hr) to density scale (used by LeakScene shared state).
 */
export function emissionToDensityScale(emissionKgHr: number): number {
  const clamped = Math.max(emissionKgHr, 0.1);
  const normalized = Math.log10(clamped) / Math.log10(1500);
  const t = Math.min(Math.max(normalized, 0), 1);
  return 0.5 + t * 2.5;
}

/**
 * Estimate plume vertical extent based on emission rate.
 */
export function emissionToHeight(emissionKgHr: number): number {
  const clamped = Math.max(emissionKgHr, 1);
  return 200 + Math.log10(clamped) * 130;
}

/**
 * Convert wind speed (m/s) to texture velocity in UV space.
 */
export function windToTextureVelocity(
  windSpeedMs: number,
  windDirectionDeg: number,
  plumeExtentMeters: number
): [number, number] {
  const fromRad = (windDirectionDeg * Math.PI) / 180;
  const uvPerSecond = windSpeedMs / Math.max(plumeExtentMeters, 100);
  const aestheticScale = 0.05;
  return [
    -Math.sin(fromRad) * uvPerSecond * aestheticScale,
    -Math.cos(fromRad) * uvPerSecond * aestheticScale,
  ];
}

/**
 * Gas-type color mapping.
 */
export function gasToColor(gas: "CH4" | "CO2"): {
  r: number;
  g: number;
  b: number;
  hex: string;
} {
  if (gas === "CH4") {
    return { r: 1.0, g: 0.42, b: 0.21, hex: "#FF6B35" };
  }
  return { r: 0.29, g: 0.56, b: 0.85, hex: "#4A90D9" };
}

/**
 * Gaussian plume dispersion model parameters.
 * Pasquill-Gifford stability class D (neutral) as default.
 */
export function getDispersionCoefficients(downwindDistance: number): {
  sigmaY: number;
  sigmaZ: number;
} {
  const x = Math.max(downwindDistance, 1);
  return {
    sigmaY: 0.08 * x * Math.pow(1 + 0.0001 * x, -0.5),
    sigmaZ: 0.06 * x * Math.pow(1 + 0.0015 * x, -0.5),
  };
}
