export interface S2Detection {
  id: number;
  facility_id: number;
  scene_id: string;
  scene_datetime: string;
  emission_rate_kg_hr: number | null;
  emission_rate_t_hr: number | null;
  uncertainty_kg_hr: number | null;
  ime_kg: number | null;
  effective_wind_m_s: number | null;
  plume_length_m: number | null;
  plume_area_m2: number | null;
  plume_pixels: number | null;
  mean_enhancement: number | null;
  max_enhancement: number | null;
  wind_speed_10m: number | null;
  wind_direction: number | null;
  confidence: string | null;
  viz_s3_key: string | null;
}

export interface S2DetectionListResponse {
  total_count: number;
  items: S2Detection[];
}

export function getConfidenceColor(confidence: string | null): string {
  switch (confidence) {
    case "high":
      return "#22c55e";
    case "medium":
      return "#f59e0b";
    case "low":
      return "#ef4444";
    default:
      return "#666";
  }
}

export function formatEmissionRate(kgHr: number | null): string {
  if (kgHr == null) return "—";
  if (kgHr >= 1000) return `${(kgHr / 1000).toFixed(1)} t/hr`;
  return `${kgHr.toFixed(0)} kg/hr`;
}
