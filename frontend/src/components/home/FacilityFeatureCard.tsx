import Link from "next/link";
import type { Facility } from "@/lib/api/facility-types";
import { getStatusLabel, STATE_LABELS, FACILITY_STATUS_COLORS } from "@/lib/api/facility-types";

interface FacilityFeatureCardProps {
  facility: Facility;
}

export default function FacilityFeatureCard({ facility }: FacilityFeatureCardProps) {
  const statusColor = FACILITY_STATUS_COLORS[facility.status] ?? "#666666";

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 hover:border-zinc-700 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold">{facility.name}</h3>
          <p className="text-sm text-zinc-500 mt-1">
            {facility.operator} — {facility.state && STATE_LABELS[facility.state]}
          </p>
        </div>
        <span
          className="text-xs px-2 py-1 rounded-full font-medium"
          style={{
            backgroundColor: `${statusColor}20`,
            color: statusColor,
          }}
        >
          {getStatusLabel(facility.status)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <span className="text-zinc-600">Type</span>
          <p className="text-zinc-300 capitalize">
            {facility.facility_type.replace(/_/g, " ")}
          </p>
        </div>
        <div>
          <span className="text-zinc-600">Commodity</span>
          <p className="text-zinc-300">{facility.commodity ?? "—"}</p>
        </div>
        <div>
          <span className="text-zinc-600">Coordinates</span>
          <p className="text-zinc-300">
            {facility.latitude.toFixed(2)}, {facility.longitude.toFixed(2)}
          </p>
        </div>
        <div>
          <span className="text-zinc-600">NGER ID</span>
          <p className="text-zinc-300">{facility.nger_id ?? "—"}</p>
        </div>
      </div>

      <Link
        href={`/facilities/${facility.id}`}
        className="inline-flex items-center text-sm text-orange-400 hover:text-orange-300 font-medium"
      >
        View facility details &rarr;
      </Link>
    </div>
  );
}
