import { Suspense } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getPlume } from "@/lib/api/carbon-mapper";
import { getPlumeCoordinates, getSectorLabel } from "@/lib/api/types";
import {
  formatEmissionRate,
  formatDate,
  formatCoordinate,
} from "@/lib/utils/formatting";
import PlumeStats from "@/components/ui/PlumeStats";
import LeakViewer from "@/components/leak/LeakViewer";

interface LeakPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: LeakPageProps): Promise<Metadata> {
  const { id } = await params;
  const plume = await getPlume(id);
  if (!plume) return { title: "Leak Not Found" };

  const { latitude, longitude } = getPlumeCoordinates(plume);
  const emission = formatEmissionRate(plume.emission_auto);
  const location = `${formatCoordinate(latitude, "lat")}, ${formatCoordinate(longitude, "lon")}`;

  return {
    title: `${emission} ${plume.gas} Leak - ${location}`,
    description: `Satellite-detected ${plume.gas} emission of ${emission} at ${location}. ${getSectorLabel(plume.sector)} sector. Detected ${formatDate(plume.scene_timestamp)}.`,
    openGraph: {
      images: plume.plume_rgb_png ? [{ url: plume.plume_rgb_png }] : [],
    },
  };
}

export default async function LeakPage({ params }: LeakPageProps) {
  const { id } = await params;
  const plume = await getPlume(id);

  if (!plume) {
    notFound();
  }

  return (
    <div className="space-y-8">
      {/* 3D Viewer */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-4">
        <Suspense
          fallback={
            <div className="h-[500px] bg-zinc-950 rounded-xl flex items-center justify-center">
              <div className="text-zinc-600 animate-pulse">
                Loading 3D visualization...
              </div>
            </div>
          }
        >
          <LeakViewer plume={plume} />
        </Suspense>
      </section>

      {/* Stats and details */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <PlumeStats plume={plume} />
          </div>

          <div>
            <h3 className="text-sm text-zinc-500 uppercase tracking-wider mb-3">
              Satellite Image
            </h3>
            {plume.plume_rgb_png ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={plume.plume_rgb_png}
                alt="Satellite view of plume"
                className="w-full rounded-lg border border-zinc-800"
              />
            ) : (
              <div className="aspect-video bg-zinc-900 rounded-lg flex items-center justify-center text-zinc-600">
                No image available
              </div>
            )}

            <div className="mt-4 space-y-2">
              <h3 className="text-sm text-zinc-500 uppercase tracking-wider mb-2">
                Raw Data
              </h3>
              {plume.plume_tif && (
                <a
                  href={plume.plume_tif}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm text-orange-400 hover:text-orange-300"
                >
                  Download Plume GeoTIFF
                </a>
              )}
              {plume.con_tif && (
                <a
                  href={plume.con_tif}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm text-orange-400 hover:text-orange-300"
                >
                  Download Concentration GeoTIFF
                </a>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
