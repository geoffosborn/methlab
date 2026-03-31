export interface Facility {
  id: number;
  name: string;
  facility_type: string;
  state: string | null;
  operator: string | null;
  latitude: number;
  longitude: number;
  nger_id: string | null;
  status: string;
  commodity: string | null;
  metadata: Record<string, unknown> | null;
}

export interface FacilityListResponse {
  total_count: number;
  items: Facility[];
}

export interface FacilityQueryParams {
  facility_type?: string;
  state?: string;
  status?: string;
  limit?: number;
  offset?: number;
  bbox?: string;
}

export const STATE_LABELS: Record<string, string> = {
  QLD: "Queensland",
  NSW: "New South Wales",
  VIC: "Victoria",
  WA: "Western Australia",
  SA: "South Australia",
  TAS: "Tasmania",
  NT: "Northern Territory",
  ACT: "Australian Capital Territory",
};

export const FACILITY_STATUS_COLORS: Record<string, string> = {
  active: "#22c55e",
  closed: "#ef4444",
  care_and_maintenance: "#f59e0b",
};

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    active: "Active",
    closed: "Closed",
    care_and_maintenance: "Care & Maintenance",
  };
  return labels[status] ?? status;
}
