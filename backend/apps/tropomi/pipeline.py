"""
TROPOMI CH4 screening pipeline — full orchestration.

Runs the complete wind-rotated TROPOMI CH4 analysis for a facility:
    download → extract AOI → get wind → rotate → aggregate → metrics → visualize → store

Designed to be called by Prefect scheduled flows or on-demand via API.
"""

import json
import logging
from dataclasses import asdict
from datetime import date, timedelta
from enum import Enum
from pathlib import Path

import numpy as np
import psycopg
from psycopg.rows import dict_row

from tropomi.config import get_settings
from tropomi.download import download_facility_overpasses
from tropomi.metrics import TropomiMetrics, compute_metrics
from tropomi.rotation import RotatedField, compute_temporal_average, rotate_field
from tropomi.visualization import render_tear_sheet
from tropomi.wind import get_wind_for_overpass

logger = logging.getLogger(__name__)


class AggregationPeriod(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


def run_facility_analysis(
    facility_id: int,
    lat: float,
    lon: float,
    facility_name: str,
    start_date: date,
    end_date: date,
    period: AggregationPeriod = AggregationPeriod.QUARTERLY,
) -> dict | None:
    """Run complete TROPOMI analysis for a single facility.

    Args:
        facility_id: Database facility ID
        lat: Facility latitude
        lon: Facility longitude
        facility_name: Facility name for visualization
        start_date: Analysis period start
        end_date: Analysis period end
        period: Aggregation period label

    Returns:
        Dict with metrics and S3 paths, or None if insufficient data
    """
    settings = get_settings()

    logger.info(
        "Starting TROPOMI analysis for %s (facility %d), %s to %s",
        facility_name, facility_id, start_date, end_date,
    )

    # Step 1: Download TROPOMI overpasses
    overpasses = download_facility_overpasses(
        facility_id=facility_id,
        lat=lat,
        lon=lon,
        start_date=start_date,
        end_date=end_date,
    )

    if len(overpasses) < 3:
        logger.warning(
            "Only %d overpasses for %s — need at least 3 for meaningful analysis",
            len(overpasses), facility_name,
        )
        return None

    # Step 2: Get wind data and rotate each overpass
    rotated_fields: list[RotatedField] = []

    for overpass in overpasses:
        wind = get_wind_for_overpass(lat, lon, overpass.datetime)
        if wind is None:
            logger.debug("No wind data for overpass %s, skipping", overpass.datetime)
            continue

        # Skip very low wind speeds (< 1 m/s) — rotation undefined
        if wind.speed < 1.0:
            logger.debug("Wind too calm (%.1f m/s), skipping", wind.speed)
            continue

        rotated = rotate_field(overpass, wind, lat, lon)
        if rotated is not None:
            rotated_fields.append(rotated)

    if len(rotated_fields) < 3:
        logger.warning(
            "Only %d rotated fields for %s — insufficient for analysis",
            len(rotated_fields), facility_name,
        )
        return None

    logger.info(
        "Rotated %d/%d overpasses for %s",
        len(rotated_fields), len(overpasses), facility_name,
    )

    # Step 3: Temporal average
    averaged = compute_temporal_average(rotated_fields)

    # Step 4: Compute metrics
    metrics = compute_metrics(averaged, rotated_fields)

    # Step 5: Generate visualization
    period_label = _format_period_label(start_date, end_date, period)
    png_bytes = render_tear_sheet(
        averaged_field=averaged,
        metrics=metrics,
        facility_name=facility_name,
        period_label=period_label,
    )

    # Step 6: Upload to S3
    s3_prefix = f"processed/tropomi/{facility_id}/{start_date.isoformat()}_{end_date.isoformat()}"
    viz_key = f"{s3_prefix}/tear_sheet.png"
    metrics_key = f"{s3_prefix}/metrics.json"
    field_key = f"{s3_prefix}/wind_rotated.npy"

    try:
        import boto3

        s3 = boto3.client("s3", region_name=settings.aws_region)

        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=viz_key,
            Body=png_bytes,
            ContentType="image/png",
        )

        metrics_json = json.dumps(asdict(metrics), default=str)
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=metrics_key,
            Body=metrics_json,
            ContentType="application/json",
        )

        # Save averaged field as numpy array
        import io
        buf = io.BytesIO()
        np.save(buf, averaged)
        buf.seek(0)
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=field_key,
            Body=buf.read(),
            ContentType="application/octet-stream",
        )

        logger.info("Uploaded results to s3://%s/%s", settings.s3_bucket, s3_prefix)

    except Exception as e:
        logger.warning("S3 upload failed (non-fatal): %s", e)
        viz_key = None
        metrics_key = None

    # Step 7: Store in database
    _store_observation(
        facility_id=facility_id,
        start_date=start_date,
        end_date=end_date,
        period=period,
        metrics=metrics,
        viz_s3_key=viz_key,
        metrics_s3_key=metrics_key,
    )

    return {
        "facility_id": facility_id,
        "facility_name": facility_name,
        "period": period_label,
        "metrics": asdict(metrics),
        "s3_viz_key": viz_key,
        "s3_metrics_key": metrics_key,
    }


