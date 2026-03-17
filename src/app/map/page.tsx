import { Suspense } from "react";
import type { Metadata } from "next";
import { getTopEmitters, getPlumesByBbox } from "@/lib/api/carbon-mapper";
import { getDeksProjectContext, geojsonToBbox } from "@/lib/api/deks-context";
import MapExplorer from "@/components/map/MapExplorer";

export const metadata: Metadata = {
  title: "Global Map",
  description:
    "Explore satellite-detected methane emissions on an interactive 3D globe.",
};

export default async function MapPage() {
  const ctx = await getDeksProjectContext();
  const bbox = ctx?.bounds ? geojsonToBbox(ctx.bounds) : null;

  // When running inside DEKS with project bounds, fetch plumes within those bounds.
  // Otherwise fall back to top emitters globally.
  const plumes = bbox
    ? await getPlumesByBbox(bbox, 200)
    : await getTopEmitters(200);

  return (
    <div className="h-[calc(100vh-3.5rem)]">
      <Suspense
        fallback={
          <div className="h-full bg-zinc-950 flex items-center justify-center">
            <div className="text-zinc-600 animate-pulse">Loading map...</div>
          </div>
        }
      >
        <MapExplorer plumes={plumes} initialBbox={bbox} />
      </Suspense>
    </div>
  );
}
