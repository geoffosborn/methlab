/** NGER Method 2 report data types per CER guidelines */

export interface GasZone {
  zone_id: string;
  zone_name: string;
  seam_name: string;
  depth_from_m: number;
  depth_to_m: number;
  thickness_m: number;
  characterisation: "virgin" | "pre-drained" | "goaf" | "other";
  gas_composition_pct_ch4: number;
  gas_composition_pct_co2: number;
  gas_composition_pct_n2: number;
  core_sample_count: number;
}

export interface GasContent {
  zone_id: string;
  zone_name: string;
  insitu_gas_content_m3_per_tonne: number;
  residual_gas_content_m3_per_tonne: number;
  desorbable_gas_content_m3_per_tonne: number;
  measurement_method: string;
  sample_count: number;
}

export interface EmissionFactor {
  zone_id: string;
  zone_name: string;
  emission_factor_m3_per_tonne: number;
  emission_factor_co2e_per_tonne: number;
  basis: "measured" | "default" | "modelled";
}

export interface GasReleaseGeometry {
  zone_id: string;
  zone_name: string;
  area_ha: number;
  thickness_m: number;
  volume_m3: number;
  coal_density_t_per_m3: number;
  coal_tonnage_t: number;
}

export interface ProductionDrainageSummary {
  reporting_year: string;
  rom_coal_t: number;
  saleable_coal_t: number;
  pre_drainage_captured_m3: number;
  pre_drainage_flared_m3: number;
  pre_drainage_utilised_m3: number;
  goaf_drainage_captured_m3: number;
  total_fugitive_emissions_co2e: number;
}

export interface VamMeasurement {
  ventilation_shaft: string;
  measurement_period_start: string;
  measurement_period_end: string;
  avg_airflow_m3_per_s: number;
  avg_ch4_concentration_pct: number;
  total_ch4_emitted_m3: number;
  total_ch4_emitted_co2e: number;
  measurement_method: string;
}

export interface SatelliteVerification {
  tropomi_annual_mean_enhancement_ppb: number | null;
  tropomi_estimated_emission_rate_kg_hr: number | null;
  tropomi_observation_count: number;
  s2_detections_count: number;
  s2_max_emission_rate_kg_hr: number | null;
  s2_mean_emission_rate_kg_hr: number | null;
  method2_total_co2e: number;
  satellite_estimated_co2e: number | null;
  discrepancy_pct: number | null;
  verification_status:
    | "consistent"
    | "under_reported"
    | "over_reported"
    | "insufficient_data";
}

export interface NgerMethod2Report {
  facility_id: number;
  facility_name: string;
  nger_id: string;
  operator: string;
  reporting_year: string;
  state: string;
  gas_zones: GasZone[];
  gas_content: GasContent[];
  emission_factors: EmissionFactor[];
  gas_release_geometry: GasReleaseGeometry[];
  production_drainage: ProductionDrainageSummary;
  vam_measurements: VamMeasurement[];
  satellite_verification: SatelliteVerification;
  generated_at: string;
}
