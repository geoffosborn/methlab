"""
Seed synthetic TROPOMI observations for NGER-mapped facilities.

Converts NGER-reported emissions (tCO2e/year) into plausible TROPOMI
wind-rotated CH4 enhancement values (ppb) for dashboard visualization.

Methodology:
  1. Convert tCO2e to tCH4/year using GWP-100 = 28 (AR5)
  2. Convert to kg/hr emission rate
  3. Estimate downwind enhancement using Gaussian plume approximation
     at TROPOMI pixel scale (~5.5 x 7 km)
  4. Add realistic noise and seasonal variation

Reference: Lauvaux et al. 2022, Sadavarte et al. 2021
"""

import json
import math
import os
import random
import sys
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# GWP-100 for CH4 (AR5)
GWP_CH4 = 28

# TROPOMI background CH4 (ppb) — Southern Hemisphere / Australia
BACKGROUND_CH4 = 1870.0

# Typical wind speed range for Australian coal basins (m/s)
WIND_SPEED_RANGE = (3.0, 8.0)

# Quarterly periods for 2024-25 and 2025-26
QUARTERS = [
    ("2024-07-01", "2024-09-30", "Q1 FY2025"),
    ("2024-10-01", "2024-12-31", "Q2 FY2025"),
    ("2025-01-01", "2025-03-31", "Q3 FY2025"),
    ("2025-04-01", "2025-06-30", "Q4 FY2025"),
    ("2025-07-01", "2025-09-30", "Q1 FY2026"),
    ("2025-10-01", "2025-12-31", "Q2 FY2026"),
]


def tco2e_to_ch4_enhancement_ppb(
    tco2e_annual: float,
    wind_speed: float = 5.0,
) -> float:
    """
    Estimate TROPOMI-scale CH4 enhancement from annual tCO2e.

    Steps:
      1. tCO2e -> tCH4/yr: divide by GWP
      2. tCH4/yr -> kg/s
      3. Gaussian plume at ~5km downwind, neutral stability (D)
         sigma_y ~ 400m, sigma_z ~ 200m at 5km
      4. Convert concentration (µg/m³) to mixing ratio (ppb)

    Returns enhancement in ppb above background.
    """
    # Step 1: tCO2e to tCH4 per year
    t_ch4_year = tco2e_annual / GWP_CH4

    # Step 2: kg/s emission rate
    kg_per_sec = t_ch4_year * 1000 / (365.25 * 24 * 3600)

    # Step 3: Gaussian plume centerline concentration at 5km
    # C = Q / (pi * sigma_y * sigma_z * u)
    sigma_y = 400.0  # m, Pasquill-Gifford class D at 5km
    sigma_z = 200.0  # m
    u = wind_speed  # m/s

    # Concentration in kg/m³
    c_kg_m3 = kg_per_sec / (math.pi * sigma_y * sigma_z * u)

    # Step 4: Convert to ppb
    # CH4 molar mass = 16 g/mol, air density ~1.2 kg/m³ at surface
    # ppb = (c_kg_m3 / air_density) * (M_air / M_ch4) * 1e9
    air_density = 1.2  # kg/m³
    m_air = 29.0  # g/mol
    m_ch4 = 16.0  # g/mol
    ppb = (c_kg_m3 / air_density) * (m_air / m_ch4) * 1e9

    return ppb


def compute_intensity_score(
    central_ppb: float,
    mean_ppb: float,
    sample_count: int,
) -> float:
    """
    Compute 0-100 intensity score.

    Scoring based on:
      - central_box enhancement (60% weight)
      - mean enhancement (30% weight)
      - data quality / sample count (10% weight)
    """
    # Normalize central enhancement: 100 ppb = ~30, 500 ppb = ~60, 2000+ ppb = ~100
    central_norm = min(100, (central_ppb / 2000) * 100) * 0.6

    # Normalize mean enhancement
    mean_norm = min(100, (mean_ppb / 1000) * 100) * 0.3

    # Sample count quality: 30+ overpasses = full marks
    quality_norm = min(100, (sample_count / 30) * 100) * 0.1

    return round(min(100, central_norm + mean_norm + quality_norm), 1)


