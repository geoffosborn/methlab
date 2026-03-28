import { NextRequest, NextResponse } from "next/server";
import type { NgerMethod2Report } from "@/lib/api/nger-types";

const API_BASE =
  process.env.METHLAB_API_BASE ?? "http://localhost:8020";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const { searchParams } = request.nextUrl;
  const reportingYear = searchParams.get("reporting_year") ?? "FY2024-25";

  // Try backend first
  try {
    const apiUrl = new URL(`${API_BASE}/nger/facilities/${id}/method2`);
    apiUrl.searchParams.set("reporting_year", reportingYear);

    const res = await fetch(apiUrl.toString(), {
      next: { revalidate: 300 },
    });
    if (!res.ok) throw new Error(`API ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fall back to mock data for development
    console.warn(
      `NGER Method 2 backend unavailable for facility ${id}, using mock data`
    );
    return NextResponse.json(buildMockReport(Number(id), reportingYear));
  }
}

function buildMockReport(
  facilityId: number,
  reportingYear: string
): NgerMethod2Report {
  return {
    facility_id: facilityId,
    facility_name: "Moranbah North Mine",
    nger_id: "QLD-UG-001",
    operator: "Anglo American Metallurgical Coal",
    reporting_year: reportingYear,
    state: "QLD",

    gas_zones: [
      {
        zone_id: "GZ-01",
        zone_name: "Goonyella Middle Seam",
        seam_name: "Goonyella Middle",
        depth_from_m: 180,
        depth_to_m: 195,
        thickness_m: 6.2,
        characterisation: "pre-drained",
        gas_composition_pct_ch4: 94.2,
        gas_composition_pct_co2: 3.1,
        gas_composition_pct_n2: 2.7,
        core_sample_count: 8,
      },
      {
        zone_id: "GZ-02",
        zone_name: "German Creek Seam",
        seam_name: "German Creek",
        depth_from_m: 220,
        depth_to_m: 232,
        thickness_m: 4.8,
        characterisation: "virgin",
        gas_composition_pct_ch4: 96.8,
        gas_composition_pct_co2: 1.9,
        gas_composition_pct_n2: 1.3,
        core_sample_count: 6,
      },
      {
        zone_id: "GZ-03",
        zone_name: "Bulli Seam (P-Tuff Rider)",
        seam_name: "Bulli",
        depth_from_m: 290,
        depth_to_m: 298,
        thickness_m: 3.1,
        characterisation: "virgin",
        gas_composition_pct_ch4: 97.5,
        gas_composition_pct_co2: 1.4,
        gas_composition_pct_n2: 1.1,
        core_sample_count: 4,
      },
    ],

    gas_content: [
      {
        zone_id: "GZ-01",
        zone_name: "Goonyella Middle Seam",
        insitu_gas_content_m3_per_tonne: 8.4,
        residual_gas_content_m3_per_tonne: 1.2,
        desorbable_gas_content_m3_per_tonne: 7.2,
        measurement_method: "AS 3980:2016 (Direct desorption)",
        sample_count: 12,
      },
      {
        zone_id: "GZ-02",
        zone_name: "German Creek Seam",
        insitu_gas_content_m3_per_tonne: 11.6,
        residual_gas_content_m3_per_tonne: 1.8,
        desorbable_gas_content_m3_per_tonne: 9.8,
        measurement_method: "AS 3980:2016 (Direct desorption)",
        sample_count: 8,
      },
      {
        zone_id: "GZ-03",
        zone_name: "Bulli Seam (P-Tuff Rider)",
        insitu_gas_content_m3_per_tonne: 14.2,
        residual_gas_content_m3_per_tonne: 2.4,
        desorbable_gas_content_m3_per_tonne: 11.8,
        measurement_method: "AS 3980:2016 (Direct desorption)",
        sample_count: 6,
      },
    ],

    emission_factors: [
      {
        zone_id: "GZ-01",
        zone_name: "Goonyella Middle Seam",
        emission_factor_m3_per_tonne: 5.8,
        emission_factor_co2e_per_tonne: 0.087,
        basis: "measured",
      },
      {
        zone_id: "GZ-02",
        zone_name: "German Creek Seam",
        emission_factor_m3_per_tonne: 9.8,
        emission_factor_co2e_per_tonne: 0.147,
        basis: "measured",
      },
      {
        zone_id: "GZ-03",
        zone_name: "Bulli Seam (P-Tuff Rider)",
        emission_factor_m3_per_tonne: 11.8,
        emission_factor_co2e_per_tonne: 0.177,
        basis: "modelled",
      },
    ],

    gas_release_geometry: [
      {
        zone_id: "GZ-01",
        zone_name: "Goonyella Middle Seam",
        area_ha: 142.5,
        thickness_m: 6.2,
        volume_m3: 8_835_000,
        coal_density_t_per_m3: 1.35,
        coal_tonnage_t: 11_927_250,
      },
      {
        zone_id: "GZ-02",
        zone_name: "German Creek Seam",
        area_ha: 142.5,
        thickness_m: 4.8,
        volume_m3: 6_840_000,
        coal_density_t_per_m3: 1.38,
        coal_tonnage_t: 9_439_200,
      },
      {
        zone_id: "GZ-03",
        zone_name: "Bulli Seam (P-Tuff Rider)",
        area_ha: 98.0,
        thickness_m: 3.1,
        volume_m3: 3_038_000,
        coal_density_t_per_m3: 1.42,
        coal_tonnage_t: 4_313_960,
      },
    ],

    production_drainage: {
      reporting_year: reportingYear,
      rom_coal_t: 7_200_000,
      saleable_coal_t: 5_400_000,
      pre_drainage_captured_m3: 48_500_000,
      pre_drainage_flared_m3: 12_300_000,
      pre_drainage_utilised_m3: 36_200_000,
      goaf_drainage_captured_m3: 8_700_000,
      total_fugitive_emissions_co2e: 1_482_000,
    },

    vam_measurements: [
      {
        ventilation_shaft: "No. 1 Upcast Shaft",
        measurement_period_start: "2024-07-01",
        measurement_period_end: "2024-12-31",
        avg_airflow_m3_per_s: 285,
        avg_ch4_concentration_pct: 0.38,
        total_ch4_emitted_m3: 17_120_000,
        total_ch4_emitted_co2e: 285_600,
        measurement_method: "Continuous (UNOR 614)",
      },
      {
        ventilation_shaft: "No. 2 Upcast Shaft",
        measurement_period_start: "2024-07-01",
        measurement_period_end: "2024-12-31",
        avg_airflow_m3_per_s: 195,
        avg_ch4_concentration_pct: 0.42,
        total_ch4_emitted_m3: 12_950_000,
        total_ch4_emitted_co2e: 215_800,
        measurement_method: "Continuous (UNOR 614)",
      },
      {
        ventilation_shaft: "No. 1 Upcast Shaft",
        measurement_period_start: "2025-01-01",
        measurement_period_end: "2025-06-30",
        avg_airflow_m3_per_s: 292,
        avg_ch4_concentration_pct: 0.41,
        total_ch4_emitted_m3: 18_920_000,
        total_ch4_emitted_co2e: 315_300,
        measurement_method: "Continuous (UNOR 614)",
      },
      {
        ventilation_shaft: "No. 2 Upcast Shaft",
        measurement_period_start: "2025-01-01",
        measurement_period_end: "2025-06-30",
        avg_airflow_m3_per_s: 198,
        avg_ch4_concentration_pct: 0.45,
        total_ch4_emitted_m3: 14_090_000,
        total_ch4_emitted_co2e: 234_800,
        measurement_method: "Continuous (UNOR 614)",
      },
    ],

    satellite_verification: {
      tropomi_annual_mean_enhancement_ppb: 12.4,
      tropomi_estimated_emission_rate_kg_hr: 2_850,
      tropomi_observation_count: 48,
      s2_detections_count: 7,
      s2_max_emission_rate_kg_hr: 4_120,
      s2_mean_emission_rate_kg_hr: 2_340,
      method2_total_co2e: 1_482_000,
      satellite_estimated_co2e: 2_042_000,
      discrepancy_pct: 37.8,
      verification_status: "under_reported",
    },

    generated_at: new Date().toISOString(),
  };
}
