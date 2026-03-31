"""
Seed synthetic Sentinel-2 plume detections for Bowen Basin underground mines.

Generates realistic S2 detection records using the Varon (2021) IME method
parameters. Based on NGER-reported emissions, mine gas content, and typical
Bowen Basin meteorological conditions.

Key assumptions:
  - S2 overpass every ~5 days, ~30% cloud rejection -> ~4-5 usable scenes/month
  - Detection probability ~40% for large mines (not every scene has a visible plume)
  - Emission rate derived from NGER annual totals with temporal variation
  - IME = Q * L / Ueff, inverted for plume quantification
  - Uncertainty ~50% (relative) per Varon 2021

References:
  - Varon et al. 2021: Quantifying Time-Averaged Methane Emissions
  - Sadavarte et al. 2021: TROPOMI Bowen Basin (190/150 Gg/yr for S2/S3 clusters)
"""

import math
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

GWP_CH4 = 28

# Underground Bowen Basin mine emission profiles
# Back-calculated from Sadavarte 2021 TROPOMI clusters and NGER data
MINE_PROFILES = {
    "Moranbah North": {
        "nger_tco2e": 1_300_000,
        "vam_fraction": 0.60,  # fraction of total emissions via VAM
        "drainage_fraction": 0.30,
        "fugitive_fraction": 0.10,  # detectable by S2
        "detection_probability": 0.35,
    },
    "Grosvenor": {
        "nger_tco2e": 1_700_000,
        "vam_fraction": 0.55,
        "drainage_fraction": 0.35,
        "fugitive_fraction": 0.10,
        "detection_probability": 0.40,
    },
    "Grasstree": {
        "nger_tco2e": 1_800_000,
        "vam_fraction": 0.50,
        "drainage_fraction": 0.25,
        "fugitive_fraction": 0.25,  # higher — known super-emitter
        "detection_probability": 0.50,
    },
    "Broadmeadow": {
        "nger_tco2e": 800_000,
        "vam_fraction": 0.60,
        "drainage_fraction": 0.30,
        "fugitive_fraction": 0.10,
        "detection_probability": 0.30,
    },
    "North Goonyella": {
        "nger_tco2e": 600_000,
        "vam_fraction": 0.65,
        "drainage_fraction": 0.20,
        "fugitive_fraction": 0.15,
        "detection_probability": 0.35,
    },
    "Oaky North": {
        "nger_tco2e": 1_200_000,
        "vam_fraction": 0.55,
        "drainage_fraction": 0.30,
        "fugitive_fraction": 0.15,
        "detection_probability": 0.45,
    },
}


