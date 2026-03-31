"use client";

import { useState, useMemo, useEffect } from "react";
import SceneCanvas from "@/components/three/SceneCanvas";
import LeakScene, { type CameraPreset } from "@/components/three/LeakScene";
import type { TileSource } from "@/components/three/MapTiles";
import type { PlumeAnnotated } from "@/lib/api/types";
import { fetchPlumeTimeSeries, type PlumeKeyframe } from "@/lib/api/plume-timeseries";
import { usePlumePlayback } from "@/hooks/usePlumePlayback";
import TimelineControls from "@/components/ui/TimelineControls";
import PlumeHUD from "@/components/ui/PlumeHUD";
import CaptureButton, { CaptureHandler } from "@/components/ui/CaptureButton";

interface DemoLocation {
  name: string;
  coords: [number, number]; // [lon, lat]
  bounds: [number, number, number, number];
  sector: string;
  gas: "CH4" | "CO2";
}

const DEMO_LOCATIONS: DemoLocation[] = [
  {
    name: "Lithgow NSW (Coal)",
    coords: [149.13, -31.95],
    bounds: [149.12, -31.96, 149.14, -31.94],
    sector: "1B1a",
    gas: "CH4",
  },
  {
    name: "Permian Basin TX (Oil & Gas)",
    coords: [-103.5, 31.9],
    bounds: [-103.52, 31.88, -103.48, 31.92],
    sector: "1B2",
    gas: "CH4",
  },
  {
    name: "Bowen Basin QLD (Coal)",
    coords: [148.15, -22.08],
    bounds: [148.13, -22.10, 148.17, -22.06],
    sector: "1B1a",
    gas: "CH4",
  },
  {
    name: "Hassi Messaoud Algeria (Oil)",
    coords: [6.07, 31.68],
    bounds: [6.05, 31.66, 6.09, 31.70],
    sector: "1B2",
    gas: "CH4",
  },
];

const DEMO_TIMESTAMP = new Date().toISOString();

