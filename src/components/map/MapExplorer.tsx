"use client";

import { useState, Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import GlobeView from "@/components/three/GlobeView";
import type { PlumeAnnotated } from "@/lib/api/types";
import { getPlumeCoordinates, getSectorLabel } from "@/lib/api/types";
import { formatEmissionRate, formatCoordinate } from "@/lib/utils/formatting";
import { GAS_COLORS } from "@/lib/plume/plume-color";
import Link from "next/link";

interface MapExplorerProps {
  plumes: PlumeAnnotated[];
}

export default function MapExplorer({ plumes }: MapExplorerProps) {
  const [gasFilter, setGasFilter] = useState<"all" | "CH4" | "CO2">("all");

  const filtered =
    gasFilter === "all"
      ? plumes
      : plumes.filter((p) => p.gas === gasFilter);

  return (
    <div className="relative h-full">
      {/* 3D Globe */}
      <Canvas
        className="h-full w-full"
        camera={{
          position: [0, 80, 220],
          near: 1,
          far: 2000,
          fov: 45,
        }}
        frameloop="always"
      >
        <Suspense fallback={null}>
          <GlobeView plumes={filtered} autoRotate={false} />
        </Suspense>
      </Canvas>

      {/* Overlay controls */}
      <div className="absolute top-4 left-4 z-10 space-y-3">
        <div className="bg-black/80 backdrop-blur-md rounded-lg p-3 border border-zinc-800">
          <h2 className="text-sm font-bold text-white mb-2">Filter</h2>
          <div className="flex gap-2">
            {(["all", "CH4", "CO2"] as const).map((gas) => (
              <button
                key={gas}
                onClick={() => setGasFilter(gas)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  gasFilter === gas
                    ? "bg-orange-500/20 text-orange-400"
                    : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {gas === "all" ? "All" : gas}
              </button>
            ))}
          </div>
          <div className="text-xs text-zinc-500 mt-2">
            {filtered.length} plumes shown
          </div>
        </div>
      </div>

      {/* Plume list sidebar */}
      <div className="absolute top-4 right-4 bottom-4 w-72 z-10 bg-black/80 backdrop-blur-md rounded-lg border border-zinc-800 overflow-hidden flex flex-col">
        <div className="p-3 border-b border-zinc-800">
          <h2 className="text-sm font-bold text-white">Top Emitters</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {filtered.slice(0, 50).map((plume) => {
            const { latitude, longitude } = getPlumeCoordinates(plume);
            const gasColor = GAS_COLORS[plume.gas];
            return (
              <Link
                key={plume.plume_id}
                href={`/leak/${plume.plume_id}`}
                className="block p-3 border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors"
              >
                <div className="flex items-baseline justify-between">
                  <span className="text-sm font-bold text-white">
                    {formatEmissionRate(plume.emission_auto)}
                  </span>
                  <span
                    className="text-xs font-medium"
                    style={{ color: gasColor.primary }}
                  >
                    {plume.gas}
                  </span>
                </div>
                <div className="text-xs text-zinc-500 mt-0.5">
                  {formatCoordinate(latitude, "lat")},{" "}
                  {formatCoordinate(longitude, "lon")}
                </div>
                <div className="text-xs text-zinc-600 mt-0.5">
                  {getSectorLabel(plume.sector)}
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
