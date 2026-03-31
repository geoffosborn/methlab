import type { PlumeAnnotated } from "@/lib/api/types";
import { getPlumeCoordinates, getSectorLabel } from "@/lib/api/types";
import {
  formatEmissionRate,
  formatDate,
  formatCoordinate,
} from "@/lib/utils/formatting";
import {
  getEmissionSeverityColor,
  getEmissionSeverityLabel,
  GAS_COLORS,
} from "@/lib/plume/plume-color";
import Link from "next/link";

interface PlumeCardProps {
  plume: PlumeAnnotated;
}

export default function PlumeCard({ plume }: PlumeCardProps) {
  const { latitude, longitude } = getPlumeCoordinates(plume);
  const gasColor = GAS_COLORS[plume.gas];
  const severityColor = getEmissionSeverityColor(plume.emission_auto);
  const severityLabel = getEmissionSeverityLabel(plume.emission_auto);

  return (
    <Link
      href={`/leak/${plume.plume_id}`}
      className="group block overflow-hidden rounded-xl bg-zinc-900 border border-zinc-800 hover:border-zinc-600 transition-all duration-200"
    >
      {/* Plume image */}
      <div className="relative aspect-video bg-zinc-950 overflow-hidden">
        {plume.plume_rgb_png ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={plume.plume_rgb_png}
            alt={`Methane plume at ${formatCoordinate(latitude, "lat")}, ${formatCoordinate(longitude, "lon")}`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-zinc-600">
            No image available
          </div>
        )}

        {/* Severity badge */}
        <div
          className="absolute top-3 right-3 px-2 py-1 rounded-full text-xs font-bold text-black"
          style={{ backgroundColor: severityColor }}
        >
          {severityLabel}
        </div>

        {/* Gas type badge */}
        <div
          className="absolute top-3 left-3 px-2 py-1 rounded-full text-xs font-bold text-white"
          style={{ backgroundColor: gasColor.dark }}
        >
          {gasColor.label}
        </div>
      </div>

      {/* Info */}
      <div className="p-4 space-y-2">
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold text-white">
            {formatEmissionRate(plume.emission_auto)}
          </span>
          <span className="text-sm text-zinc-500">
            {formatDate(plume.scene_timestamp)}
          </span>
        </div>

        <div className="text-sm text-zinc-400">
          {formatCoordinate(latitude, "lat")},{" "}
          {formatCoordinate(longitude, "lon")}
        </div>

        <div className="flex items-center gap-2 text-xs text-zinc-500">
          <span>{getSectorLabel(plume.sector)}</span>
          <span className="text-zinc-700">|</span>
          <span>{plume.platform}</span>
        </div>
      </div>
    </Link>
  );
}
