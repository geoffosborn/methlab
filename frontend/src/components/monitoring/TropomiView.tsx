"use client";

import useSWR from "swr";
import type { TropomiListResponse } from "@/lib/api/tropomi-types";
import TropomiTearSheet from "./TropomiTearSheet";
import EmissionTimeSeries from "./EmissionTimeSeries";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

interface TropomiViewProps {
  facilityId: number;
}

export default function TropomiView({ facilityId }: TropomiViewProps) {
  const { data, isLoading } = useSWR<TropomiListResponse>(
    `/api/tropomi/facilities/${facilityId}`,
    fetcher,
    { revalidateOnFocus: false }
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2].map((i) => (
          <div
            key={i}
            className="bg-zinc-900/50 border border-zinc-800 rounded-lg h-48 animate-pulse"
          />
        ))}
      </div>
    );
  }

  const observations = data?.items ?? [];

  if (observations.length === 0) {
    return (
      <div className="bg-zinc-900/30 border border-zinc-800 border-dashed rounded-lg p-12 text-center">
        <h3 className="text-lg font-semibold text-zinc-400 mb-2">
          No TROPOMI Data Yet
        </h3>
        <p className="text-zinc-600 text-sm max-w-md mx-auto">
          TROPOMI wind-rotated CH4 analysis will appear here once the
          screening pipeline has processed this facility. The pipeline runs
          monthly for all monitored facilities.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Time series chart */}
      <EmissionTimeSeries observations={observations} />

      {/* Tear sheets grid */}
      <div>
        <h2 className="text-lg font-semibold mb-4">
          Wind-Rotated CH4 Analysis
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {observations.map((obs) => (
            <TropomiTearSheet key={obs.id} observation={obs} />
          ))}
        </div>
      </div>
    </div>
  );
}
