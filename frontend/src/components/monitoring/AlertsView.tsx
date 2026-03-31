"use client";

import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import type { AlertListResponse } from "@/lib/api/alert-types";
import { SEVERITY_CONFIG, ALERT_TYPE_LABELS } from "@/lib/api/alert-types";

const fetcher = (url: string) =>
  fetch(url).then((r) => (r.ok ? r.json() : { total_count: 0, items: [] }));

export default function AlertsView() {
  const [filter, setFilter] = useState<"all" | "unacknowledged">(
    "unacknowledged"
  );
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  const params = new URLSearchParams();
  if (filter === "unacknowledged") params.set("acknowledged", "false");
  if (severityFilter !== "all") params.set("severity", severityFilter);
  params.set("limit", "50");

  const { data, mutate } = useSWR<AlertListResponse>(
    `/api/alerts?${params}`,
    fetcher,
    { revalidateOnFocus: false }
  );

  const handleAcknowledge = async (alertId: number) => {
    await fetch(`/api/alerts/${alertId}/acknowledge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ acknowledged_by: "operator" }),
    });
    mutate();
  };

  const alerts = data?.items ?? [];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {(["unacknowledged", "all"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filter === f
                ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                : "bg-zinc-900 text-zinc-500 border border-zinc-800 hover:text-zinc-300"
            }`}
          >
            {f === "unacknowledged" ? "Unacknowledged" : "All"}
          </button>
        ))}
        <span className="text-zinc-700 self-center">|</span>
        {["all", "critical", "high", "medium", "low"].map((s) => (
          <button
            key={s}
            onClick={() => setSeverityFilter(s)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
              severityFilter === s
                ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                : "bg-zinc-900 text-zinc-500 border border-zinc-800 hover:text-zinc-300"
            }`}
          >
            {s === "all" ? "All Severity" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Count */}
      <p className="text-sm text-zinc-500">
        {data?.total_count ?? 0} alerts
      </p>

      {/* Alert list */}
      {alerts.length === 0 ? (
        <div className="bg-zinc-900/30 border border-zinc-800 border-dashed rounded-lg p-12 text-center">
          <p className="text-zinc-600">No alerts matching your filters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => {
            const sev =
              SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.low;
            return (
              <div
                key={alert.id}
                className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <span
                    className="w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0"
                    style={{ backgroundColor: sev.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-sm">{alert.title}</h3>
                      <span
                        className="text-xs px-1.5 py-0.5 rounded capitalize"
                        style={{
                          backgroundColor: `${sev.color}20`,
                          color: sev.color,
                        }}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-xs text-zinc-600 px-1.5 py-0.5 rounded bg-zinc-800">
                        {ALERT_TYPE_LABELS[alert.alert_type] ??
                          alert.alert_type}
                      </span>
                    </div>
                    {alert.description && (
                      <p className="text-sm text-zinc-500 mt-1">
                        {alert.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-zinc-600">
                      <span>
                        {new Date(alert.created_at).toLocaleString("en-AU")}
                      </span>
                      <Link
                        href={`/facilities/${alert.facility_id}`}
                        className="hover:text-orange-400"
                      >
                        View facility
                      </Link>
                    </div>
                  </div>
                  {!alert.acknowledged && (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="px-3 py-1 text-xs rounded border border-zinc-700 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors flex-shrink-0"
                    >
                      Acknowledge
                    </button>
                  )}
                  {alert.acknowledged && (
                    <span className="text-xs text-zinc-600 flex-shrink-0">
                      Ack&apos;d
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
