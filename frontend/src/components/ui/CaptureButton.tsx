"use client";

import { useCallback } from "react";
import { useThree } from "@react-three/fiber";

/**
 * Captures the current WebGL canvas as a PNG download.
 * Must be placed inside a <Canvas> (uses useThree).
 */
export function CaptureHandler({ onCapture }: { onCapture: () => void }) {
  // Register the capture function — this component is rendered inside Canvas
  const { gl } = useThree();

  // Expose capture via a global so the button outside Canvas can trigger it
  if (typeof window !== "undefined") {
    (window as any).__captureCanvas = () => {
      gl.render(gl.domElement as any, gl.domElement as any); // force render
      const dataUrl = gl.domElement.toDataURL("image/png");
      const link = document.createElement("a");
      link.download = `plume-capture-${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
    };
  }

  return null;
}

/**
 * Button that triggers a canvas screenshot download.
 * Place outside the Canvas — it calls the handler registered inside.
 */
export default function CaptureButton() {
  const handleCapture = useCallback(() => {
    if (typeof window !== "undefined" && (window as any).__captureCanvas) {
      (window as any).__captureCanvas();
    }
  }, []);

  return (
    <button
      onClick={handleCapture}
      className="px-3 py-1.5 rounded text-xs font-medium bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800 transition-colors"
      title="Save screenshot"
    >
      Capture PNG
    </button>
  );
}
