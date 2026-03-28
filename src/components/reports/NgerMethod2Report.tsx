"use client";

import useSWR from "swr";
import type {
  NgerMethod2Report as Report,
  GasZone,
  GasContent,
  EmissionFactor,
  GasReleaseGeometry,
  VamMeasurement,
} from "@/lib/api/nger-types";
import ReportTable, { type Column } from "./ReportTable";
import SatelliteVerification from "./SatelliteVerification";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

interface NgerMethod2ReportProps {
  facilityId: number;
  facilityName: string;
  ngerIdDisplay?: string;
}

/* ── Column definitions ── */

const gasZoneCols: Column<GasZone>[] = [
  { key: "zone_id", label: "Zone", align: "left" },
  { key: "seam_name", label: "Seam", align: "left" },
  {
    key: "depth_from_m",
    label: "Depth From (m)",
    align: "right",
    format: (v) => Number(v).toFixed(0),
  },
  {
    key: "depth_to_m",
    label: "Depth To (m)",
    align: "right",
    format: (v) => Number(v).toFixed(0),
  },
  {
    key: "thickness_m",
    label: "Thickness (m)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  { key: "characterisation", label: "Type", align: "left" },
  {
    key: "gas_composition_pct_ch4",
    label: "CH\u2084 (%)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  {
    key: "gas_composition_pct_co2",
    label: "CO\u2082 (%)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  {
    key: "core_sample_count",
    label: "Cores",
    align: "right",
    format: (v) => String(v),
  },
];

const gasContentCols: Column<GasContent>[] = [
  { key: "zone_name", label: "Gas Zone", align: "left" },
  {
    key: "insitu_gas_content_m3_per_tonne",
    label: "In-situ (m\u00B3/t)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  {
    key: "residual_gas_content_m3_per_tonne",
    label: "Residual (m\u00B3/t)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  {
    key: "desorbable_gas_content_m3_per_tonne",
    label: "Desorbable (m\u00B3/t)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  { key: "measurement_method", label: "Method", align: "left" },
  {
    key: "sample_count",
    label: "Samples",
    align: "right",
    format: (v) => String(v),
  },
];

const emissionFactorCols: Column<EmissionFactor>[] = [
  { key: "zone_name", label: "Gas Zone", align: "left" },
  {
    key: "emission_factor_m3_per_tonne",
    label: "EF (m\u00B3/t)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  {
    key: "emission_factor_co2e_per_tonne",
    label: "EF (tCO\u2082e/t coal)",
    align: "right",
    format: (v) => Number(v).toFixed(3),
  },
  { key: "basis", label: "Basis", align: "left" },
];

const geometryCols: Column<GasReleaseGeometry>[] = [
  { key: "zone_name", label: "Gas Zone", align: "left" },
  {
    key: "area_ha",
    label: "Area (ha)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  {
    key: "thickness_m",
    label: "Thickness (m)",
    align: "right",
    format: (v) => Number(v).toFixed(1),
  },
  {
    key: "volume_m3",
    label: "Volume (m\u00B3)",
    align: "right",
    format: (v) => Number(v).toLocaleString(),
  },
  {
    key: "coal_density_t_per_m3",
    label: "Density (t/m\u00B3)",
    align: "right",
    format: (v) => Number(v).toFixed(2),
  },
  {
    key: "coal_tonnage_t",
    label: "Coal Tonnage (t)",
    align: "right",
    format: (v) => Number(v).toLocaleString(),
  },
];

const vamCols: Column<VamMeasurement>[] = [
  { key: "ventilation_shaft", label: "Shaft", align: "left" },
  { key: "measurement_period_start", label: "From", align: "left" },
  { key: "measurement_period_end", label: "To", align: "left" },
  {
    key: "avg_airflow_m3_per_s",
    label: "Airflow (m\u00B3/s)",
    align: "right",
    format: (v) => Number(v).toLocaleString(),
  },
  {
    key: "avg_ch4_concentration_pct",
    label: "CH\u2084 (%)",
    align: "right",
    format: (v) => Number(v).toFixed(2),
  },
  {
    key: "total_ch4_emitted_m3",
    label: "CH\u2084 Emitted (m\u00B3)",
    align: "right",
    format: (v) => Number(v).toLocaleString(),
  },
  {
    key: "total_ch4_emitted_co2e",
    label: "tCO\u2082e",
    align: "right",
    format: (v) => Number(v).toLocaleString(),
  },
  { key: "measurement_method", label: "Method", align: "left" },
];

/* ── Component ── */

export default function NgerMethod2Report({
  facilityId,
  facilityName,
  ngerIdDisplay,
}: NgerMethod2ReportProps) {
  const { data, isLoading, error } = useSWR<Report>(
    `/api/nger/facilities/${facilityId}/method2`,
    fetcher,
    { revalidateOnFocus: false }
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-zinc-900/50 border border-zinc-800 rounded-lg h-32 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-zinc-900/30 border border-zinc-800 border-dashed rounded-lg p-12 text-center">
        <h3 className="text-lg font-semibold text-zinc-400 mb-2">
          Report Unavailable
        </h3>
        <p className="text-zinc-600 text-sm max-w-md mx-auto">
          Unable to generate the NGER Method 2 report for this facility. The
          backend may not have sufficient gas zone and reservoir data.
        </p>
      </div>
    );
  }

  const pd = data.production_drainage;

  return (
    <div className="nger-report space-y-8">
      {/* Print button */}
      <div className="flex items-center justify-between print:hidden">
        <div>
          <p className="text-xs text-zinc-500">
            Reporting year: {data.reporting_year} &middot; Generated:{" "}
            {new Date(data.generated_at).toLocaleDateString("en-AU", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </p>
        </div>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
        >
          Export as PDF
        </button>
      </div>

      {/* Print-only header */}
      <div className="hidden print:block print-header">
        <h1 className="text-xl font-bold">
          NGER Method 2 — Fugitive Emissions Report
        </h1>
        <p className="text-sm mt-1">
          {data.facility_name}
          {ngerIdDisplay && ` (${ngerIdDisplay})`} &middot; {data.operator}
        </p>
        <p className="text-sm">
          Reporting year: {data.reporting_year} &middot; State: {data.state}
        </p>
        <p className="text-xs mt-2 text-gray-500">
          Generated by MethLab &middot;{" "}
          {new Date(data.generated_at).toLocaleDateString("en-AU", {
            day: "numeric",
            month: "long",
            year: "numeric",
          })}
        </p>
        <hr className="mt-3 border-gray-300" />
      </div>

      {/* 1. Gas Zone Characterisation */}
      <ReportTable
        title="1. Gas Zone Characterisation"
        description="Seam-by-seam characterisation of gas zones within the gas release zone, per NGER Method 2 requirements (minimum 2-3 core drillings per zone)."
        columns={gasZoneCols}
        rows={data.gas_zones}
        footnote="Gas composition determined by gas chromatography. Core samples collected per AS 3980:2016."
      />

      {/* 2. In-Situ Gas Content */}
      <ReportTable
        title="2. In-Situ Gas Content per Zone"
        description="Measured gas content by direct desorption method. In-situ = residual + desorbable."
        columns={gasContentCols}
        rows={data.gas_content}
      />

      {/* 3. Emission Factors */}
      <ReportTable
        title="3. Emission Factors per Zone"
        description="Mine-specific emission factors derived from gas content measurements and post-drainage residual content."
        columns={emissionFactorCols}
        rows={data.emission_factors}
        footnote="EF (m³/t) = desorbable gas content. EF (tCO₂e/t) = EF × gas density × GWP-100 (CH₄ = 28)."
      />

      {/* 4. Gas Release Zone Geometry */}
      <ReportTable
        title="4. Gas Release Zone Geometry"
        description="Geometry of the column of strata disturbed during mining operations. Area based on longwall panel extraction plus goaf influence zone."
        columns={geometryCols}
        rows={data.gas_release_geometry}
      />

      {/* 5. Production & Drainage Summary */}
      <div className="report-section">
        <h3 className="text-base font-semibold mb-1">
          5. Production &amp; Drainage Summary
        </h3>
        <p className="text-xs text-zinc-500 mb-3 print-muted">
          Annual coal production and gas drainage volumes for{" "}
          {pd.reporting_year}.
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <SummaryCard
            label="ROM Coal"
            value={pd.rom_coal_t.toLocaleString()}
            unit="tonnes"
          />
          <SummaryCard
            label="Saleable Coal"
            value={pd.saleable_coal_t.toLocaleString()}
            unit="tonnes"
          />
          <SummaryCard
            label="Pre-drainage Captured"
            value={pd.pre_drainage_captured_m3.toLocaleString()}
            unit="m³"
          />
          <SummaryCard
            label="Pre-drainage Flared"
            value={pd.pre_drainage_flared_m3.toLocaleString()}
            unit="m³"
          />
          <SummaryCard
            label="Pre-drainage Utilised"
            value={pd.pre_drainage_utilised_m3.toLocaleString()}
            unit="m³"
          />
          <SummaryCard
            label="Goaf Drainage"
            value={pd.goaf_drainage_captured_m3.toLocaleString()}
            unit="m³"
          />
          <SummaryCard
            label="Total Fugitive Emissions"
            value={pd.total_fugitive_emissions_co2e.toLocaleString()}
            unit="tCO₂e"
            highlight
          />
        </div>
      </div>

      {/* 6. VAM Measurements */}
      <ReportTable
        title="6. Ventilation Air Methane (VAM) Measurements"
        description="Continuous monitoring of methane concentration in ventilation exhaust air."
        columns={vamCols}
        rows={data.vam_measurements}
        footnote="Measurements per NGER Technical Guidelines Division 3.3. UNOR 614 = non-dispersive infrared analyser."
      />

      {/* 7. Satellite Verification */}
      <SatelliteVerification data={data.satellite_verification} />

      {/* Print footer */}
      <div className="hidden print:block text-xs text-gray-400 mt-8 pt-4 border-t border-gray-300">
        <p>
          This report was generated by MethLab using NGER Method 2 methodology
          per the National Greenhouse and Energy Reporting (Measurement)
          Determination 2008, Division 3.3.
        </p>
        <p className="mt-1">
          Satellite verification data sourced from ESA Sentinel-5P (TROPOMI) and
          Sentinel-2 (SWIR). Emission rate estimates are independent of the
          Method 2 calculation and are provided for cross-validation purposes
          only.
        </p>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  unit,
  highlight,
}: {
  label: string;
  value: string;
  unit: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-lg p-3 border print-card ${
        highlight
          ? "bg-orange-500/10 border-orange-500/30"
          : "bg-zinc-900/50 border-zinc-800"
      }`}
    >
      <div className="text-xs text-zinc-500 mb-0.5">{label}</div>
      <div
        className={`text-sm font-semibold tabular-nums ${highlight ? "text-orange-400" : ""}`}
      >
        {value}
      </div>
      <div className="text-xs text-zinc-600">{unit}</div>
    </div>
  );
}
