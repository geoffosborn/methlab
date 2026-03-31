"""
Sentinel-2 methane detection pipeline — full orchestration.

Runs the complete S2 SWIR plume detection and quantification for a facility:
    download → background model → enhancement → segmentation → quantification → store

Triggered by new S2 scenes (via Prefect schedule) or on-demand.
"""

import json
import logging
from dataclasses import asdict
from datetime import date, timedelta

import numpy as np
import psycopg
from psycopg.rows import dict_row

from sentinel2.background import get_or_build_background_model
from sentinel2.config import get_settings
from sentinel2.download import S2Scene, download_facility_scenes
from sentinel2.enhancement import compute_enhancement
from sentinel2.quantification import EmissionEstimate, quantify_emission
from sentinel2.segmentation import segment_plumes

logger = logging.getLogger(__name__)


def run_facility_detection(
    facility_id: int,
    lat: float,
    lon: float,
    facility_name: str,
    target_date: date,
    wind_speed: float,
    wind_direction: float,
) -> list[dict]:
    """Run S2 plume detection for a facility on a specific date.

    This processes a single scene (or recent scenes) against the
    background model to detect and quantify plumes.

    Args:
        facility_id: Database facility ID
        lat: Facility latitude
        lon: Facility longitude
        facility_name: Name for logging/storage
        target_date: Date to process
        wind_speed: ERA5 10m wind speed (m/s)
        wind_direction: Meteorological wind direction (degrees, FROM)

    Returns:
        List of detection result dicts
    """
    settings = get_settings()

    logger.info("Starting S2 detection for %s on %s", facility_name, target_date)

    # Step 1: Download background time series (1 year before target)
    bg_start = target_date - timedelta(days=400)
    bg_end = target_date - timedelta(days=30)  # Exclude recent months

    bg_scenes = download_facility_scenes(
        facility_id=facility_id,
        lat=lat,
        lon=lon,
        start_date=bg_start,
        end_date=bg_end,
    )

    if len(bg_scenes) < settings.min_background_scenes:
        logger.warning(
            "Insufficient background scenes (%d < %d) for %s",
            len(bg_scenes), settings.min_background_scenes, facility_name,
        )
        return []

    # Step 2: Build background model
    model = get_or_build_background_model(facility_id, bg_scenes)

    # Step 3: Download target scene(s)
    target_scenes = download_facility_scenes(
        facility_id=facility_id,
        lat=lat,
        lon=lon,
        start_date=target_date - timedelta(days=5),
        end_date=target_date + timedelta(days=5),
    )

    if not target_scenes:
        logger.info("No S2 scenes found near %s for %s", target_date, facility_name)
        return []

    results = []

    for scene in target_scenes:
        # Step 4: Compute enhancement
        enhancement = compute_enhancement(
            scene=scene,
            model=model,
            wind_direction=wind_direction,
            gaussian_sigma=settings.gaussian_sigma,
            sigma_threshold=settings.upwind_sigma_threshold,
        )

        if enhancement is None:
            continue

        # Step 5: Segment plumes
        segments = segment_plumes(enhancement, min_plume_pixels=settings.min_plume_pixels)

        if not segments:
            logger.debug("No plume clusters found in %s", scene.scene_id)
            continue

        # Step 6: Quantify each plume
        for i, segment in enumerate(segments):
            estimate = quantify_emission(
                segment=segment,
                scene=scene,
                wind_speed_10m=wind_speed,
            )

            detection = {
                "facility_id": facility_id,
                "scene_id": scene.scene_id,
                "scene_datetime": scene.datetime.isoformat(),
                "plume_index": i,
                "emission_rate_kg_hr": estimate.emission_rate_kg_hr,
                "emission_rate_t_hr": estimate.emission_rate_t_hr,
                "ime_kg": estimate.ime_kg,
                "effective_wind_m_s": estimate.effective_wind_m_s,
                "plume_length_m": estimate.plume_length_m,
                "plume_area_m2": segment.area_m2,
                "plume_pixels": segment.area_pixels,
                "mean_enhancement": segment.mean_enhancement,
                "max_enhancement": segment.max_enhancement,
                "uncertainty_kg_hr": estimate.uncertainty_kg_hr,
                "wind_speed_10m": wind_speed,
                "wind_direction": wind_direction,
                "solar_zenith": scene.solar_zenith,
                "view_zenith": scene.view_zenith,
                "cloud_cover": scene.cloud_cover,
            }

            # Store in database
            _store_detection(detection)

            # Upload artifacts to S3
            _upload_artifacts(
                facility_id=facility_id,
                scene=scene,
                enhancement=enhancement,
                segment=segment,
                detection=detection,
            )

            results.append(detection)

            logger.info(
                "Detection: %s plume %d — %.1f kg/hr (%.2f t/hr), %d pixels, "
                "IME=%.1f kg, Ueff=%.1f m/s, L=%.0f m",
                facility_name, i,
                estimate.emission_rate_kg_hr, estimate.emission_rate_t_hr,
                segment.area_pixels, estimate.ime_kg,
                estimate.effective_wind_m_s, estimate.plume_length_m,
            )

    return results


