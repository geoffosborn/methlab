import type { Metadata } from "next";
import { getFacility } from "@/lib/api/methlab-api";
import { notFound } from "next/navigation";
import Link from "next/link";
import S2View from "@/components/monitoring/S2View";

interface S2PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: S2PageProps): Promise<Metadata> {
  const { id } = await params;
  const facility = await getFacility(Number(id)).catch(() => null);
  return {
    title: facility
      ? `${facility.name} — Sentinel-2 Detection`
      : "Sentinel-2 Detection",
  };
}

export default async function S2Page({ params }: S2PageProps) {
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
        <span className="text-sm text-zinc-400">Sentinel-2</span>
      </div>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-1">{facility.name}</h1>
        <p className="text-zinc-500">
          Sentinel-2 SWIR Methane Plume Detection & Quantification (Varon IME Method)
        </p>
      </div>

      <S2View facilityId={facility.id} />
    </div>
  );
}
