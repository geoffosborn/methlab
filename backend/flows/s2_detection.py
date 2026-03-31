"""
Prefect flow: On-demand Sentinel-2 plume detection.

Triggered when:
    - New S2 scene available over a TROPOMI-flagged facility
    - Manual request via API
    - Scheduled weekly scan of high-intensity facilities
"""

import logging
from datetime import date, timedelta

from prefect import flow, task

logger = logging.getLogger(__name__)


@task(retries=1, retry_delay_seconds=120, log_prints=True)
def detect_facility(
    facility_id: int,
    lat: float,
    lon: float,
    name: str,
    target_date: date,
    wind_speed: float,
    wind_direction: float,
) -> list[dict]:
    """Run S2 plume detection for a single facility."""
    from sentinel2.pipeline import run_facility_detection

    return run_facility_detection(
        facility_id=facility_id,
        lat=lat,
        lon=lon,
        facility_name=name,
        target_date=target_date,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
    )


@task(log_prints=True)
def get_wind_data(lat: float, lon: float, target_date: date) -> dict | None:
    """Fetch ERA5 wind data for the detection."""
    from tropomi.wind import download_era5_wind

    wind = download_era5_wind(lat, lon, target_date, hour=12)
    if wind is None:
        return None
    return {"speed": wind.speed, "direction": wind.direction_from}


@flow(name="s2-facility-detection", log_prints=True)
def s2_facility_detection(
    facility_id: int,
    target_date: date | None = None,
):
    """Run S2 detection for a specific facility.

    Args:
        facility_id: Facility to process
        target_date: Date to search for scenes (default: today)
    """
    import psycopg
    from psycopg.rows import dict_row
    from sentinel2.config import get_settings

    settings = get_settings()

    if target_date is None:
        target_date = date.today()

    # Get facility info
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, name,
                       ST_Y(centroid::geometry) as latitude,
                       ST_X(centroid::geometry) as longitude
                FROM facilities WHERE id = %s
                """,
                [facility_id],
            )
            fac = cur.fetchone()

    if not fac:
        print(f"Facility {facility_id} not found")
        return {"error": "facility_not_found"}

    print(f"S2 detection for {fac['name']} on {target_date}")

    # Get wind data
    wind = get_wind_data(fac["latitude"], fac["longitude"], target_date)
    if wind is None:
        print("No wind data available, using default")
        wind = {"speed": 5.0, "direction": 270.0}

    # Run detection
    detections = detect_facility(
        facility_id=fac["id"],
        lat=fac["latitude"],
        lon=fac["longitude"],
        name=fac["name"],
        target_date=target_date,
        wind_speed=wind["speed"],
        wind_direction=wind["direction"],
    )

    # Check alerts for each detection
    from app.services.alert_service import check_s2_detection_alerts, create_alerts

    for det in detections:
        alerts = check_s2_detection_alerts(det)
        if alerts:
            create_alerts(alerts)
            print(f"Created {len(alerts)} alerts for detection")

    print(f"Found {len(detections)} plume detections")
    return {"facility": fac["name"], "detections": len(detections)}


@flow(name="s2-weekly-scan", log_prints=True)
def s2_weekly_scan(
    intensity_threshold: float = 40.0,
    max_facilities: int = 20,
):
    """Weekly S2 scan of high-intensity TROPOMI-flagged facilities.

    Processes the top N facilities by TROPOMI intensity score.
    """
    import psycopg
    from psycopg.rows import dict_row
    from sentinel2.config import get_settings

    settings = get_settings()
    target_date = date.today()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (t.facility_id)
                       t.facility_id, f.name,
                       ST_Y(f.centroid::geometry) as latitude,
                       ST_X(f.centroid::geometry) as longitude,
                       t.intensity_score
                FROM tropomi_observations t
                JOIN facilities f ON f.id = t.facility_id
                WHERE t.intensity_score >= %s
                  AND f.status = 'active'
                ORDER BY t.facility_id, t.period_start DESC
                """,
                [intensity_threshold],
            )
            facilities = cur.fetchall()

    # Sort by intensity and take top N
    facilities.sort(key=lambda f: f["intensity_score"] or 0, reverse=True)
    facilities = facilities[:max_facilities]

    print(f"Weekly S2 scan: {len(facilities)} facilities above intensity {intensity_threshold}")

    for fac in facilities:
        s2_facility_detection(
            facility_id=fac["facility_id"],
            target_date=target_date,
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        s2_facility_detection(facility_id=int(sys.argv[1]))
    else:
        s2_weekly_scan()
