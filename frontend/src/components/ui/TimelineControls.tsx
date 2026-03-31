"use client";

import { useCallback, useRef } from "react";
import type { PlumeKeyframe } from "@/lib/api/plume-timeseries";
import type { InterpolatedFrame } from "@/hooks/usePlumePlayback";
import { getEmissionSeverityColor } from "@/lib/plume/plume-color";

interface TimelineControlsProps {
  keyframes: PlumeKeyframe[];
  currentFrame: InterpolatedFrame;
  progress: number;
  isPlaying: boolean;
  speed: number;
  onToggle: () => void;
  onSetTime: (t: number) => void;
  onSetSpeed: (s: number) => void;
}

function formatDate(date: Date): string {
  return date.toLocaleDateString("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-AU", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function TimelineControls({
  keyframes,
  currentFrame,
  progress,
  isPlaying,
  speed,
  onToggle,
  onSetTime,
  onSetSpeed,
}: TimelineControlsProps) {
  const trackRef = useRef<HTMLDivElement>(null);

  const handleTrackClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!trackRef.current) return;
      const rect = trackRef.current.getBoundingClientRect();
      const t = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      onSetTime(t);
    },
    [onSetTime]
  );

  const handleDrag = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!trackRef.current) return;
      const rect = trackRef.current.getBoundingClientRect();

      const move = (ev: PointerEvent) => {
        const t = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
        onSetTime(t);
      };

      const up = () => {
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", up);
      };

      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
    },
    [onSetTime]
  );

  if (keyframes.length < 2) return null;

  const firstDate = keyframes[0].timestamp;
  const lastDate = keyframes[keyframes.length - 1].timestamp;

  return (
    <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 space-y-3">
      {/* Header: timestamp + emission */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Play/pause */}
          <button
            onClick={onToggle}
            className="w-8 h-8 flex items-center justify-center rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition-colors"
          >
            {isPlaying ? (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <rect x="2" y="1" width="3.5" height="12" rx="1" />
                <rect x="8.5" y="1" width="3.5" height="12" rx="1" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                <path d="M3 1.5v11l9-5.5z" />
              </svg>
            )}
          </button>

          <div>
            <div className="text-sm font-medium text-zinc-200">
              {formatDate(currentFrame.timestamp)}
              <span className="text-zinc-500 ml-1">{formatTime(currentFrame.timestamp)}</span>
            </div>
            <div className="text-xs text-zinc-500">
              {currentFrame.emission.toFixed(0)} kg/hr
              <span className="mx-1.5">·</span>
              Wind {currentFrame.windSpeed.toFixed(1)} m/s at {currentFrame.windDirection.toFixed(0)}°
            </div>
          </div>
        </div>

        {/* Speed selector */}
        <div className="flex gap-1">
          {[0.5, 1, 2, 4].map((s) => (
            <button
              key={s}
              onClick={() => onSetSpeed(s)}
              className={`px-2 py-0.5 rounded text-xs font-mono transition-colors ${
                speed === s
                  ? "bg-zinc-700 text-white"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Timeline track */}
      <div
        ref={trackRef}
        className="relative h-6 cursor-pointer group"
        onClick={handleTrackClick}
        onPointerDown={handleDrag}
      >
        {/* Track background */}
        <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-1 bg-zinc-800 rounded-full" />

        {/* Progress fill */}
        <div
          className="absolute top-1/2 -translate-y-1/2 left-0 h-1 bg-orange-500/60 rounded-full"
          style={{ width: `${progress * 100}%` }}
        />

        {/* Keyframe dots — colored by emission severity */}
        {keyframes.map((kf, i) => {
          const pos = keyframes.length > 1 ? i / (keyframes.length - 1) : 0;
          const dotColor = getEmissionSeverityColor(kf.emission);
          return (
            <div
              key={kf.plumeId + i}
              className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-2 h-2 rounded-full transition-opacity group-hover:opacity-100 opacity-80"
              style={{ left: `${pos * 100}%`, backgroundColor: dotColor }}
              title={`${formatDate(kf.timestamp)} — ${kf.emission.toFixed(0)} kg/hr`}
            />
          );
        })}

        {/* Scrubber handle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-orange-500 border-2 border-orange-300 shadow-lg shadow-orange-500/20"
          style={{ left: `${progress * 100}%` }}
        />
      </div>

      {/* Date range */}
      <div className="flex justify-between text-[10px] text-zinc-600">
        <span>{formatDate(firstDate)}</span>
        <span>{keyframes.length} observations</span>
        <span>{formatDate(lastDate)}</span>
      </div>
    </div>
  );
}
