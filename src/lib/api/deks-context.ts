/**
 * Extract DEKS project context from proxy headers.
 *
 * When methlab runs as a module inside the DEKS container, the reverse proxy
 * injects X-DEKS-* headers with user identity and project context. This module
 * reads those headers in server components / API routes.
 */
import { headers } from "next/headers";

export interface DeksProjectContext {
  projectId: string;
  projectSlug: string;
  projectName: string;
  bounds: GeoJSONGeometry | null;
}

export interface GeoJSONGeometry {
  type: string;
  coordinates: number[] | number[][] | number[][][] | number[][][][];
}

/**
 * Extract project context from X-DEKS-* proxy headers.
 * Returns null when running standalone (no container proxy).
 */
export async function getDeksProjectContext(): Promise<DeksProjectContext | null> {
  const h = await headers();
  const projectId = h.get("x-deks-project-id");
  if (!projectId) return null;

  let bounds: GeoJSONGeometry | null = null;
  const boundsRaw = h.get("x-deks-project-bounds");
  if (boundsRaw) {
    try {
      bounds = JSON.parse(boundsRaw) as GeoJSONGeometry;
    } catch {
      // Malformed bounds header — skip
    }
  }

  return {
    projectId,
    projectSlug: h.get("x-deks-project-slug") ?? "",
    projectName: h.get("x-deks-project-name") ?? "",
    bounds,
  };
}

/**
 * Extract a [west, south, east, north] bounding box from a GeoJSON geometry.
 * Works with Polygon, MultiPolygon, and Point geometries.
 */
export function geojsonToBbox(
  geom: GeoJSONGeometry
): [number, number, number, number] | null {
  const coords = flattenCoordinates(geom);
  if (coords.length === 0) return null;

  let west = Infinity,
    south = Infinity,
    east = -Infinity,
    north = -Infinity;

  for (const [lon, lat] of coords) {
    if (lon < west) west = lon;
    if (lon > east) east = lon;
    if (lat < south) south = lat;
    if (lat > north) north = lat;
  }

  return [west, south, east, north];
}

function flattenCoordinates(geom: GeoJSONGeometry): [number, number][] {
  const { type, coordinates } = geom;

  if (type === "Point") {
    const [lon, lat] = coordinates as number[];
    return [[lon, lat]];
  }

  if (type === "Polygon") {
    return (coordinates as number[][][]).flat() as [number, number][];
  }

  if (type === "MultiPolygon") {
    return (coordinates as number[][][][]).flat(2) as [number, number][];
  }

  // LineString, MultiLineString, etc.
  try {
    const flat = (coordinates as number[][]).flat();
    const pairs: [number, number][] = [];
    for (let i = 0; i < flat.length - 1; i += 2) {
      pairs.push([flat[i], flat[i + 1]]);
    }
    return pairs;
  } catch {
    return [];
  }
}
