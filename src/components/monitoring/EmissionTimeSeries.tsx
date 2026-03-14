"use client";

import type { TropomiObservation } from "@/lib/api/tropomi-types";
import { getIntensityLevel } from "@/lib/api/tropomi-types";

interface EmissionTimeSeriesProps {
  observations: TropomiObservation[];
}

/**
 * Simple SVG time series chart showing CH4 enhancement over time.
 * Replaces recharts dependency for Phase 2 — recharts added in Phase 3
 * when S2 data points are overlaid.
 */
export default function EmissionTimeSeries({
  observations,
}: EmissionTimeSeriesProps) {
  if (observations.length === 0) {
    return (
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 text-center">
        <p className="text-zinc-600 text-sm">
          No TROPOMI observations yet. Data will appear after the first
          pipeline run.
        </p>
      </div>
    );
  }

  // Sort by period start ascending
  const sorted = [...observations].sort(
    (a, b) => new Date(a.period_start).getTime() - new Date(b.period_start).getTime()
  );

  const values = sorted.map((o) => o.central_box_mean_ppb ?? 0);
  const maxVal = Math.max(...values, 5);
  const minVal = Math.min(...values, 0);
  const range = maxVal - minVal || 1;

  const width = 600;
  const height = 200;
  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  // Generate SVG path
  const points = sorted.map((o, i) => {
    const x = padding.left + (i / Math.max(sorted.length - 1, 1)) * chartW;
    const y =
      padding.top + chartH - ((values[i] - minVal) / range) * chartH;
    return { x, y, obs: o, val: values[i] };
  });

  const linePath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
    .join(" ");

  // Y-axis ticks
  const yTicks = Array.from({ length: 5 }, (_, i) => {
    const val = minVal + (range * i) / 4;
    const y = padding.top + chartH - (i / 4) * chartH;
    return { val, y };
  });

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
      <h3 className="text-sm font-semibold mb-3">
        CH4 Enhancement Over Time
      </h3>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Grid lines */}
        {yTicks.map((tick, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              y1={tick.y}
              x2={width - padding.right}
              y2={tick.y}
              stroke="#333"
              strokeDasharray="4,4"
            />
            <text
              x={padding.left - 8}
              y={tick.y}
              textAnchor="end"
              dominantBaseline="middle"
              fill="#666"
              fontSize="10"
            >
              {tick.val.toFixed(1)}
            </text>
          </g>
        ))}

        {/* Y-axis label */}
        <text
          x={12}
          y={height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#666"
          fontSize="10"
          transform={`rotate(-90, 12, ${height / 2})`}
        >
          ppb above background
        </text>

        {/* Line */}
        <path d={linePath} fill="none" stroke="#f59e0b" strokeWidth="2" />

        {/* Data points */}
        {points.map((p, i) => {
          const intensity = p.obs.intensity_score
            ? getIntensityLevel(p.obs.intensity_score)
            : { color: "#666" };
          return (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="4"
              fill={intensity.color}
              stroke="#1a1a2e"
              strokeWidth="2"
            />
          );
        })}

        {/* X-axis labels */}
        {points
          .filter(
            (_, i) =>
              i === 0 ||
              i === points.length - 1 ||
              i % Math.ceil(points.length / 6) === 0
          )
          .map((p, i) => (
            <text
              key={i}
              x={p.x}
              y={height - 8}
              textAnchor="middle"
              fill="#666"
              fontSize="9"
            >
              {formatShortDate(p.obs.period_start)}
            </text>
          ))}
      </svg>
    </div>
  );
}

function formatShortDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleString("default", { month: "short", year: "2-digit" });
}
