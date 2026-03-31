import type { Metadata } from "next";
import { getFacility } from "@/lib/api/methlab-api";
import { notFound } from "next/navigation";
import Link from "next/link";
import { getStatusLabel } from "@/lib/api/facility-types";

interface FacilityPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: FacilityPageProps): Promise<Metadata> {
  const { id } = await params;
  const facility = await getFacility(Number(id)).catch(() => null);
  return {
    title: facility ? `${facility.name} | Facilities` : "Facility",
  };
}

export default async function FacilityPage({ params }: FacilityPageProps) {
  const { id } = await params;
  const facility = await getFacility(Number(id)).catch(() => null);

  if (!facility) {
    notFound();
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          href="/facilities"
          className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          Facilities
        </Link>
        <span className="text-zinc-700 mx-2">/</span>
        <span className="text-sm text-zinc-400">{facility.name}</span>
      </div>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold">{facility.name}</h1>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              facility.status === "active"
                ? "bg-green-500/20 text-green-400"
                : facility.status === "closed"
                  ? "bg-red-500/20 text-red-400"
                  : "bg-amber-500/20 text-amber-400"
            }`}
          >
            {getStatusLabel(facility.status)}
          </span>
        </div>
        {facility.operator && (
          <p className="text-zinc-400">{facility.operator}</p>
        )}
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5 space-y-4">
          <h2 className="text-lg font-semibold">Details</h2>
          <dl className="space-y-3">
            <DetailRow label="State" value={facility.state} />
            <DetailRow label="Commodity" value={facility.commodity} />
            <DetailRow label="Type" value="Coal Mine" />
            {facility.nger_id && (
              <DetailRow label="NGER ID" value={facility.nger_id} />
            )}
          </dl>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5 space-y-4">
          <h2 className="text-lg font-semibold">Location</h2>
          <dl className="space-y-3">
            <DetailRow
              label="Latitude"
              value={facility.latitude.toFixed(4) + "\u00B0"}
            />
            <DetailRow
              label="Longitude"
              value={facility.longitude.toFixed(4) + "\u00B0"}
            />
          </dl>
        </div>
      </div>

      {/* NGER Compliance */}
      {facility.metadata &&
        typeof facility.metadata === "object" &&
        "nger_baseline_2024" in facility.metadata && (
          <NgerComplianceCard
            metadata={facility.metadata as Record<string, string | number>}
          />
        )}

      {/* Monitoring sections */}
      <div className="mt-8 space-y-4">
        <h2 className="text-lg font-semibold">Monitoring</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            href={`/facilities/${facility.id}/tropomi`}
            className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5 hover:border-zinc-700 transition-colors group"
          >
            <h3 className="font-semibold group-hover:text-orange-400 transition-colors">
              TROPOMI CH4 Screening
            </h3>
            <p className="text-zinc-500 text-sm mt-1">
              Wind-rotated methane column analysis from Sentinel-5P
            </p>
          </Link>
          <Link
            href={`/facilities/${facility.id}/sentinel2`}
            className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5 hover:border-zinc-700 transition-colors group"
          >
            <h3 className="font-semibold group-hover:text-orange-400 transition-colors">
              Sentinel-2 Detection
            </h3>
            <p className="text-zinc-500 text-sm mt-1">
              High-resolution SWIR plume detection & quantification (Varon IME)
            </p>
          </Link>
          {facility.nger_id && (
            <Link
              href={`/facilities/${facility.id}/nger-report`}
              className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5 hover:border-zinc-700 transition-colors group"
            >
              <h3 className="font-semibold group-hover:text-orange-400 transition-colors">
                NGER Method 2 Report
              </h3>
              <p className="text-zinc-500 text-sm mt-1">
                CER-formatted fugitive emissions report with satellite
                verification
              </p>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string | null | undefined;
}) {
  if (!value) return null;
  return (
    <div className="flex justify-between">
      <dt className="text-zinc-500 text-sm">{label}</dt>
      <dd className="text-sm font-medium">{value}</dd>
    </div>
  );
}

function NgerComplianceCard({
  metadata,
}: {
  metadata: Record<string, string | number>;
}) {
  const baseline = Number(metadata.nger_baseline_2024 ?? 0);
  const reported = Number(metadata.nger_reported_2024 ?? 0);
  const emitter = String(metadata.nger_emitter ?? "");
  const ngerName = String(metadata.nger_name ?? "");

  if (!baseline || !reported) return null;

  const exceedance = reported - baseline;
  const exceedancePct = ((exceedance / baseline) * 100).toFixed(1);
  const isOver = exceedance > 0;

  const formatTonnes = (t: number) => {
    if (t >= 1_000_000) return `${(t / 1_000_000).toFixed(2)}M`;
    if (t >= 1_000) return `${(t / 1_000).toFixed(0)}k`;
    return t.toLocaleString();
  };

  // Bar width as percentage of max(baseline, reported)
  const maxVal = Math.max(baseline, reported);
  const baselinePctWidth = (baseline / maxVal) * 100;
  const reportedPctWidth = (reported / maxVal) * 100;

  return (
    <div className="mt-6 bg-zinc-900/50 border border-zinc-800 rounded-lg p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">NGER Safeguard Compliance</h2>
        <span
          className={`px-2.5 py-1 rounded-full text-xs font-bold ${
            isOver
              ? "bg-red-500/20 text-red-400"
              : "bg-green-500/20 text-green-400"
          }`}
        >
          {isOver ? `${exceedancePct}% OVER` : `${Math.abs(Number(exceedancePct))}% UNDER`}
        </span>
      </div>

      {ngerName && (
        <p className="text-xs text-zinc-500">
          NGER facility: {ngerName}
          {emitter && ` — ${emitter}`}
        </p>
      )}

      <div className="space-y-3">
        {/* Baseline bar */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-zinc-500">Baseline (2023-24)</span>
            <span className="text-zinc-300 font-medium">
              {formatTonnes(baseline)} tCO₂e
            </span>
          </div>
          <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-zinc-500 rounded-full"
              style={{ width: `${baselinePctWidth}%` }}
            />
          </div>
        </div>

        {/* Reported bar */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-zinc-500">Reported Emissions</span>
            <span
              className={`font-medium ${isOver ? "text-red-400" : "text-green-400"}`}
            >
              {formatTonnes(reported)} tCO₂e
            </span>
          </div>
          <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${isOver ? "bg-red-500" : "bg-green-500"}`}
              style={{ width: `${reportedPctWidth}%` }}
            />
          </div>
        </div>
      </div>

      {isOver && (
        <div className="pt-2 border-t border-zinc-800">
          <p className="text-xs text-red-400/80">
            Exceeded baseline by{" "}
            <span className="font-bold">{formatTonnes(exceedance)} tCO₂e</span>.
            Under the reformed Safeguard Mechanism, this facility must
            surrender ACCUs or apply for a multi-year monitoring period.
          </p>
        </div>
      )}
    </div>
  );
}
