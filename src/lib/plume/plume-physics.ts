/**
 * Maps real-world emission data to volumetric cloud renderer parameters.
 *
 * The three-geospatial CloudLayer uses:
 * - densityScale: overall opacity multiplier (clouds default ~0.2)
 * - coverage: 0-1, controls what fraction of weather texture produces density
 * - scatteringCoefficient / absorptionCoefficient: light interaction
 *
 * Methane plumes are much less dense than clouds, so we use much lower values.
 */

/**
 * Map emission rate (kg/hr) to CloudLayer densityScale.
 * emission_auto in the dataset ranges from ~1 to ~1400 kg/hr.
 * We use a log scale since the range spans orders of magnitude.
 */
export function emissionToDensityScale(emissionKgHr: number): number {
  const clamped = Math.max(emissionKgHr, 0.1);
  const normalized = Math.log10(clamped) / Math.log10(1500);
  const t = Math.min(Math.max(normalized, 0), 1);
  // Range: 0.005 (barely visible) to 0.08 (clearly visible)
  return 0.005 + t * 0.075;
}

/**
 * Map emission rate to cloud coverage parameter.
 * Higher emissions = more of the weather texture area fills with density.
 */
export function emissionToCoverage(emissionKgHr: number): number {
  const clamped = Math.max(emissionKgHr, 0.1);
  const normalized = Math.log10(clamped) / Math.log10(1500);
  const t = Math.min(Math.max(normalized, 0), 1);
  return 0.15 + t * 0.5; // Range: 0.15 to 0.65
}

/**
 * Estimate plume vertical extent based on emission rate.
 * Larger emissions create taller plumes.
 */
export function emissionToHeight(emissionKgHr: number): number {
  const clamped = Math.max(emissionKgHr, 1);
  // Small leaks ~50m tall, large leaks ~500m tall
  return 50 + Math.log10(clamped) * 150;
}

/**
 * Convert wind speed (m/s) to weather texture velocity in UV space.
 * This controls how fast the plume visually advects.
 */
export function windToTextureVelocity(
  windSpeedMs: number,
  windDirectionDeg: number,
  plumeExtentMeters: number
): [number, number] {
  // Meteorological convention: direction wind comes FROM
  // Plume moves in opposite direction
  const fromRad = (windDirectionDeg * Math.PI) / 180;
  // Scale factor: UV units per second
  // UV 1.0 = full texture width = plumeExtentMeters
  const uvPerSecond = windSpeedMs / Math.max(plumeExtentMeters, 100);
  // Slow it down for visual aesthetics (real-time would be too fast)
  const aestheticScale = 0.05;
  return [
    -Math.sin(fromRad) * uvPerSecond * aestheticScale,
    -Math.cos(fromRad) * uvPerSecond * aestheticScale,
  ];
}

/**
 * Gas-type color mapping for post-processing tint.
 */
export function gasToColor(gas: "CH4" | "CO2"): {
  r: number;
  g: number;
  b: number;
  hex: string;
} {
  if (gas === "CH4") {
    return { r: 1.0, g: 0.42, b: 0.21, hex: "#FF6B35" }; // Orange-red
  }
  return { r: 0.29, g: 0.56, b: 0.85, hex: "#4A90D9" }; // Blue
}

/**
 * Gaussian plume dispersion model parameters.
 * Pasquill-Gifford stability class D (neutral) as default.
 */
export function getDispersionCoefficients(downwindDistance: number): {
  sigmaY: number;
  sigmaZ: number;
} {
  // Stability class D (neutral conditions)
  // sigma_y = 0.08 * x * (1 + 0.0001 * x)^(-0.5)
  // sigma_z = 0.06 * x * (1 + 0.0015 * x)^(-0.5)
  const x = Math.max(downwindDistance, 1);
  return {
    sigmaY: 0.08 * x * Math.pow(1 + 0.0001 * x, -0.5),
    sigmaZ: 0.06 * x * Math.pow(1 + 0.0015 * x, -0.5),
  };
}
