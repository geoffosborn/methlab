"use client";

import useSWR from "swr";
import Link from "next/link";

const fetcher = (url: string) =>
  fetch(url).then((r) => (r.ok ? r.json() : null));

export default function MonitoringPreview() {
  const { data: rankings } = useSWR<Array<Record<string, unknown>>>(
    "/api/tropomi/rankings?limit=5",
    fetcher,
    { revalidateOnFocus: false }
  );

  const { data: detections } = useSWR<Array<Record<string, unknown>>>(
    "/api/sentinel2/detections?limit=3",
    fetcher,
    { revalidateOnFocus: false }
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* TROPOMI Rankings */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <h3 className="text-sm font-bold">TROPOMI Intensity Rankings</h3>
          <Link
            href="/dashboard"
            className="text-xs text-zinc-500 hover:text-zinc-300"
          >
            Dashboard &rarr;
          </Link>
        </div>
        {rankings && rankings.length > 0 ? (
          <div className="divide-y divide-zinc-800/50">
            {rankings.map((r, i) => (
              <Link
                key={String(r.facility_id ?? i)}
                href={`/facilities/${r.facility_id}/tropomi`}
                className="flex items-center px-4 py-3 hover:bg-zinc-800/50 transition-colors"
              >
                <span className="text-zinc-600 text-sm w-6">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {String(r.facility_name ?? "")}
                  </div>
                  <div className="text-xs text-zinc-600">
                    {String(r.state ?? "")} — {String(r.operator ?? "")}
                  </div>
                </div>
                <div className="text-right ml-3">
                  <div className="text-sm font-bold text-orange-400">
                    {typeof r.intensity_score === "number"
                      ? r.intensity_score.toFixed(0)
                      : "—"}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <div className="text-zinc-600 text-sm mb-2">
              TROPOMI satellite rankings
            </div>
            <div className="text-xs text-zinc-700">
              Methane column density analysis coming soon.
              Weekly satellite revisits rank facilities by emission intensity.
            </div>
          </div>
        )}
      </div>

      {/* Sentinel-2 Detections */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <h3 className="text-sm font-bold">Sentinel-2 Detections</h3>
          <Link
            href="/dashboard"
            className="text-xs text-zinc-500 hover:text-zinc-300"
          >
            Dashboard &rarr;
          </Link>
        </div>
        {detections && detections.length > 0 ? (
          <div className="divide-y divide-zinc-800/50">
            {detections.map((d, i) => (
              <Link
                key={i}
                href={`/facilities/${d.facility_id}`}
                className="flex items-center px-4 py-3 hover:bg-zinc-800/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    {String(d.facility_name ?? "")}
                  </div>
                  <div className="text-xs text-zinc-600">
                    {d.scene_datetime
                      ? new Date(String(d.scene_datetime)).toLocaleDateString("en-AU")
                      : ""}
                  </div>
                </div>
                <div className="text-right ml-3">
                  <div className="text-sm font-bold">
                    {typeof d.emission_rate_kg_hr === "number"
                      ? d.emission_rate_kg_hr >= 1000
                        ? `${(d.emission_rate_kg_hr / 1000).toFixed(1)} t/hr`
                        : `${d.emission_rate_kg_hr.toFixed(0)} kg/hr`
                      : "—"}
                  </div>
                  <div className="text-xs text-zinc-600 capitalize">
                    {String(d.confidence ?? "")}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <div className="text-zinc-600 text-sm mb-2">
              High-resolution plume detections
            </div>
            <div className="text-xs text-zinc-700">
              Sentinel-2 multispectral analysis coming soon.
              10m resolution plume detection and quantification.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
