export interface PlumeAnnotated {
  id: string;
  plume_id: string;
  plume_name?: string;
  gas: "CH4" | "CO2";
  geometry_json: {
    type: "Point";
    coordinates: [number, number]; // [longitude, latitude]
    bbox: number[] | null;
  };
  scene_id: string;
  scene_timestamp: string;
  instrument: string;
  mission_phase: string;
  platform: string;
  provider?: string;
  emission_auto: number | null;
  emission_uncertainty_auto: number | null;
  emission_cmf_type: string;
  ime?: number | null;
  gsd: number;
  sensitivity_mode: string;
  off_nadir: number;
  plume_png: string;
  plume_rgb_png: string;
  plume_tif: string;
  con_tif: string;
  rgb_png: string;
  rgb_tif?: string;
  plume_bounds: [number, number, number, number]; // [west, south, east, north]
  plume_quality: string | null;
  plume_latitude?: number;
  plume_longitude?: number;
  wind_speed_avg_auto: number;
  wind_speed_std_auto?: number;
  wind_direction_avg_auto: number;
  wind_direction_std_auto?: number;
  wind_source_auto?: string;
  emission_version?: string;
  processing_software?: string;
  publication_sources?: string[];
  is_offshore?: boolean;
  collection?: string;
  cmf_type?: string;
  sector: string | null;
  status?: string;
  hide_emission?: boolean;
  published_at: string;
  modified: string;
}

export interface PlumeListResponse {
  bbox_count?: number;
  total_count: number;
  limit: number;
  offset: number;
  items: PlumeAnnotated[];
  nearby_items?: PlumeAnnotated[];
}

export interface PlumeQueryParams {
  limit?: number;
  offset?: number;
  gas?: "CH4" | "CO2";
  sort?: string;
  order?: "asc" | "desc";
  plume_bounds?: string;
  min_emission?: number;
  max_emission?: number;
}

// IPCC sector labels
export const SECTOR_LABELS: Record<string, string> = {
  "1A1": "Electricity Generation",
  "1B1a": "Coal Mining",
  "1B2": "Oil & Gas",
  "4B": "Livestock",
  "6A": "Solid Waste",
  "6B": "Wastewater",
};

export function getSectorLabel(sector: string | null): string {
  if (!sector) return "Unknown";
  return SECTOR_LABELS[sector] ?? sector;
}

export function getPlumeCoordinates(plume: PlumeAnnotated): {
  longitude: number;
  latitude: number;
} {
  return {
    longitude: plume.geometry_json.coordinates[0],
    latitude: plume.geometry_json.coordinates[1],
  };
}
