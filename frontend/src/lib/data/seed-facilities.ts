import type { Facility } from "@/lib/api/facility-types";

/**
 * Hardcoded Bowen Basin coal mines for homepage display.
 * Replace with getFacilities() API call when methlab-api is deployed.
 */
export const SEED_FACILITIES: Facility[] = [
  {
    id: 1,
    name: "Moranbah North",
    facility_type: "underground_coal",
    state: "QLD",
    operator: "Anglo American",
    latitude: -21.7,
    longitude: 148.1,
    nger_id: "QLD-UG-001",
    status: "active",
    commodity: "Metallurgical Coal",
    metadata: null,
  },
  {
    id: 2,
    name: "Grasstree",
    facility_type: "underground_coal",
    state: "QLD",
    operator: "Anglo American",
    latitude: -21.85,
    longitude: 148.15,
    nger_id: "QLD-UG-002",
    status: "active",
    commodity: "Metallurgical Coal",
    metadata: null,
  },
  {
    id: 3,
    name: "Broadmeadow",
    facility_type: "underground_coal",
    state: "QLD",
    operator: "BHP",
    latitude: -21.75,
    longitude: 148.05,
    nger_id: "QLD-UG-003",
    status: "active",
    commodity: "Metallurgical Coal",
    metadata: null,
  },
  {
    id: 4,
    name: "Goonyella Riverside",
    facility_type: "open_cut_coal",
    state: "QLD",
    operator: "BHP",
    latitude: -21.82,
    longitude: 148.0,
    nger_id: "QLD-OC-001",
    status: "active",
    commodity: "Metallurgical Coal",
    metadata: null,
  },
];

/** Primary featured facility for homepage card */
export const FEATURED_FACILITY = SEED_FACILITIES[0];

/** Center coordinates for Bowen Basin region */
export const BOWEN_BASIN_CENTER: [number, number] = [-21.75, 148.08];
