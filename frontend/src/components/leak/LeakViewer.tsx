"use client";

import { useState, useEffect } from "react";
import SceneCanvas from "@/components/three/SceneCanvas";
import LeakScene, { type CameraPreset } from "@/components/three/LeakScene";
import type { TileSource } from "@/components/three/MapTiles";
import TimelineControls from "@/components/ui/TimelineControls";
import PlumeHUD from "@/components/ui/PlumeHUD";
import CaptureButton, { CaptureHandler } from "@/components/ui/CaptureButton";
import type { PlumeAnnotated } from "@/lib/api/types";
import { getPlumeCoordinates } from "@/lib/api/types";
import { fetchPlumeTimeSeries, type PlumeKeyframe } from "@/lib/api/plume-timeseries";
import { usePlumePlayback } from "@/hooks/usePlumePlayback";

interface LeakViewerProps {
  plume: PlumeAnnotated;
}

export default function LeakViewer({ plume }: LeakViewerProps) {
  const [cameraPreset, setCameraPreset] = useState<CameraPreset>("orbit");
  const [tileSource, setTileSource] = useState<TileSource>("satellite");
  const [keyframes, setKeyframes] = useState<PlumeKeyframe[]>([]);
  const [timeSeriesLoading, setTimeSeriesLoading] = useState(true);

  const { latitude, longitude } = getPlumeCoordinates(plume);

  useEffect(() => {
    setTimeSeriesLoading(true);
    fetchPlumeTimeSeries(latitude, longitude, plume.gas)
      .then((kfs) => setKeyframes(kfs))
      .catch(() => setKeyframes([]))
      .finally(() => setTimeSeriesLoading(false));
  }, [latitude, longitude, plume.gas]);

  const playback = usePlumePlayback(keyframes);
  const hasTimeline = keyframes.length >= 2;

  const activeEmission = hasTimeline ? playback.currentFrame.emission : (plume.emission_auto ?? 0);
  const activeWindSpeed = hasTimeline ? playback.currentFrame.windSpeed : plume.wind_speed_avg_auto;
  const activeWindDir = hasTimeline ? playback.currentFrame.windDirection : plume.wind_direction_avg_auto;

  return (
    <div className="space-y-3">
      {/* 3D Viewer with HUD overlay */}
      <div className="relative h-[500px] lg:h-[600px] w-full bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800">
        <PlumeHUD
          emission={activeEmission}
          windSpeed={activeWindSpeed}
          windDirection={activeWindDir}
          timestamp={hasTimeline ? playback.currentFrame.timestamp : undefined}
          gas={plume.gas}
        />
        <SceneCanvas className="h-full w-full">
          <CaptureHandler onCapture={() => {}} />
          <LeakScene
            plume={plume}
            cameraPreset={cameraPreset}
            tileSource={tileSource}
            animationFrame={hasTimeline ? playback.currentFrame : undefined}
          />
        </SceneCanvas>
      </div>

      {/* Timeline */}
      {timeSeriesLoading ? (
        <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800 text-sm text-zinc-500 animate-pulse">
          Loading observations...
        </div>
      ) : hasTimeline ? (
        <TimelineControls
          keyframes={keyframes}
          currentFrame={playback.currentFrame}
          progress={playback.progress}
          isPlaying={playback.isPlaying}
          speed={playback.speed}
          onToggle={playback.toggle}
          onSetTime={playback.setTime}
          onSetSpeed={playback.setSpeed}
        />
      ) : null}

      {/* Controls bar */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex gap-1.5">
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider self-center mr-1">Camera</span>
          {(
            [
              ["orbit", "Orbit"],
              ["ground", "Ground"],
              ["overview", "Above"],
              ["flyaround", "Fly"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setCameraPreset(key)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                cameraPreset === key
                  ? "bg-zinc-700 text-white"
                  : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex gap-1.5">
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider self-center mr-1">Map</span>
          {(
            [
              ["satellite", "Satellite"],
              ["osm", "OSM"],
              ["topo", "Topo"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTileSource(key)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                tileSource === key
                  ? "bg-zinc-700 text-white"
                  : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <CaptureButton />
      </div>
    </div>
  );
}