def generate_s2_detections(facility: dict, profile: dict) -> list[dict]:
    """Generate synthetic S2 detections for a facility over 2 years."""
    fid = facility["id"]
    lat = facility["latitude"]
    lon = facility["longitude"]
    random.seed(fid * 7919)  # Reproducible per facility

    # Base fugitive emission rate (kg/hr)
    t_ch4_yr = profile["nger_tco2e"] / GWP_CH4
    kg_hr_total = t_ch4_yr * 1000 / 8766  # hours per year
    base_fugitive_kg_hr = kg_hr_total * profile["fugitive_fraction"]

    detections = []
    # Generate scenes from 2023-01 to 2025-12
    start = date(2023, 1, 1)
    end = date(2025, 12, 31)
    current = start

    scene_num = 0
    while current <= end:
        # S2 revisit ~5 days
        current += timedelta(days=random.randint(4, 6))
        if current > end:
            break

        # Cloud rejection (~30%)
        cloud_cover = random.uniform(0, 1)
        if cloud_cover > 0.30:
            # Cloudy scene — skip (but some partial scenes still get through)
            if cloud_cover > 0.50:
                continue

        # Detection probability
        if random.random() > profile["detection_probability"]:
            continue

        scene_num += 1

        # Seasonal variation (winter = more gas, summer = more convective mixing)
        month = current.month
        if month in (6, 7, 8):
            seasonal = random.uniform(1.1, 1.3)
        elif month in (12, 1, 2):
            seasonal = random.uniform(0.7, 0.95)
        else:
            seasonal = random.uniform(0.85, 1.15)

        # Random day-to-day variation (±40%)
        emission_rate = base_fugitive_kg_hr * seasonal * random.uniform(0.6, 1.4)

        # Wind conditions (ERA5 10m)
        wind_speed_10m = random.uniform(2.5, 9.0)
        wind_direction = random.uniform(0, 360)
        effective_wind = 0.33 * wind_speed_10m + 0.45

        # Plume geometry
        # Plume length scales with emission rate and wind
        plume_length = emission_rate * effective_wind * random.uniform(0.8, 1.5)
        plume_length = max(200, min(5000, plume_length))

        # IME = Q * L / Ueff
        ime_kg = emission_rate * plume_length / (effective_wind * 3600)
        # Add noise
        ime_kg *= random.uniform(0.7, 1.3)

        plume_area = plume_length * random.uniform(80, 200)  # m^2
        plume_pixels = max(40, int(plume_area / 100))  # 10m pixels

        # Enhancement values (SWIR)
        mean_enhancement = random.uniform(0.003, 0.015) * (emission_rate / 100)
        max_enhancement = mean_enhancement * random.uniform(1.5, 3.0)

        # Solar/view geometry (typical for Bowen Basin, ~22S)
        solar_zenith = random.uniform(20, 55)
        view_zenith = random.uniform(0, 12)

        # Confidence based on plume pixels and enhancement
        if plume_pixels > 100 and mean_enhancement > 0.01:
            confidence = "high"
        elif plume_pixels > 60 or mean_enhancement > 0.005:
            confidence = "medium"
        else:
            confidence = "low"

        # Uncertainty (~50% relative, per Varon 2021)
        uncertainty = emission_rate * random.uniform(0.4, 0.6)

        # Scene time (S2 overpass ~10:30 local = ~00:30 UTC for AEST)
        scene_dt = datetime(
            current.year, current.month, current.day,
            0, 30 + random.randint(0, 15), random.randint(0, 59),
        )

        # Plume centroid (offset from facility by wind direction)
        offset_km = plume_length / 2000
        plume_lat = lat + offset_km / 111 * math.cos(math.radians(wind_direction))
        plume_lon = lon + offset_km / (111 * math.cos(math.radians(lat))) * math.sin(math.radians(wind_direction))

        scene_id = f"S2B_MSIL2A_{current.strftime('%Y%m%d')}T{scene_dt.strftime('%H%M%S')}_N0510_R{random.randint(1,143):03d}_T55K{chr(random.randint(65,77))}{chr(random.randint(65,86))}"

        detections.append({
            "facility_id": fid,
            "scene_id": scene_id,
            "scene_datetime": scene_dt.isoformat() + "+00:00",
            "emission_rate_kg_hr": round(emission_rate, 1),
            "uncertainty_kg_hr": round(uncertainty, 1),
            "ime_kg": round(ime_kg, 2),
            "effective_wind_m_s": round(effective_wind, 2),
            "plume_length_m": round(plume_length, 1),
            "plume_area_m2": round(plume_area, 1),
            "plume_pixels": plume_pixels,
            "mean_enhancement": round(mean_enhancement, 6),
            "max_enhancement": round(max_enhancement, 6),
            "wind_speed_10m": round(wind_speed_10m, 1),
            "wind_direction": round(wind_direction, 1),
            "solar_zenith": round(solar_zenith, 1),
            "view_zenith": round(view_zenith, 1),
            "cloud_cover": round(cloud_cover, 3),
            "confidence": confidence,
        })

    return detections


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
    db_pass = os.getenv("DB_PASSWORD", "")

    conn_str = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_pass}"

    with psycopg.connect(conn_str, row_factory=dict_row) as conn:
        # Fetch facilities
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name,
                       ST_Y(centroid::geometry) AS latitude,
                       ST_X(centroid::geometry) AS longitude
                FROM facilities
                WHERE status = 'active'
            """)
            facilities = {row["name"]: row for row in cur.fetchall()}

        total = 0
        for mine_name, profile in MINE_PROFILES.items():
            fac = facilities.get(mine_name)
            if not fac:
                print(f"  SKIP {mine_name}: not in DB")
                continue

            detections = generate_s2_detections(fac, profile)
            if not detections:
                print(f"  SKIP {mine_name}: no detections generated")
                continue

            with conn.cursor() as cur:
                for det in detections:
                    cur.execute("""
                        INSERT INTO s2_detections
                            (facility_id, scene_id, scene_datetime,
                             emission_rate_kg_hr, uncertainty_kg_hr, ime_kg,
                             effective_wind_m_s, plume_length_m, plume_area_m2,
                             plume_pixels, mean_enhancement, max_enhancement,
                             wind_speed_10m, wind_direction, solar_zenith,
                             view_zenith, cloud_cover, confidence)
                        VALUES
                            (%(facility_id)s, %(scene_id)s, %(scene_datetime)s,
                             %(emission_rate_kg_hr)s, %(uncertainty_kg_hr)s, %(ime_kg)s,
                             %(effective_wind_m_s)s, %(plume_length_m)s, %(plume_area_m2)s,
                             %(plume_pixels)s, %(mean_enhancement)s, %(max_enhancement)s,
                             %(wind_speed_10m)s, %(wind_direction)s, %(solar_zenith)s,
                             %(view_zenith)s, %(cloud_cover)s, %(confidence)s)
                        ON CONFLICT DO NOTHING
                    """, det)

            conn.commit()
            total += len(detections)
            print(f"  {mine_name}: {len(detections)} detections (avg {sum(d['emission_rate_kg_hr'] for d in detections)/len(detections):.0f} kg/hr)")

        print(f"\nTotal: {total} S2 detections seeded across {len(MINE_PROFILES)} mines")


if __name__ == "__main__":
    main()
