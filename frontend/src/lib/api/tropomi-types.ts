export interface TropomiObservation {
  id: number;
  facility_id: number;
  period_start: string;
  period_end: string;
  aggregation_period: string;
  mean_enhancement_ppb: number | null;
  max_enhancement_ppb: number | null;
  central_box_mean_ppb: number | null;
  sample_count: number | null;
  valid_pixel_fraction: number | null;
  mean_wind_speed: number | null;
  intensity_score: number | null;
  background_ch4_ppb: number | null;
  viz_s3_key: string | null;
  metrics_s3_key: string | null;
}

export interface TropomiListResponse {
  total_count: number;
  items: TropomiObservation[];
}

export interface TropomiRanking {
  facility_id: number;
  facility_name: string;
  state: string;
  operator: string;
  intensity_score: number;
  central_box_mean_ppb: number;
  mean_enhancement_ppb: number;
  sample_count: number;
  period_start: string;
  period_end: string;
}

export function getIntensityLevel(score: number): {
  label: string;
  color: string;
} {
  if (score >= 70) return { label: "High", color: "#ef4444" };
  if (score >= 40) return { label: "Moderate", color: "#f59e0b" };
  if (score >= 15) return { label: "Low", color: "#3b82f6" };
  return { label: "Minimal", color: "#22c55e" };
}
