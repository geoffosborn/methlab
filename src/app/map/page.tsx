import { Suspense } from "react";
import type { Metadata } from "next";
import { getTopEmitters } from "@/lib/api/carbon-mapper";
import MapExplorer from "@/components/map/MapExplorer";

export const metadata: Metadata = {
  title: "Global Map",
  description:
    "Explore satellite-detected methane emissions on an interactive 3D globe.",
};

export default async function MapPage() {
  const plumes = await getTopEmitters(200);

  return (
    <div className="h-[calc(100vh-3.5rem)]">
      <Suspense
        fallback={
          <div className="h-full bg-zinc-950 flex items-center justify-center">
            <div className="text-zinc-600 animate-pulse">Loading map...</div>
          </div>
        }
      >
        <MapExplorer plumes={plumes} />
      </Suspense>
    </div>
  );
}
