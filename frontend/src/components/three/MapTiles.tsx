"use client";

import { useMemo } from "react";
import { useLoader } from "@react-three/fiber";
import * as THREE from "three";

/**
 * Convert lat/lon to tile XY at a given zoom level.
 */
function latLonToTile(lat: number, lon: number, zoom: number): { x: number; y: number } {
  const n = Math.pow(2, zoom);
  const x = Math.floor(((lon + 180) / 360) * n);
  const latRad = (lat * Math.PI) / 180;
  const y = Math.floor(((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n);
  return { x, y };
}

/**
 * Get the lat/lon bounds of a tile.
 */
function tileBounds(tx: number, ty: number, zoom: number) {
  const n = Math.pow(2, zoom);
  const lonLeft = (tx / n) * 360 - 180;
  const lonRight = ((tx + 1) / n) * 360 - 180;
  const latTop = (Math.atan(Math.sinh(Math.PI * (1 - (2 * ty) / n))) * 180) / Math.PI;
  const latBottom = (Math.atan(Math.sinh(Math.PI * (1 - (2 * (ty + 1)) / n))) * 180) / Math.PI;
  return { lonLeft, lonRight, latTop, latBottom };
}

export type TileSource = "satellite" | "osm" | "topo";

const TILE_URLS: Record<TileSource, (z: number, x: number, y: number) => string> = {
  satellite: (z, x, y) =>
    `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`,
  osm: (z, x, y) =>
    `https://tile.openstreetmap.org/${z}/${x}/${y}.png`,
  topo: (z, x, y) =>
    `https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/${z}/${y}/${x}`,
};

interface MapTilesProps {
  latitude: number;
  longitude: number;
  /** World units to cover (width and depth of the tile area). */
  worldSize?: number;
  /** Zoom level (default 14 — ~2.4km per tile). */
  zoom?: number;
  /** Number of tiles in each direction from center (default 2 = 5x5 grid). */
  gridRadius?: number;
  /** Tile source. */
  source?: TileSource;
}

function TilePlane({
  url,
  position,
  size,
}: {
  url: string;
  position: [number, number, number];
  size: number;
}) {
  const texture = useLoader(THREE.TextureLoader, url);

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={position}>
      <planeGeometry args={[size, size]} />
      <meshBasicMaterial map={texture} toneMapped={false} />
    </mesh>
  );
}

export default function MapTiles({
  latitude,
  longitude,
  worldSize = 4000,
  zoom = 14,
  gridRadius = 2,
  source = "satellite",
}: MapTilesProps) {
  const tiles = useMemo(() => {
    const center = latLonToTile(latitude, longitude, zoom);
    const tileCount = gridRadius * 2 + 1;

    // Calculate meters per tile at this latitude
    const centerBounds = tileBounds(center.x, center.y, zoom);
    const mPerDegLon = 111320 * Math.cos((latitude * Math.PI) / 180);
    const tileSizeMeters = (centerBounds.lonRight - centerBounds.lonLeft) * mPerDegLon;

    // Scale factor: map tile meters to world units
    const tileWorldSize = worldSize / tileCount;

    const result: { url: string; position: [number, number, number]; size: number; key: string }[] = [];

    for (let dy = -gridRadius; dy <= gridRadius; dy++) {
      for (let dx = -gridRadius; dx <= gridRadius; dx++) {
        const tx = center.x + dx;
        const ty = center.y + dy;
        const url = TILE_URLS[source](zoom, tx, ty);

        // Position in world space: dx/dy tiles from center
        // Note: tile Y increases southward, but world Z increases northward
        const worldX = dx * tileWorldSize;
        const worldZ = dy * tileWorldSize;

        result.push({
          url,
          position: [worldX, 0.05, worldZ],
          size: tileWorldSize,
          key: `${tx}-${ty}`,
        });
      }
    }

    return result;
  }, [latitude, longitude, zoom, gridRadius, worldSize, source]);

  return (
    <group>
      {tiles.map((tile) => (
        <TilePlane
          key={tile.key}
          url={tile.url}
          position={tile.position}
          size={tile.size}
        />
      ))}
    </group>
  );
}
