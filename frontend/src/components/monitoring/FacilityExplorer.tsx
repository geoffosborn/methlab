"use client";

import { useState, useMemo, Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import GlobeView from "@/components/three/GlobeView";
import type { Facility } from "@/lib/api/facility-types";
import { FACILITY_STATUS_COLORS, getStatusLabel } from "@/lib/api/facility-types";
import Link from "next/link";

interface FacilityExplorerProps {
  facilities: Facility[];
}

const STATES = ["All", "QLD", "NSW", "VIC", "WA", "SA", "TAS"] as const;

export default function FacilityExplorer({
  facilities,
}: FacilityExplorerProps) {
  const [stateFilter, setStateFilter] = useState<string>("All");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let items = facilities;
    if (stateFilter !== "All") {
      items = items.filter((f) => f.state === stateFilter);
    }
    if (statusFilter !== "all") {
      items = items.filter((f) => f.status === statusFilter);
    }
    if (search) {
      const q = search.toLowerCase();
      items = items.filter(
        (f) =>
          f.name.toLowerCase().includes(q) ||
          f.operator?.toLowerCase().includes(q)
      );
    }
    return items;
  }, [facilities, stateFilter, statusFilter, search]);

  // State counts for filter badges
  const stateCounts = useMemo(() => {
    const counts: Record<string, number> = { All: facilities.length };
    for (const f of facilities) {
      if (f.state) counts[f.state] = (counts[f.state] || 0) + 1;
    }
    return counts;
  }, [facilities]);

  return (
    <div className="h-[calc(100vh-3.5rem)] relative">
      {/* 3D Globe - centered on Australia */}
      <Canvas
        className="h-full w-full"
        camera={{
          position: [50, -80, 180],
          near: 1,
          far: 2000,
          fov: 45,
        }}
        frameloop="always"
      >
        <Suspense fallback={null}>
          <GlobeView plumes={[]} facilities={filtered} autoRotate={false} />
        </Suspense>
      </Canvas>

      {/* Filter controls */}
      <div className="absolute top-4 left-4 z-10 space-y-3">
        <div className="bg-black/80 backdrop-blur-md rounded-lg p-3 border border-zinc-800">
          <h2 className="text-sm font-bold text-white mb-2">
            Coal Mine Facilities
          </h2>

          {/* Search */}
          <input
            type="text"
            placeholder="Search mines..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-3 py-1.5 rounded bg-zinc-900 border border-zinc-700 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-orange-500/50 mb-2"
          />

          {/* State filter */}
          <div className="flex flex-wrap gap-1.5 mb-2">
            {STATES.map((state) => (
              <button
                key={state}
                onClick={() => setStateFilter(state)}
                className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                  stateFilter === state
                    ? "bg-orange-500/20 text-orange-400"
                    : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {state}
                {stateCounts[state] ? ` (${stateCounts[state]})` : ""}
              </button>
            ))}
          </div>

          {/* Status filter */}
          <div className="flex gap-1.5">
            {["all", "active", "care_and_maintenance", "closed"].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                  statusFilter === s
                    ? "bg-orange-500/20 text-orange-400"
                    : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {s === "all" ? "All" : getStatusLabel(s)}
              </button>
            ))}
          </div>

          <div className="text-xs text-zinc-500 mt-2">
            {filtered.length} facilities shown
          </div>
        </div>
      </div>

      {/* Facility list sidebar */}
      <div className="absolute top-4 right-4 bottom-4 w-80 z-10 bg-black/80 backdrop-blur-md rounded-lg border border-zinc-800 overflow-hidden flex flex-col">
        <div className="p-3 border-b border-zinc-800">
          <h2 className="text-sm font-bold text-white">Facilities</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {filtered.length === 0 && (
            <div className="p-6 text-center text-zinc-600 text-sm">
              {facilities.length === 0
                ? "No facilities loaded. Start the MethLab API to see coal mine data."
                : "No facilities match your filters."}
            </div>
          )}
          {filtered.map((facility) => (
            <Link
              key={facility.id}
              href={`/facilities/${facility.id}`}
              className="block p-3 border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors"
            >
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-bold text-white">
                  {facility.name}
                </span>
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0 ml-2"
                  style={{
                    backgroundColor:
                      FACILITY_STATUS_COLORS[facility.status] ?? "#666",
                  }}
                />
              </div>
              <div className="text-xs text-zinc-500 mt-0.5">
                {facility.operator}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-zinc-600">{facility.state}</span>
                <span className="text-xs text-zinc-700">
                  {facility.commodity}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
