import type { PlumeAnnotated } from "@/lib/api/types";
import { getPlumeCoordinates, getSectorLabel } from "@/lib/api/types";
import {
  formatEmissionRate,
  formatDate,
  formatCoordinate,
  formatWindSpeed,
  formatWindDirection,
  getEmissionEquivalencies,
} from "@/lib/utils/formatting";
import {
  getEmissionSeverityColor,
  getEmissionSeverityLabel,
  GAS_COLORS,
} from "@/lib/plume/plume-color";

interface PlumeStatsProps {
  plume: PlumeAnnotated;
}

export default function PlumeStats({ plume }: PlumeStatsProps) {
  const { latitude, longitude } = getPlumeCoordinates(plume);
  const emission = plume.emission_auto ?? 0;
  const equivalencies = getEmissionEquivalencies(emission);
  const gasColor = GAS_COLORS[plume.gas];
  const severityColor = getEmissionSeverityColor(plume.emission_auto);

  return (
    <div className="space-y-6">
      {/* Primary stat */}
      <div>
        <div className="text-sm text-zinc-500 uppercase tracking-wider mb-1">
          Emission Rate
        </div>
        <div className="flex items-baseline gap-3">
          <span className="text-4xl font-bold text-white">
            {formatEmissionRate(plume.emission_auto)}
          </span>
          <span
            className="px-2 py-1 rounded text-xs font-bold"
            style={{
              backgroundColor: severityColor,
              color: "#000",
            }}
          >
            {getEmissionSeverityLabel(plume.emission_auto)}
          </span>
        </div>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-4">
        <StatItem label="Gas Type">
          <span style={{ color: gasColor.primary }}>{gasColor.label}</span>
        </StatItem>
        <StatItem label="Sector">
          {getSectorLabel(plume.sector)}
        </StatItem>
        <StatItem label="Location">
          {formatCoordinate(latitude, "lat")},{" "}
          {formatCoordinate(longitude, "lon")}
        </StatItem>
        <StatItem label="Detected">
          {formatDate(plume.scene_timestamp)}
        </StatItem>
        <StatItem label="Wind Speed">
          {formatWindSpeed(plume.wind_speed_avg_auto)}
        </StatItem>
        <StatItem label="Wind Direction">
          {formatWindDirection(plume.wind_direction_avg_auto)}
        </StatItem>
        <StatItem label="Platform">{plume.platform}</StatItem>
        <StatItem label="Quality">{plume.plume_quality ?? "N/A"}</StatItem>
      </div>

      {/* Equivalencies */}
      {emission > 0 && (
        <div className="border-t border-zinc-800 pt-4">
          <div className="text-sm text-zinc-500 uppercase tracking-wider mb-3">
            Annual Impact
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between text-zinc-300">
              <span>CO2 equivalent</span>
              <span className="font-mono">
                {equivalencies.co2eqTonnesPerYear.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}{" "}
                tonnes/yr
              </span>
            </div>
            <div className="flex justify-between text-zinc-300">
              <span>Equivalent cars</span>
              <span className="font-mono">
                {equivalencies.carsEquivalent.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-zinc-300">
              <span>Equivalent homes</span>
              <span className="font-mono">
                {equivalencies.homesEquivalent.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between text-zinc-300">
              <span>Social cost (EPA)</span>
              <span className="font-mono text-red-400">
                $
                {equivalencies.socialCostPerYear.toLocaleString(undefined, {
                  maximumFractionDigits: 0,
                })}
                /yr
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatItem({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="text-xs text-zinc-600 uppercase tracking-wider">
        {label}
      </div>
      <div className="text-sm text-zinc-300 mt-0.5">{children}</div>
    </div>
  );
}
