"use client";

import SceneCanvas from "@/components/three/SceneCanvas";
import LeakScene from "@/components/three/LeakScene";
import type { PlumeAnnotated } from "@/lib/api/types";

interface LeakViewerProps {
  plume: PlumeAnnotated;
}

export default function LeakViewer({ plume }: LeakViewerProps) {
  return (
    <div className="h-[500px] lg:h-[600px] w-full bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800">
      <SceneCanvas className="h-full w-full">
        <LeakScene plume={plume} />
      </SceneCanvas>
    </div>
  );
}