def generate_observations(facility: dict) -> list[dict]:
    """Generate quarterly TROPOMI observations for a facility."""
    tco2e = facility.get("nger_reported_2024")
    if not tco2e or tco2e <= 0:
        return []

    observations = []
    random.seed(facility["id"] * 1000)  # Reproducible per facility

    for period_start, period_end, label in QUARTERS:
        # Seasonal variation: slightly higher in winter (less ventilation)
        month = int(period_start.split("-")[1])
        seasonal_factor = 1.0
        if month in (6, 7, 8):  # Australian winter
            seasonal_factor = 1.15
        elif month in (12, 1, 2):  # Australian summer
            seasonal_factor = 0.9

        # Random variation per quarter (±20%)
        variation = random.uniform(0.8, 1.2) * seasonal_factor

        # Wind speed for this quarter
        wind_speed = random.uniform(*WIND_SPEED_RANGE)

        # Base enhancement
        base_ppb = tco2e_to_ch4_enhancement_ppb(tco2e * variation, wind_speed)

        # Central box gets ~1.5x the mean (concentrated plume)
        central_ppb = base_ppb * random.uniform(1.3, 1.7)
        mean_ppb = base_ppb * random.uniform(0.6, 0.9)
        max_ppb = central_ppb * random.uniform(1.5, 2.5)

        # Sample count: ~20-40 overpasses per quarter for Australia
        sample_count = random.randint(18, 42)
        valid_fraction = random.uniform(0.55, 0.85)

        intensity = compute_intensity_score(central_ppb, mean_ppb, sample_count)

        observations.append({
            "facility_id": facility["id"],
            "period_start": period_start,
            "period_end": period_end,
            "aggregation_period": "quarterly",
            "mean_enhancement_ppb": round(mean_ppb, 2),
            "max_enhancement_ppb": round(max_ppb, 2),
            "central_box_mean_ppb": round(central_ppb, 2),
            "sample_count": sample_count,
            "valid_pixel_fraction": round(valid_fraction, 3),
            "mean_wind_speed": round(wind_speed, 1),
            "intensity_score": intensity,
            "background_ch4_ppb": round(BACKGROUND_CH4 + random.uniform(-5, 5), 1),
        })

    return observations


def main():
    env_path = Path(__file__).parent.parent / "apps" / "api" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "methlab")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")

    with psycopg.connect(
        host=db_host, port=int(db_port), dbname=db_name,
        user=db_user, password=db_password,
    ) as conn:
        # Get facilities with NGER data
        cur = conn.execute("""
            SELECT id, name, state, metadata
            FROM facilities
            WHERE nger_id IS NOT NULL
            ORDER BY (metadata->>'nger_reported_2024')::int DESC
        """)
        facilities = []
        for row in cur.fetchall():
            fac = {
                "id": row[0],
                "name": row[1],
                "state": row[2],
                "nger_reported_2024": json.loads(row[3] if isinstance(row[3], str) else json.dumps(row[3])).get("nger_reported_2024"),
            }
            facilities.append(fac)

        print(f"Found {len(facilities)} facilities with NGER data")

        total_inserted = 0
        for fac in facilities:
            obs_list = generate_observations(fac)
            for obs in obs_list:
                try:
                    conn.execute("""
                        INSERT INTO tropomi_observations (
                            facility_id, period_start, period_end, aggregation_period,
                            mean_enhancement_ppb, max_enhancement_ppb, central_box_mean_ppb,
                            sample_count, valid_pixel_fraction, mean_wind_speed,
                            intensity_score, background_ch4_ppb
                        ) VALUES (
                            %(facility_id)s, %(period_start)s, %(period_end)s, %(aggregation_period)s,
                            %(mean_enhancement_ppb)s, %(max_enhancement_ppb)s, %(central_box_mean_ppb)s,
                            %(sample_count)s, %(valid_pixel_fraction)s, %(mean_wind_speed)s,
                            %(intensity_score)s, %(background_ch4_ppb)s
                        )
                        ON CONFLICT (facility_id, period_start, period_end, aggregation_period) DO NOTHING
                    """, obs)
                    total_inserted += 1
                except Exception as e:
                    print(f"  ERROR {fac['name']}: {e}")

            top_score = max((o["intensity_score"] for o in obs_list), default=0)
            top_ppb = max((o["central_box_mean_ppb"] for o in obs_list), default=0)
            print(f"  {fac['name']:30s} {fac['state']:5s}  {fac.get('nger_reported_2024', 0):>10,} tCO2e  "
                  f"peak={top_ppb:6.1f} ppb  score={top_score:5.1f}")

        conn.commit()
        print(f"\nDone. {total_inserted} observations inserted for {len(facilities)} facilities.")


if __name__ == "__main__":
    main()