def _store_detection(detection: dict):
    """Store a plume detection in the database."""
    settings = get_settings()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO s2_detections (
                    facility_id, scene_id, scene_datetime,
                    emission_rate_kg_hr, uncertainty_kg_hr,
                    ime_kg, effective_wind_m_s, plume_length_m,
                    plume_area_m2, plume_pixels,
                    mean_enhancement, max_enhancement,
                    wind_speed_10m, wind_direction,
                    solar_zenith, view_zenith, cloud_cover,
                    confidence
                ) VALUES (
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s
                )
                """,
                [
                    detection["facility_id"],
                    detection["scene_id"],
                    detection["scene_datetime"],
                    detection["emission_rate_kg_hr"],
                    detection["uncertainty_kg_hr"],
                    detection["ime_kg"],
                    detection["effective_wind_m_s"],
                    detection["plume_length_m"],
                    detection["plume_area_m2"],
                    detection["plume_pixels"],
                    detection["mean_enhancement"],
                    detection["max_enhancement"],
                    detection["wind_speed_10m"],
                    detection["wind_direction"],
                    detection["solar_zenith"],
                    detection["view_zenith"],
                    detection["cloud_cover"],
                    _compute_confidence(detection),
                ],
            )
            conn.commit()


def _compute_confidence(detection: dict) -> str:
    """Assign detection confidence level based on signal quality."""
    pixels = detection.get("plume_pixels", 0)
    enhancement = detection.get("mean_enhancement", 0)

    if pixels >= 100 and enhancement > 0.01:
        return "high"
    elif pixels >= 60 and enhancement > 0.005:
        return "medium"
    else:
        return "low"


def _upload_artifacts(
    facility_id: int,
    scene: S2Scene,
    enhancement,
    segment,
    detection: dict,
):
    """Upload detection artifacts (enhancement map, plume mask) to S3."""
    settings = get_settings()
    date_str = scene.datetime.strftime("%Y%m%d")
    s3_prefix = f"processed/sentinel2/{facility_id}/{date_str}"

    try:
        import io
        import boto3

        s3 = boto3.client("s3", region_name=settings.aws_region)

        # Upload enhancement array
        buf = io.BytesIO()
        np.save(buf, enhancement.enhancement)
        buf.seek(0)
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=f"{s3_prefix}/enhancement.npy",
            Body=buf.read(),
        )

        # Upload plume mask
        buf = io.BytesIO()
        np.save(buf, enhancement.plume_mask)
        buf.seek(0)
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=f"{s3_prefix}/plume_mask.npy",
            Body=buf.read(),
        )

        # Upload detection metadata
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=f"{s3_prefix}/detection.json",
            Body=json.dumps(detection, default=str),
            ContentType="application/json",
        )

    except Exception as e:
        logger.warning("S3 upload failed (non-fatal): %s", e)
