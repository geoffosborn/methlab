import type { Metadata } from "next";
import { getFacility } from "@/lib/api/methlab-api";
import Link from "next/link";
import NgerMethod2Report from "@/components/reports/NgerMethod2Report";

interface NgerReportPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: NgerReportPageProps): Promise<Metadata> {
  const { id } = await params;
  const facility = await getFacility(Number(id)).catch(() => null);
  return {
    title: facility
      ? `${facility.name} — NGER Method 2 Report`
      : "NGER Method 2 Report",
  };
}

export default async function NgerReportPage({ params }: NgerReportPageProps) {
  const { id } = await params;
  const facilityId = Number(id);
  const facility = await getFacility(facilityId).catch(() => null);

  const facilityName = facility?.name ?? "Facility";
  const ngerId = facility?.nger_id ?? undefined;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      {/* Breadcrumb */}
      <div className="mb-6 print:hidden">
        <Link
          href="/facilities"
          className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          Facilities
        </Link>
        <span className="text-zinc-700 mx-2">/</span>
        <Link
          href={`/facilities/${facilityId}`}
          className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {facilityName}
        </Link>
        <span className="text-zinc-700 mx-2">/</span>
        <span className="text-sm text-zinc-400">NGER Method 2 Report</span>
      </div>

      {/* Header */}
      <div className="mb-8 print:hidden">
        <h1 className="text-3xl font-bold mb-1">{facilityName}</h1>
        <p className="text-zinc-500">
          NGER Method 2 — Fugitive Emissions Report
        </p>
      </div>

      <NgerMethod2Report
        facilityId={facilityId}
        facilityName={facilityName}
        ngerIdDisplay={ngerId}
      />
    </div>
  );
}
