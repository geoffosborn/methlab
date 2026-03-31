import { getPlumesByBbox } from "./carbon-mapper";
import type { PlumeAnnotated } from "./types";

export interface PlumeKeyframe {
  timestamp: Date;
  emission: number;
  windSpeed: number;
  windDirection: number;
  bounds: [number, number, number, number];
  plumeId: string;
  source: PlumeAnnotated;
}

/**
 * Fetch plume observations near a location, sorted by time.
 * Returns keyframes suitable for time-series animation.
 */
export async function fetchPlumeTimeSeries(
  latitude: number,
  longitude: number,
  gas: "CH4" | "CO2",
  limit = 200
): Promise<PlumeKeyframe[]> {
  // Expand point to ~4km bbox
  const delta = 0.02;
  const bbox: [number, number, number, number] = [
    longitude - delta,
    latitude - delta,
    longitude + delta,
    latitude + delta,
  ];

  const plumes = await getPlumesByBbox(bbox, limit);

  return plumes
    .filter(
      (p) =>
        p.gas === gas &&
        p.emission_auto !== null &&
        p.wind_speed_avg_auto != null &&
        p.wind_direction_avg_auto != null
    )
    .map((p) => ({
      timestamp: new Date(p.scene_timestamp),
      emission: p.emission_auto!,
      windSpeed: p.wind_speed_avg_auto,
      windDirection: p.wind_direction_avg_auto,
      bounds: p.plume_bounds,
      plumeId: p.plume_id,
      source: p,
    }))
    .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
}