export default function PlumeDemoPage() {
  const [locationIdx, setLocationIdx] = useState(0);
  const [emission, setEmission] = useState(120);
  const [windSpeed, setWindSpeed] = useState(4);
  const [windDirection, setWindDirection] = useState(225);
  const [gas, setGas] = useState<"CH4" | "CO2">("CH4");
  const [cameraPreset, setCameraPreset] = useState<CameraPreset>("orbit");
  const [tileSource, setTileSource] = useState<TileSource>("satellite");

  const location = DEMO_LOCATIONS[locationIdx];

  // Time-series playback
  const [keyframes, setKeyframes] = useState<PlumeKeyframe[]>([]);
  const [timeSeriesLoading, setTimeSeriesLoading] = useState(true);

  useEffect(() => {
    setTimeSeriesLoading(true);
    setKeyframes([]);
    fetchPlumeTimeSeries(location.coords[1], location.coords[0], gas)
      .then((kfs) => setKeyframes(kfs))
      .catch(() => setKeyframes([]))
      .finally(() => setTimeSeriesLoading(false));
  }, [gas, location.coords]);

  const playback = usePlumePlayback(keyframes);
  const hasTimeline = keyframes.length >= 2;

  // When playing back, use interpolated values; otherwise use manual sliders
  const activeEmission = hasTimeline ? playback.currentFrame.emission : emission;
  const activeWindSpeed = hasTimeline ? playback.currentFrame.windSpeed : windSpeed;
  const activeWindDir = hasTimeline ? playback.currentFrame.windDirection : windDirection;
  const activeBounds = hasTimeline ? playback.currentFrame.bounds : location.bounds;

  const plume = useMemo<PlumeAnnotated>(
    () => ({
      id: "demo-plume",
      plume_id: "demo-plume",
      gas,
      geometry_json: { type: "Point", coordinates: location.coords, bbox: null },
      scene_id: "demo-scene",
      scene_timestamp: DEMO_TIMESTAMP,
      instrument: "Demo",
      mission_phase: "demo",
      platform: "demo",
      emission_auto: activeEmission,
      emission_uncertainty_auto: activeEmission * 0.15,
      emission_cmf_type: "ime",
      gsd: 30,
      sensitivity_mode: "standard",
      off_nadir: 0,
      plume_png: "",
      plume_rgb_png: "",
      plume_tif: "",
      con_tif: "",
      rgb_png: "",
      plume_bounds: activeBounds,
      plume_quality: "good",
      wind_speed_avg_auto: activeWindSpeed,
      wind_direction_avg_auto: activeWindDir,
      sector: location.sector,
      published_at: DEMO_TIMESTAMP,
      modified: DEMO_TIMESTAMP,
    }),
    [activeEmission, activeWindSpeed, activeWindDir, activeBounds, gas, location]
  );

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Methane Plume Visualisation
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Satellite-detected emissions rendered as 3D smoke plumes over real
            terrain. Select a location, then play the timeline to see how
            emissions change across observations.
          </p>
        </div>

        {/* Location picker */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-zinc-500 uppercase tracking-wider self-center mr-1">Location</span>
          {DEMO_LOCATIONS.map((loc, i) => (
            <button
              key={loc.name}
              onClick={() => setLocationIdx(i)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                locationIdx === i
                  ? "bg-orange-600 text-white"
                  : "bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800"
              }`}
            >
              {loc.name}
            </button>
          ))}
        </div>

        {/* 3D Viewer with HUD */}
        <div className="relative h-[500px] lg:h-[650px] w-full bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800">
          <PlumeHUD
            emission={activeEmission}
            windSpeed={activeWindSpeed}
            windDirection={activeWindDir}
            timestamp={hasTimeline ? playback.currentFrame.timestamp : undefined}
            gas={gas}
          />
          <SceneCanvas
            className="h-full w-full"
            camera={{
              position: [2000, 800, 2000],
              near: 1,
              far: 4e5,
              fov: 50,
            }}
          >
            <CaptureHandler onCapture={() => {}} />
            <LeakScene
              plume={plume}
              cameraPreset={cameraPreset}
              tileSource={tileSource}
              animationFrame={hasTimeline ? playback.currentFrame : undefined}
            />
          </SceneCanvas>
        </div>

        {/* Timeline playback */}
        {timeSeriesLoading ? (
          <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800 text-sm text-zinc-500 animate-pulse">
            Loading observations from Carbon Mapper...
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
        ) : keyframes.length === 0 && !timeSeriesLoading ? (
          <div className="bg-zinc-900 rounded-lg p-3 border border-zinc-800 text-xs text-zinc-500">
            No satellite observations found for this location. Using manual controls below.
          </div>
        ) : null}

        {/* Camera presets + map source + capture */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex gap-1.5">
            <span className="text-xs text-zinc-500 uppercase tracking-wider self-center mr-1">Camera</span>
            {(
              [
                ["orbit", "Orbit"],
                ["ground", "Ground Level"],
                ["overview", "Overview"],
                ["flyaround", "Fly Around"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setCameraPreset(key)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
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
            <span className="text-xs text-zinc-500 uppercase tracking-wider self-center mr-1">Map</span>
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
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
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

        {/* Manual controls — only shown when no timeline data */}
        {!hasTimeline && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <ControlSlider
                label="Emission Rate"
                unit="kg/hr"
                value={emission}
                min={1}
                max={1000}
                step={1}
                onChange={setEmission}
              />
              <ControlSlider
                label="Wind Speed"
                unit="m/s"
                value={windSpeed}
                min={0.5}
                max={15}
                step={0.5}
                onChange={setWindSpeed}
              />
              <ControlSlider
                label="Wind Direction"
                unit="°"
                value={windDirection}
                min={0}
                max={360}
                step={5}
                onChange={setWindDirection}
              />
              <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                <label className="block text-xs text-zinc-500 uppercase tracking-wider mb-2">
                  Gas Type
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setGas("CH4")}
                    className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
                      gas === "CH4"
                        ? "bg-orange-600 text-white"
                        : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    CH₄ Methane
                  </button>
                  <button
                    onClick={() => setGas("CO2")}
                    className={`flex-1 px-3 py-2 rounded text-sm font-medium transition-colors ${
                      gas === "CO2"
                        ? "bg-blue-600 text-white"
                        : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    CO₂
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Info */}
        <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 text-xs text-zinc-500 space-y-1">
          <p>
            <strong className="text-zinc-400">Data:</strong> Real satellite
            observations from Carbon Mapper. Emission rates, wind conditions,
            and plume extents from the annotated plume catalog.
          </p>
          <p>
            <strong className="text-zinc-400">Rendering:</strong> Particle-based
            smoke (react-smoke) driven by observation data. Particle density,
            cloud size, opacity, and wind drift scale with measured emission
            rates and wind vectors.
          </p>
          <p>
            <strong className="text-zinc-400">Controls:</strong> Orbit
            (left-drag), zoom (scroll), pan (right-drag).
          </p>
        </div>
      </div>
    </div>
  );
}

function ControlSlider({
  label,
  unit,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  unit: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
      <label className="block text-xs text-zinc-500 uppercase tracking-wider mb-1">
        {label}
      </label>
      <div className="text-lg font-mono font-bold text-zinc-100 mb-2">
        {value}
        <span className="text-xs text-zinc-500 ml-1">{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-orange-500"
      />
    </div>
  );
}
