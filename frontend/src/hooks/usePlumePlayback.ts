"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { PlumeKeyframe } from "@/lib/api/plume-timeseries";

export interface InterpolatedFrame {
  emission: number;
  windSpeed: number;
  windDirection: number;
  bounds: [number, number, number, number];
  timestamp: Date;
  keyframeIndex: number;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/** Interpolate angles via shortest path (handles 350°→10° wrap). */
function lerpAngle(a: number, b: number, t: number): number {
  let delta = ((b - a + 540) % 360) - 180;
  return ((a + delta * t) + 360) % 360;
}

function lerpBounds(
  a: [number, number, number, number],
  b: [number, number, number, number],
  t: number
): [number, number, number, number] {
  return [
    lerp(a[0], b[0], t),
    lerp(a[1], b[1], t),
    lerp(a[2], b[2], t),
    lerp(a[3], b[3], t),
  ];
}

function interpolateFrame(
  keyframes: PlumeKeyframe[],
  progress: number
): InterpolatedFrame {
  if (keyframes.length === 0) {
    return {
      emission: 0,
      windSpeed: 0,
      windDirection: 0,
      bounds: [0, 0, 0, 0],
      timestamp: new Date(),
      keyframeIndex: 0,
    };
  }

  if (keyframes.length === 1) {
    const kf = keyframes[0];
    return {
      emission: kf.emission,
      windSpeed: kf.windSpeed,
      windDirection: kf.windDirection,
      bounds: kf.bounds,
      timestamp: kf.timestamp,
      keyframeIndex: 0,
    };
  }

  // Map progress [0,1] to keyframe index space
  const maxIdx = keyframes.length - 1;
  const clampedProgress = Math.max(0, Math.min(1, progress));
  const exactIdx = clampedProgress * maxIdx;
  const idxA = Math.max(0, Math.min(Math.floor(exactIdx), maxIdx - 1));
  const idxB = Math.min(idxA + 1, maxIdx);
  const t = idxA === idxB ? 0 : exactIdx - idxA;

  const a = keyframes[idxA];
  const b = keyframes[idxB];

  if (!a || !b) {
    const fallback = keyframes[0];
    return {
      emission: fallback.emission,
      windSpeed: fallback.windSpeed,
      windDirection: fallback.windDirection,
      bounds: fallback.bounds,
      timestamp: fallback.timestamp,
      keyframeIndex: 0,
    };
  }

  return {
    emission: lerp(a.emission, b.emission, t),
    windSpeed: lerp(a.windSpeed, b.windSpeed, t),
    windDirection: lerpAngle(a.windDirection, b.windDirection, t),
    bounds: lerpBounds(a.bounds, b.bounds, t),
    timestamp: new Date(lerp(a.timestamp.getTime(), b.timestamp.getTime(), t)),
    keyframeIndex: idxA,
  };
}

export function usePlumePlayback(keyframes: PlumeKeyframe[]) {
  const [progress, setProgress] = useState(0); // 0-1
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const rafRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);

  // Duration in seconds for one full playback cycle at 1x speed
  const cycleDuration = 10;

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);
  const toggle = useCallback(() => setIsPlaying((p) => !p), []);

  const setTime = useCallback((t: number) => {
    setProgress(Math.max(0, Math.min(1, t)));
  }, []);

  // Animation loop
  useEffect(() => {
    if (!isPlaying || keyframes.length < 2) return;

    lastTimeRef.current = performance.now();

    const tick = (now: number) => {
      const dt = (now - lastTimeRef.current) / 1000;
      lastTimeRef.current = now;

      setProgress((prev) => {
        const next = prev + (dt * speed) / cycleDuration;
        if (next >= 1) return 0; // loop
        return next;
      });

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [isPlaying, speed, keyframes.length, cycleDuration]);

  const currentFrame = interpolateFrame(keyframes, progress);

  return {
    currentFrame,
    progress,
    isPlaying,
    speed,
    play,
    pause,
    toggle,
    setTime,
    setSpeed,
    keyframeCount: keyframes.length,
  };
}
