"use client";

import { getEmissionSeverityColor, getEmissionSeverityLabel } from "@/lib/plume/plume-color";

interface PlumeHUDProps {
  emission: number;
  windSpeed: number;
  windDirection: number;
  timestamp?: Date;
  gas: "CH4" | "CO2";
}

export default function PlumeHUD({
  emission,
  windSpeed,
  windDirection,
  timestamp,
  gas,
}: PlumeHUDProps) {
  const severityColor = getEmissionSeverityColor(emission);
  const severityLabel = getEmissionSeverityLabel(emission);

  return (
    <div className="absolute top-3 left-3 pointer-events-none z-10">
      <div className="bg-black/60 backdrop-blur-sm rounded-lg px-3 py-2 space-y-1 text-xs font-mono">
        {/* Emission with severity */}
        <div className="flex items-center gap-2">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: severityColor }}
          />
          <span className="text-white font-bold text-sm">
            {emission.toFixed(0)} kg/hr
          </span>
          <span className="text-zinc-400">{gas === "CH4" ? "CH₄" : "CO₂"}</span>
          <span style={{ color: severityColor }}>{severityLabel}</span>
        </div>

        {/* Wind */}
        <div className="text-zinc-400">
          Wind {windSpeed.toFixed(1)} m/s at {windDirection.toFixed(0)}°
        </div>

        {/* Timestamp */}
        {timestamp && (
          <div className="text-zinc-500">
            {timestamp.toLocaleDateString("en-AU", {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}{" "}
            {timestamp.toLocaleTimeString("en-AU", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        )}
      </div>
    </div>
  );
}
