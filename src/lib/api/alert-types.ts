export interface Alert {
  id: number;
  facility_id: number;
  alert_type: string;
  severity: string;
  title: string;
  description: string | null;
  metadata: Record<string, unknown> | null;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  created_at: string;
}

export interface AlertListResponse {
  total_count: number;
  items: Alert[];
}

export interface AlertSummary {
  total: number;
  unacknowledged: number;
  by_severity: Array<{
    severity: string;
    acknowledged: boolean;
    count: number;
  }>;
}

export const SEVERITY_CONFIG: Record<
  string,
  { color: string; bg: string; label: string }
> = {
  critical: { color: "#ef4444", bg: "bg-red-500/20", label: "Critical" },
  high: { color: "#f59e0b", bg: "bg-amber-500/20", label: "High" },
  medium: { color: "#3b82f6", bg: "bg-blue-500/20", label: "Medium" },
  low: { color: "#22c55e", bg: "bg-green-500/20", label: "Low" },
};

export const ALERT_TYPE_LABELS: Record<string, string> = {
  threshold_exceedance: "Threshold Exceeded",
  new_detection: "New Detection",
  nger_baseline_breach: "NGER Baseline Breach",
  trend_increase: "Trend Increase",
};