def run_all_facilities(
    start_date: date,
    end_date: date,
    period: AggregationPeriod = AggregationPeriod.QUARTERLY,
) -> list[dict]:
    """Run TROPOMI analysis for all active facilities.

    Designed to be called as a Prefect flow on a monthly schedule.
    """
    settings = get_settings()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, name,
                       ST_Y(centroid::geometry) as latitude,
                       ST_X(centroid::geometry) as longitude
                FROM facilities
                WHERE status = 'active'
                ORDER BY name
            """)
            facilities = cur.fetchall()

    logger.info("Running TROPOMI analysis for %d facilities", len(facilities))

    results = []
    for fac in facilities:
        try:
            result = run_facility_analysis(
                facility_id=fac["id"],
                lat=fac["latitude"],
                lon=fac["longitude"],
                facility_name=fac["name"],
                start_date=start_date,
                end_date=end_date,
                period=period,
            )
            if result:
                results.append(result)
        except Exception as e:
            logger.error("Failed analysis for %s: %s", fac["name"], e, exc_info=True)

    logger.info(
        "Completed TROPOMI analysis: %d/%d facilities with results",
        len(results), len(facilities),
    )

    return results


def _store_observation(
    facility_id: int,
    start_date: date,
    end_date: date,
    period: AggregationPeriod,
    metrics: TropomiMetrics,
    viz_s3_key: str | None,
    metrics_s3_key: str | None,
):
    """Store TROPOMI observation results in database."""
    settings = get_settings()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tropomi_observations (
                    facility_id, period_start, period_end, aggregation_period,
                    mean_enhancement_ppb, max_enhancement_ppb, central_box_mean_ppb,
                    sample_count, valid_pixel_fraction, mean_wind_speed,
                    intensity_score, background_ch4_ppb,
                    viz_s3_key, metrics_s3_key
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s
                )
                ON CONFLICT (facility_id, period_start, period_end, aggregation_period)
                DO UPDATE SET
                    mean_enhancement_ppb = EXCLUDED.mean_enhancement_ppb,
                    max_enhancement_ppb = EXCLUDED.max_enhancement_ppb,
                    central_box_mean_ppb = EXCLUDED.central_box_mean_ppb,
                    sample_count = EXCLUDED.sample_count,
                    valid_pixel_fraction = EXCLUDED.valid_pixel_fraction,
                    mean_wind_speed = EXCLUDED.mean_wind_speed,
                    intensity_score = EXCLUDED.intensity_score,
                    background_ch4_ppb = EXCLUDED.background_ch4_ppb,
                    viz_s3_key = EXCLUDED.viz_s3_key,
                    metrics_s3_key = EXCLUDED.metrics_s3_key,
                    updated_at = now()
                """,
                [
                    facility_id, start_date, end_date, period.value,
                    metrics.mean_enhancement_ppb, metrics.max_enhancement_ppb,
                    metrics.central_box_mean_ppb,
                    metrics.sample_count, metrics.valid_pixel_fraction,
                    metrics.mean_wind_speed,
                    metrics.intensity_score, metrics.background_ch4_ppb,
                    viz_s3_key, metrics_s3_key,
                ],
            )
            conn.commit()

    logger.info("Stored TROPOMI observation for facility %d", facility_id)


def _format_period_label(
    start_date: date, end_date: date, period: AggregationPeriod
) -> str:
    """Format a human-readable period label."""
    if period == AggregationPeriod.MONTHLY:
        return start_date.strftime("%B %Y")
    elif period == AggregationPeriod.QUARTERLY:
        q = (start_date.month - 1) // 3 + 1
        return f"{start_date.year} Q{q}"
    else:
        return str(start_date.year)
