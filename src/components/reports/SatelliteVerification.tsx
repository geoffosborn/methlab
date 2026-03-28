"use client";

import type { SatelliteVerification as SatVerification } from "@/lib/api/nger-types";

const STATUS_CONFIG = {
  consistent: {
    label: "Consistent",
    color: "bg-green-500/20 text-green-400",
    printColor: "print-status-green",
  },
  under_reported: {
    label: "Potential Under-reporting",
    color: "bg-red-500/20 text-red-400",
    printColor: "print-status-red",
  },
  over_reported: {
    label: "Over-reported",
    color: "bg-amber-500/20 text-amber-400",
    printColor: "print-status-amber",
  },
  insufficient_data: {
    label: "Insufficient Data",
    color: "bg-zinc-500/20 text-zinc-400",
    printColor: "print-status-grey",
  },
} as const;

function fmt(n: number | null, unit: string, decimals = 0): string {
  if (n === null) return "N/A";
  return `${n.toLocaleString(undefined, { maximumFractionDigits: decimals })} ${unit}`;
}

function fmtPct(n: number | null): string {
  if (n === null) return "N/A";
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

export default function SatelliteVerification({
  data,
}: {
  data: SatVerification;
}) {
  const status = STATUS_CONFIG[data.verification_status];

  return (
    <div className="report-section">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold">
          Satellite Verification Cross-Check
        </h3>
        <span
          className={`px-2.5 py-1 rounded-full text-xs font-bold ${status.color} ${status.printColor}`}
        >
          {status.label}
        </span>
      </div>

      <p className="text-xs text-zinc-500 mb-4 print-muted">
        Independent satellite-derived emission estimates compared against Method
        2 totals. TROPOMI (Sentinel-5P) provides regional enhancement
        measurements; Sentinel-2 SWIR detects individual plume events.
      </p>

      {/* Comparison bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Method 2 estimate */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 print-card">
          <div className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">
            Method 2 Reported Total
          </div>
          <div className="text-2xl font-bold tabular-nums">
            {fmt(data.method2_total_co2e, "tCO\u2082e")}
          </div>
          <div className="text-xs text-zinc-600 mt-1">
            Based on gas zone characterisation &amp; production data
          </div>
        </div>

        {/* Satellite estimate */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 print-card">
          <div className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">
            Satellite-Derived Estimate
          </div>
          <div className="text-2xl font-bold tabular-nums">
            {data.satellite_estimated_co2e !== null
              ? fmt(data.satellite_estimated_co2e, "tCO\u2082e")
              : "Insufficient data"}
          </div>
          {data.discrepancy_pct !== null && (
            <div
              className={`text-xs mt-1 font-medium ${
                data.discrepancy_pct > 20
                  ? "text-red-400"
                  : data.discrepancy_pct > 0
                    ? "text-amber-400"
                    : "text-green-400"
              }`}
            >
              {fmtPct(data.discrepancy_pct)} vs Method 2
            </div>
          )}
        </div>
      </div>

      {/* Detail metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="TROPOMI Mean Enhancement"
          value={fmt(data.tropomi_annual_mean_enhancement_ppb, "ppb", 1)}
        />
        <MetricCard
          label="TROPOMI Est. Rate"
          value={fmt(data.tropomi_estimated_emission_rate_kg_hr, "kg/hr")}
        />
        <MetricCard
          label="TROPOMI Overpasses"
          value={String(data.tropomi_observation_count)}
        />
        <MetricCard
          label="S2 Plume Detections"
          value={String(data.s2_detections_count)}
        />
        <MetricCard
          label="S2 Max Rate"
          value={fmt(data.s2_max_emission_rate_kg_hr, "kg/hr")}
        />
        <MetricCard
          label="S2 Mean Rate"
          value={fmt(data.s2_mean_emission_rate_kg_hr, "kg/hr")}
        />
      </div>

      {data.verification_status === "under_reported" && (
        <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg print-alert-red">
          <p className="text-xs text-red-400">
            Satellite observations suggest actual fugitive emissions may exceed
            the Method 2 estimate by{" "}
            <span className="font-bold">{fmtPct(data.discrepancy_pct)}</span>.
            This discrepancy warrants review of gas zone characterisation inputs
            and may indicate unmeasured emission sources (e.g., surface seeps,
            open-cut highwall, or incomplete goaf gas accounting).
          </p>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-zinc-900/30 border border-zinc-800 rounded p-3 print-card">
      <div className="text-xs text-zinc-500 mb-0.5">{label}</div>
      <div className="text-sm font-semibold tabular-nums">{value}</div>
    </div>
  );
}
