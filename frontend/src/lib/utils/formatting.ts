import { format, formatDistanceToNow, parseISO } from "date-fns";

export function formatEmissionRate(kgPerHour: number | null): string {
  if (kgPerHour === null) return "N/A";
  if (kgPerHour >= 1000) return `${(kgPerHour / 1000).toFixed(1)}t/hr`;
  if (kgPerHour >= 1) return `${kgPerHour.toFixed(0)} kg/hr`;
  return `${(kgPerHour * 1000).toFixed(0)} g/hr`;
}

export function formatDate(isoDate: string): string {
  return format(parseISO(isoDate), "MMM d, yyyy");
}

export function formatTimeAgo(isoDate: string): string {
  return formatDistanceToNow(parseISO(isoDate), { addSuffix: true });
}

export function formatCoordinate(
  value: number,
  type: "lat" | "lon"
): string {
  const dir =
    type === "lat" ? (value >= 0 ? "N" : "S") : value >= 0 ? "E" : "W";
  return `${Math.abs(value).toFixed(4)}${dir}`;
}

export function formatWindSpeed(ms: number): string {
  return `${ms.toFixed(1)} m/s`;
}

export function formatWindDirection(degrees: number): string {
  const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(degrees / 45) % 8;
  return `${dirs[index]} (${degrees.toFixed(0)})`;
}

/**
 * Convert methane emission rate to relatable equivalencies
 */
export function getEmissionEquivalencies(kgPerHourCH4: number) {
  const kgPerYear = kgPerHourCH4 * 8760;
  // Methane GWP-100 = 28 (IPCC AR5)
  const co2eqTonnesPerYear = (kgPerYear * 28) / 1000;
  // Average US car emits ~4.6 tonnes CO2/year
  const carsEquivalent = co2eqTonnesPerYear / 4.6;
  // Average US home emits ~7.5 tonnes CO2/year
  const homesEquivalent = co2eqTonnesPerYear / 7.5;
  // Social cost of carbon ~$51/tonne CO2 (US EPA)
  const socialCostPerYear = co2eqTonnesPerYear * 51;

  return {
    kgPerYear,
    co2eqTonnesPerYear,
    carsEquivalent: Math.round(carsEquivalent),
    homesEquivalent: Math.round(homesEquivalent),
    socialCostPerYear,
  };
}
