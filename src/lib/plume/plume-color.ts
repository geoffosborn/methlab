/**
 * Color definitions for gas types in the plume visualization.
 */

export const GAS_COLORS = {
  CH4: {
    primary: "#FF6B35",
    light: "#FF9A6C",
    dark: "#CC4400",
    rgb: [1.0, 0.42, 0.21] as [number, number, number],
    label: "Methane",
  },
  CO2: {
    primary: "#4A90D9",
    light: "#7AB3E8",
    dark: "#2A5FA0",
    rgb: [0.29, 0.56, 0.85] as [number, number, number],
    label: "Carbon Dioxide",
  },
} as const;

export type GasType = keyof typeof GAS_COLORS;

export function getGasColor(gas: GasType) {
  return GAS_COLORS[gas];
}

/**
 * Returns a severity color based on emission rate.
 * Used for UI indicators like cards and badges.
 */
export function getEmissionSeverityColor(emissionKgHr: number | null): string {
  if (emissionKgHr === null) return "#666";
  if (emissionKgHr >= 500) return "#FF1744"; // Critical - red
  if (emissionKgHr >= 100) return "#FF6B35"; // High - orange
  if (emissionKgHr >= 25) return "#FFD600"; // Medium - yellow
  return "#66BB6A"; // Low - green
}

export function getEmissionSeverityLabel(
  emissionKgHr: number | null
): string {
  if (emissionKgHr === null) return "Unknown";
  if (emissionKgHr >= 500) return "Critical";
  if (emissionKgHr >= 100) return "High";
  if (emissionKgHr >= 25) return "Medium";
  return "Low";
}
