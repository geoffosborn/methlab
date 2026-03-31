import { Suspense } from "react";
import Link from "next/link";
import { getTopEmitters, getRecentPlumes, getPlumeCount } from "@/lib/api/carbon-mapper";
import PlumeCard from "@/components/ui/PlumeCard";
import HeroGlobe from "@/components/home/HeroGlobe";

export default async function HomePage() {
  const [topEmitters, recentPlumes, totalCount] = await Promise.all([
    getTopEmitters(6),
    getRecentPlumes(3),
    getPlumeCount(),
  ]);

  const leakOfTheWeek = topEmitters[0] ?? recentPlumes[0];

  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div className="space-y-6">
              <h1 className="text-5xl sm:text-6xl font-bold leading-tight">
                Making
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-500">
                  invisible
                </span>{" "}
                emissions
                <br />
                visible
              </h1>
              <p className="text-lg text-zinc-400 max-w-md">
                Real satellite data. Immersive 3D visualization.{" "}
                {totalCount.toLocaleString()}+ methane plumes detected globally,
                rendered as volumetric plumes you can explore.
              </p>
              <div className="flex gap-4">
                <Link
                  href="/leaks"
                  className="px-6 py-3 rounded-lg bg-gradient-to-r from-orange-500 to-red-600 text-white font-semibold hover:from-orange-600 hover:to-red-700 transition-all"
                >
                  Explore Leaks
                </Link>
                <Link
                  href="/map"
                  className="px-6 py-3 rounded-lg border border-zinc-700 text-zinc-300 font-semibold hover:bg-zinc-800 transition-all"
                >
                  View Map
                </Link>
              </div>
            </div>

            <Suspense
              fallback={
                <div className="h-[500px] bg-zinc-950 rounded-2xl flex items-center justify-center">
                  <div className="text-zinc-600 animate-pulse">Loading globe...</div>
                </div>
              }
            >
              <div className="h-[500px]">
                <HeroGlobe plumes={topEmitters} />
              </div>
            </Suspense>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <StatBlock
              value={totalCount.toLocaleString()}
              label="Plumes Detected"
            />
            <StatBlock value="35,000+" label="Tonnes CH4/hr" />
            <StatBlock value="6+" label="Satellite Platforms" />
            <StatBlock value="Global" label="Coverage" />
          </div>
        </div>
      </section>

      {/* Leak of the Week */}
      {leakOfTheWeek && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-baseline justify-between mb-6">
            <h2 className="text-3xl font-bold">Leak of the Week</h2>
            <Link
              href={`/leak/${leakOfTheWeek.plume_id}`}
              className="text-orange-400 hover:text-orange-300 text-sm font-medium"
            >
              View in 3D &rarr;
            </Link>
          </div>
          <div className="max-w-sm">
            <PlumeCard plume={leakOfTheWeek} />
          </div>
        </section>
      )}

      {/* Recent detections */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pb-16">
        <div className="flex items-baseline justify-between mb-6">
          <h2 className="text-3xl font-bold">Recent Detections</h2>
          <Link
            href="/leaks"
            className="text-orange-400 hover:text-orange-300 text-sm font-medium"
          >
            View all &rarr;
          </Link>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {recentPlumes.map((plume) => (
            <PlumeCard key={plume.plume_id} plume={plume} />
          ))}
        </div>
      </section>
    </div>
  );
}

function StatBlock({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="text-3xl font-bold text-white">{value}</div>
      <div className="text-sm text-zinc-500 mt-1">{label}</div>
    </div>
  );
}
