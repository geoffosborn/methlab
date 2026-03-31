import type { Metadata } from "next";
import { getFacility } from "@/lib/api/methlab-api";
import { notFound } from "next/navigation";
import Link from "next/link";
import TropomiView from "@/components/monitoring/TropomiView";

interface TropomiPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: TropomiPageProps): Promise<Metadata> {
  const { id } = await params;
  const facility = await getFacility(Number(id)).catch(() => null);
  return {
    title: facility
      ? `${facility.name} — TROPOMI Screening`
      : "TROPOMI Screening",
  };
}

export default async function TropomiPage({ params }: TropomiPageProps) {
  const { id } = await params;
  const facility = await getFacility(Number(id)).catch(() => null);

  if (!facility) {
    notFound();
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          href="/facilities"
          className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          Facilities
        </Link>
        <span className="text-zinc-700 mx-2">/</span>
        <Link
          href={`/facilities/${facility.id}`}
          className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {facility.name}
        </Link>
        <span className="text-zinc-700 mx-2">/</span>
        <span className="text-sm text-zinc-400">TROPOMI</span>
      </div>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-1">{facility.name}</h1>
        <p className="text-zinc-500">
          TROPOMI CH4 Wind-Rotated Screening Analysis
        </p>
      </div>

      <TropomiView facilityId={facility.id} />
    </div>
  );
}
