/** Convert degrees to radians */
export function toRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/** Convert radians to degrees */
export function toDegrees(radians: number): number {
  return (radians * 180) / Math.PI;
}

/**
 * Convert meteorological wind direction (0=N, clockwise) to
 * a unit vector in local ENU (East-North-Up) frame.
 * Wind direction indicates where wind comes FROM,
 * so plume goes in the opposite direction.
 */
export function windDirectionToVector(
  directionDegrees: number
): [number, number] {
  // Meteorological: 0=N, 90=E (direction wind comes FROM)
  // Plume travels opposite to wind source
  const fromRad = toRadians(directionDegrees);
  // Plume goes in opposite direction: east component, north component
  return [-Math.sin(fromRad), -Math.cos(fromRad)];
}

/**
 * Calculate bounds extent in meters (approximate)
 */
export function boundsExtentMeters(
  bounds: [number, number, number, number]
): { widthM: number; heightM: number } {
  const [west, south, east, north] = bounds;
  const midLat = (south + north) / 2;
  const latScale = 111320; // meters per degree latitude
  const lonScale = 111320 * Math.cos(toRadians(midLat)); // meters per degree longitude

  return {
    widthM: (east - west) * lonScale,
    heightM: (north - south) * latScale,
  };
}
