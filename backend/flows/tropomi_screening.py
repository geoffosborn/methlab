"""
Prefect flow: Monthly TROPOMI CH4 screening for all facilities.

Schedule: 5th of each month (allows TROPOMI data latency)
Runtime: ~10 min/facility, ~18 hours for 110 facilities
"""

import logging
from datetime import date, timedelta

from prefect import flow, task
from prefect.concurrency.sync import rate_limit

logger = logging.getLogger(__name__)


@task(retries=2, retry_delay_seconds=60, log_prints=True)
def screen_facility(
    facility_id: int,
    lat: float,
    lon: float,
    name: str,
    start_date: date,
    end_date: date,
) -> dict | None:
    """Run TROPOMI screening for a single facility."""
    from tropomi.pipeline import AggregationPeriod, run_facility_analysis

    rate_limit("tropomi-api", occupy=1)  # Rate limit API calls

    return run_facility_analysis(
        facility_id=facility_id,
        lat=lat,
        lon=lon,
        facility_name=name,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.MONTHLY,
    )


@flow(name="tropomi-monthly-screening", log_prints=True)
def tropomi_monthly_screening(
    year: int | None = None,
    month: int | None = None,
    facility_ids: list[int] | None = None,
):
    """Screen all (or selected) facilities with TROPOMI for a given month.

    Args:
        year: Year to process (default: previous month)
        month: Month to process (default: previous month)
        facility_ids: Specific facilities to process (default: all active)
    """
    import psycopg
    from psycopg.rows import dict_row
    from tropomi.config import get_settings

    settings = get_settings()

    # Default to previous month
    if year is None or month is None:
        today = date.today()
        prev = today.replace(day=1) - timedelta(days=1)
        year = prev.year
        month = prev.month

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    print(f"TROPOMI screening: {start_date} to {end_date}")

    # Get facilities
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            sql = """
                SELECT id, name,
                       ST_Y(centroid::geometry) as latitude,
                       ST_X(centroid::geometry) as longitude
                FROM facilities
                WHERE status = 'active'
            """
            params = []
            if facility_ids:
                sql += " AND id = ANY(%s)"
                params.append(facility_ids)
            sql += " ORDER BY name"

            cur.execute(sql, params)
            facilities = cur.fetchall()

    print(f"Processing {len(facilities)} facilities")

    # Submit tasks
    results = []
    for fac in facilities:
        result = screen_facility.submit(
            facility_id=fac["id"],
            lat=fac["latitude"],
            lon=fac["longitude"],
            name=fac["name"],
            start_date=start_date,
            end_date=end_date,
        )
        results.append(result)

    # Collect results
    completed = [r.result() for r in results if r.result() is not None]
    print(f"Completed: {len(completed)}/{len(facilities)} facilities with results")

    return {"processed": len(facilities), "with_results": len(completed)}


if __name__ == "__main__":
    tropomi_monthly_screening()
