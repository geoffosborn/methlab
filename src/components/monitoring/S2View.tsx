"use client";

import useSWR from "swr";
import type { S2DetectionListResponse } from "@/lib/api/sentinel2-types";
import S2DetectionCard from "./S2DetectionCard";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

interface S2ViewProps {
  facilityId: number;
}

export default function S2View({ facilityId }: S2ViewProps) {
  const { data, isLoading } = useSWR<S2DetectionListResponse>(
    `/api/sentinel2/facilities/${facilityId}`,
    fetcher,
    { revalidateOnFocus: false }
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-zinc-900/50 border border-zinc-800 rounded-lg h-40 animate-pulse"
          />
        ))}
      </div>
    );
  }

  const detections = data?.items ?? [];

  if (detections.length === 0) {
    return (
      <div className="bg-zinc-900/30 border border-zinc-800 border-dashed rounded-lg p-12 text-center">
        <h3 className="text-lg font-semibold text-zinc-400 mb-2">
          No Sentinel-2 Detections Yet
        </h3>
        <p className="text-zinc-600 text-sm max-w-md mx-auto">
          Plume detections using the Varon IME method will appear here once
          the S2 pipeline has processed scenes for this facility. Detections
          are triggered by TROPOMI screening flags or new S2 scenes.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatBox
          label="Total Detections"
          value={data?.total_count?.toString() ?? "0"}
        />
        <StatBox
          label="High Confidence"
          value={detections
            .filter((d) => d.confidence === "high")
            .length.toString()}
        />
        <StatBox
          label="Avg Emission"
          value={(() => {
            const rates = detections
              .map((d) => d.emission_rate_kg_hr)
              .filter((r): r is number => r != null);
            if (rates.length === 0) return "—";
            const avg = rates.reduce((a, b) => a + b, 0) / rates.length;
            return avg >= 1000
              ? `${(avg / 1000).toFixed(1)} t/hr`
              : `${avg.toFixed(0)} kg/hr`;
          })()}
        />
        <StatBox
          label="Peak Emission"
          value={(() => {
            const rates = detections
              .map((d) => d.emission_rate_kg_hr)
              .filter((r): r is number => r != null);
            if (rates.length === 0) return "—";
            const max = Math.max(...rates);
            return max >= 1000
              ? `${(max / 1000).toFixed(1)} t/hr`
              : `${max.toFixed(0)} kg/hr`;
          })()}
        />
      </div>

      {/* Detection cards */}
      <div>
        <h2 className="text-lg font-semibold mb-4">
          Individual Plume Detections
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {detections.map((det) => (
            <S2DetectionCard key={det.id} detection={det} />
          ))}
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-xl font-bold mt-1">{value}</div>
    </div>
  );
}
