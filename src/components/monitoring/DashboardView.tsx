"use client";

import useSWR from "swr";
import Link from "next/link";
import type { AlertListResponse } from "@/lib/api/alert-types";
import { SEVERITY_CONFIG, ALERT_TYPE_LABELS } from "@/lib/api/alert-types";
import type { TropomiRanking } from "@/lib/api/tropomi-types";
import { getIntensityLevel } from "@/lib/api/tropomi-types";

const fetcher = (url: string) =>
  fetch(url).then((r) => (r.ok ? r.json() : null));

export default function DashboardView() {
  const { data: rankings } = useSWR<TropomiRanking[]>(
    "/api/tropomi/rankings?limit=10",
    fetcher,
    { revalidateOnFocus: false }
  );

  const { data: alerts } = useSWR<AlertListResponse>(
    "/api/alerts?acknowledged=false&limit=10",
    fetcher,
    { revalidateOnFocus: false }
  );

  const { data: recentDetections } = useSWR<Array<Record<string, unknown>>>(
    "/api/sentinel2/detections?limit=5",
    fetcher,
    { revalidateOnFocus: false }
  );

  return (
    <div className="space-y-8">
      {/* Top row: summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <SummaryCard
          label="Active Facilities"
          value="110"
          subtext="Australian coal mines"
        />
        <SummaryCard
          label="Unacknowledged Alerts"
          value={alerts?.total_count?.toString() ?? "—"}
          subtext="Pending review"
          urgent={!!alerts?.total_count && alerts.total_count > 0}
        />
        <SummaryCard
          label="TROPOMI Rankings"
          value={rankings?.length?.toString() ?? "—"}
          subtext="Facilities with data"
        />
        <SummaryCard
          label="S2 Detections"
          value={recentDetections?.length?.toString() ?? "—"}
          subtext="Recent plumes"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* TROPOMI rankings */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
            <h2 className="text-sm font-bold">TROPOMI Intensity Rankings</h2>
            <Link
              href="/facilities"
              className="text-xs text-zinc-500 hover:text-zinc-300"
            >
              View all
            </Link>
          </div>
          <div className="divide-y divide-zinc-800/50">
            {!rankings || rankings.length === 0 ? (
              <div className="p-6 text-center text-zinc-600 text-sm">
                No TROPOMI rankings yet. Run the pipeline to see results.
              </div>
            ) : (
              rankings.map((r, i) => {
                const level = getIntensityLevel(r.intensity_score ?? 0);
                return (
                  <Link
                    key={r.facility_id}
                    href={`/facilities/${r.facility_id}/tropomi`}
                    className="flex items-center px-4 py-3 hover:bg-zinc-800/50 transition-colors"
                  >
                    <span className="text-zinc-600 text-sm w-6">
                      {i + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">
                        {r.facility_name}
                      </div>
                      <div className="text-xs text-zinc-600">
                        {r.state} — {r.operator}
                      </div>
                    </div>
                    <div className="text-right ml-3">
                      <div
                        className="text-sm font-bold"
                        style={{ color: level.color }}
                      >
                        {r.intensity_score?.toFixed(0)}
                      </div>
                      <div className="text-xs text-zinc-600">{level.label}</div>
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </div>

        {/* Recent alerts */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
            <h2 className="text-sm font-bold">Recent Alerts</h2>
            <Link
              href="/alerts"
              className="text-xs text-zinc-500 hover:text-zinc-300"
            >
              View all
            </Link>
          </div>
          <div className="divide-y divide-zinc-800/50">
            {!alerts || alerts.items.length === 0 ? (
              <div className="p-6 text-center text-zinc-600 text-sm">
                No unacknowledged alerts.
              </div>
            ) : (
              alerts.items.map((alert) => {
                const sev = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.low;
                return (
                  <div
                    key={alert.id}
                    className="px-4 py-3 hover:bg-zinc-800/50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: sev.color }}
                      />
                      <span className="text-sm font-medium flex-1 truncate">
                        {alert.title}
                      </span>
                      <span
                        className="text-xs px-1.5 py-0.5 rounded capitalize"
                        style={{
                          backgroundColor: `${sev.color}20`,
                          color: sev.color,
                        }}
                      >
                        {alert.severity}
                      </span>
                    </div>
                    <div className="text-xs text-zinc-600 mt-1 ml-4">
                      {ALERT_TYPE_LABELS[alert.alert_type] ?? alert.alert_type}
                      {" — "}
                      {new Date(alert.created_at).toLocaleDateString("en-AU")}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Recent S2 detections */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-zinc-800">
          <h2 className="text-sm font-bold">Recent Sentinel-2 Detections</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-zinc-500 border-b border-zinc-800">
                <th className="text-left px-4 py-2 font-medium">Facility</th>
                <th className="text-left px-4 py-2 font-medium">Date</th>
                <th className="text-right px-4 py-2 font-medium">Emission</th>
                <th className="text-left px-4 py-2 font-medium">Confidence</th>
                <th className="text-right px-4 py-2 font-medium">Wind</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {!recentDetections || recentDetections.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-6 text-center text-zinc-600"
                  >
                    No S2 detections yet.
                  </td>
                </tr>
              ) : (
                recentDetections.map((d, i) => (
                  <tr
                    key={i}
                    className="hover:bg-zinc-800/50 transition-colors"
                  >
                    <td className="px-4 py-2">
                      <Link
                        href={`/facilities/${d.facility_id}`}
                        className="hover:text-orange-400"
                      >
                        {String(d.facility_name ?? "")}
                      </Link>
                    </td>
                    <td className="px-4 py-2 text-zinc-500">
                      {new Date(
                        String(d.scene_datetime ?? "")
                      ).toLocaleDateString("en-AU")}
                    </td>
                    <td className="px-4 py-2 text-right font-medium">
                      {typeof d.emission_rate_kg_hr === "number"
                        ? d.emission_rate_kg_hr >= 1000
                          ? `${(d.emission_rate_kg_hr / 1000).toFixed(1)} t/hr`
                          : `${d.emission_rate_kg_hr.toFixed(0)} kg/hr`
                        : "—"}
                    </td>
                    <td className="px-4 py-2 capitalize text-zinc-500">
                      {String(d.confidence ?? "")}
                    </td>
                    <td className="px-4 py-2 text-right text-zinc-500">
                      {typeof d.wind_speed_10m === "number"
                        ? `${d.wind_speed_10m.toFixed(1)} m/s`
                        : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  subtext,
  urgent = false,
}: {
  label: string;
  value: string;
  subtext: string;
  urgent?: boolean;
}) {
  return (
    <div
      className={`bg-zinc-900/50 border rounded-lg p-4 ${
        urgent ? "border-red-500/50" : "border-zinc-800"
      }`}
    >
      <div className="text-xs text-zinc-500">{label}</div>
      <div
        className={`text-2xl font-bold mt-1 ${urgent ? "text-red-400" : ""}`}
      >
        {value}
      </div>
      <div className="text-xs text-zinc-600 mt-1">{subtext}</div>
    </div>
  );
}
