"use client";

import type { S2Detection } from "@/lib/api/sentinel2-types";
import {
  getConfidenceColor,
  formatEmissionRate,
} from "@/lib/api/sentinel2-types";

interface S2DetectionCardProps {
  detection: S2Detection;
}

export default function S2DetectionCard({ detection }: S2DetectionCardProps) {
  const confColor = getConfidenceColor(detection.confidence);
  const date = new Date(detection.scene_datetime);

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
      {/* Enhancement visualization placeholder */}
      {detection.viz_s3_key ? (
        <div className="aspect-video bg-zinc-950 flex items-center justify-center">
          <img
            src={`/api/sentinel2/image?key=${encodeURIComponent(detection.viz_s3_key)}`}
            alt={`S2 enhancement map ${detection.scene_datetime}`}
            className="w-full h-full object-contain"
          />
        </div>
      ) : (
        <div className="aspect-video bg-zinc-950 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-400">
              {formatEmissionRate(detection.emission_rate_kg_hr)}
            </div>
            <div className="text-xs text-zinc-500 mt-1">
              {date.toLocaleDateString("en-AU", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </div>
          </div>
        </div>
      )}

      <div className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">
            {formatEmissionRate(detection.emission_rate_kg_hr)}
          </span>
          <span
            className="px-2 py-0.5 rounded-full text-xs font-medium capitalize"
            style={{
              backgroundColor: `${confColor}20`,
              color: confColor,
            }}
          >
            {detection.confidence}
          </span>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-zinc-500">IME</span>
            <span className="ml-2 font-medium">
              {detection.ime_kg != null
                ? `${detection.ime_kg.toFixed(1)} kg`
                : "—"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500">Ueff</span>
            <span className="ml-2 font-medium">
              {detection.effective_wind_m_s != null
                ? `${detection.effective_wind_m_s.toFixed(1)} m/s`
                : "—"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500">Area</span>
            <span className="ml-2 font-medium">
              {detection.plume_pixels != null
                ? `${detection.plume_pixels} px`
                : "—"}
            </span>
          </div>
          <div>
            <span className="text-zinc-500">Length</span>
            <span className="ml-2 font-medium">
              {detection.plume_length_m != null
                ? `${(detection.plume_length_m / 1000).toFixed(1)} km`
                : "—"}
            </span>
          </div>
        </div>

        {/* Uncertainty */}
        {detection.uncertainty_kg_hr != null &&
          detection.emission_rate_kg_hr != null && (
            <div className="text-xs text-zinc-600">
              Uncertainty: ±{formatEmissionRate(detection.uncertainty_kg_hr)}
            </div>
          )}
      </div>
    </div>
  );
}
