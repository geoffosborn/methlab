"use client";

import { useEffect, useState } from "react";
import type { TropomiObservation } from "@/lib/api/tropomi-types";
import { getIntensityLevel } from "@/lib/api/tropomi-types";

interface TropomiTearSheetProps {
  observation: TropomiObservation;
}

function usePresignedUrl(s3Key: string | null): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!s3Key) return;
    fetch(`/api/storage?key=${encodeURIComponent(s3Key)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setUrl(data?.url ?? null))
      .catch(() => setUrl(null));
  }, [s3Key]);

  return url;
}

export default function TropomiTearSheet({
  observation,
}: TropomiTearSheetProps) {
  const intensity = observation.intensity_score
    ? getIntensityLevel(observation.intensity_score)
    : null;

  const imageUrl = usePresignedUrl(observation.viz_s3_key);

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
      {/* Tear sheet image */}
      {observation.viz_s3_key ? (
        <div className="aspect-[2/1] bg-zinc-950 flex items-center justify-center">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={`TROPOMI wind-rotated CH4 for ${observation.period_start}`}
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="animate-pulse bg-zinc-900 w-full h-full" />
          )}
        </div>
      ) : (
        <div className="aspect-[2/1] bg-zinc-950 flex items-center justify-center">
          <p className="text-zinc-600 text-sm">
            Visualization pending processing
          </p>
        </div>
      )}

      {/* Metrics summary */}
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">
            {formatPeriod(observation.period_start, observation.period_end)}
          </h3>
          {intensity && (
            <span
              className="px-2 py-0.5 rounded-full text-xs font-medium"
              style={{
                backgroundColor: `${intensity.color}20`,
                color: intensity.color,
              }}
            >
              {intensity.label}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <MetricItem
            label="Central Enhancement"
            value={
              observation.central_box_mean_ppb != null
                ? `${observation.central_box_mean_ppb.toFixed(1)} ppb`
                : "—"
            }
          />
          <MetricItem
            label="Peak Enhancement"
            value={
              observation.max_enhancement_ppb != null
                ? `${observation.max_enhancement_ppb.toFixed(1)} ppb`
                : "—"
            }
          />
          <MetricItem
            label="Overpasses"
            value={observation.sample_count?.toString() ?? "—"}
          />
          <MetricItem
            label="Intensity Score"
            value={
              observation.intensity_score != null
                ? `${observation.intensity_score.toFixed(0)}/100`
                : "—"
            }
          />
        </div>
      </div>
    </div>
  );
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  );
}

function formatPeriod(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  const month = s.toLocaleString("default", { month: "short" });
  const endMonth = e.toLocaleString("default", { month: "short" });

  if (s.getFullYear() === e.getFullYear()) {
    if (s.getMonth() === e.getMonth()) {
      return `${month} ${s.getFullYear()}`;
    }
    return `${month} — ${endMonth} ${s.getFullYear()}`;
  }
  return `${month} ${s.getFullYear()} — ${endMonth} ${e.getFullYear()}`;
}
