"use client";

import { useRef, useMemo, useEffect } from "react";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { PlumeAnnotated } from "@/lib/api/types";
import { getPlumeCoordinates } from "@/lib/api/types";
import { gasToColor } from "@/lib/plume/plume-physics";
import type { Facility } from "@/lib/api/facility-types";
import { FACILITY_STATUS_COLORS } from "@/lib/api/facility-types";

interface GlobeViewProps {
  plumes: PlumeAnnotated[];
  facilities?: Facility[];
  autoRotate?: boolean;
}

const EARTH_RADIUS = 100;

function latLonToXYZ(
  lat: number,
  lon: number,
  radius: number
): [number, number, number] {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lon + 180) * (Math.PI / 180);
  return [
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  ];
}

/**
 * Interactive 3D globe showing plume locations as glowing markers.
 */
export default function GlobeView({
  plumes,
  facilities = [],
  autoRotate = true,
}: GlobeViewProps) {
  const markersRef = useRef<THREE.InstancedMesh>(null);
  const facilityMarkersRef = useRef<THREE.InstancedMesh>(null);

  // Create instanced markers for plume locations
  const { positions, colors, scales } = useMemo(() => {
    const pos: [number, number, number][] = [];
    const col: [number, number, number][] = [];
    const scl: number[] = [];

    for (const plume of plumes) {
      const { latitude, longitude } = getPlumeCoordinates(plume);
      pos.push(latLonToXYZ(latitude, longitude, EARTH_RADIUS + 0.5));
      const color = gasToColor(plume.gas);
      col.push([color.r, color.g, color.b]);
      // Scale by emission rate
      const emission = plume.emission_auto ?? 10;
      scl.push(0.3 + Math.log10(Math.max(emission, 1)) * 0.4);
    }

    return { positions: pos, colors: col, scales: scl };
  }, [plumes]);

  // Update instanced mesh matrices
  useEffect(() => {
    if (!markersRef.current) return;
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();

    for (let i = 0; i < positions.length; i++) {
      dummy.position.set(...positions[i]);
      dummy.scale.setScalar(scales[i]);
      dummy.lookAt(0, 0, 0);
      dummy.updateMatrix();
      markersRef.current.setMatrixAt(i, dummy.matrix);
      color.setRGB(...colors[i]);
      markersRef.current.setColorAt(i, color);
    }
    markersRef.current.instanceMatrix.needsUpdate = true;
    if (markersRef.current.instanceColor)
      markersRef.current.instanceColor.needsUpdate = true;
  }, [positions, colors, scales]);

  // Facility marker data
  const facilityMarkers = useMemo(() => {
    const pos: [number, number, number][] = [];
    const col: [number, number, number][] = [];

    for (const facility of facilities) {
      pos.push(latLonToXYZ(facility.latitude, facility.longitude, EARTH_RADIUS + 0.5));
      const statusColor = FACILITY_STATUS_COLORS[facility.status] ?? "#666666";
      const c = new THREE.Color(statusColor);
      col.push([c.r, c.g, c.b]);
    }

    return { positions: pos, colors: col };
  }, [facilities]);

  // Update facility instanced mesh
  useEffect(() => {
    if (!facilityMarkersRef.current || facilityMarkers.positions.length === 0) return;
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();

    for (let i = 0; i < facilityMarkers.positions.length; i++) {
      dummy.position.set(...facilityMarkers.positions[i]);
      dummy.scale.setScalar(0.6);
      dummy.lookAt(0, 0, 0);
      dummy.updateMatrix();
      facilityMarkersRef.current.setMatrixAt(i, dummy.matrix);
      color.setRGB(...facilityMarkers.colors[i]);
      facilityMarkersRef.current.setColorAt(i, color);
    }
    facilityMarkersRef.current.instanceMatrix.needsUpdate = true;
    if (facilityMarkersRef.current.instanceColor)
      facilityMarkersRef.current.instanceColor.needsUpdate = true;
  }, [facilityMarkers]);

  return (
    <>
      <OrbitControls
        enableZoom
        enablePan={false}
        minDistance={120}
        maxDistance={400}
        autoRotate={autoRotate}
        autoRotateSpeed={0.3}
      />

      <ambientLight intensity={0.4} />
      <directionalLight position={[100, 100, 50]} intensity={1.2} />
      <directionalLight position={[-50, -50, 100]} intensity={0.3} />

      {/* Earth sphere */}
      <group>
        <mesh>
          <sphereGeometry args={[EARTH_RADIUS, 64, 64]} />
          <meshStandardMaterial
            color="#1a2332"
            roughness={0.8}
            metalness={0.1}
            emissive="#0a1420"
            emissiveIntensity={0.1}
          />
        </mesh>

        {/* Wireframe overlay for continents effect */}
        <mesh>
          <sphereGeometry args={[EARTH_RADIUS + 0.2, 32, 32]} />
          <meshBasicMaterial
            color="#2a4a5a"
            wireframe
            transparent
            opacity={0.15}
          />
        </mesh>

        {/* Plume markers */}
        {positions.length > 0 && (
          <instancedMesh
            ref={markersRef}
            args={[undefined, undefined, positions.length]}
          >
            <sphereGeometry args={[1, 8, 8]} />
            <meshStandardMaterial
              emissive="#ff6b35"
              emissiveIntensity={2}
              toneMapped={false}
            />
          </instancedMesh>
        )}

        {/* Facility markers */}
        {facilityMarkers.positions.length > 0 && (
          <instancedMesh
            ref={facilityMarkersRef}
            args={[undefined, undefined, facilityMarkers.positions.length]}
          >
            <octahedronGeometry args={[1, 0]} />
            <meshStandardMaterial
              emissive="#22c55e"
              emissiveIntensity={1.5}
              toneMapped={false}
            />
          </instancedMesh>
        )}
      </group>
    </>
  );
}
