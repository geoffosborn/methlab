"""
Sentinel-2 SWIR band ratio background model.

Builds a temporal regression model of the B12/B11 ratio using a long
time series (1+ year). Methane absorption in B12 causes departures
from the expected ratio, which appear as negative residuals.

Uses HuberRegressor for robustness to outliers (plume-contaminated scenes).

Reference:
    Varon et al. (2021) — Section 2.1: "We build a background model
    for each pixel by regressing B12 reflectance on B11 reflectance
    using a robust linear regression..."
"""

import io
import logging
from dataclasses import dataclass
from pathlib import Path

import boto3
import numpy as np
from sklearn.linear_model import HuberRegressor

from sentinel2.config import get_settings
from sentinel2.download import S2Scene

logger = logging.getLogger(__name__)


@dataclass
class BackgroundModel:
    """Per-pixel robust linear regression of B12 on B11.

    For each pixel position, the model is:
        B12_predicted = slope * B11 + intercept

    Enhancement = B12_predicted - B12_observed
    (positive enhancement indicates CH4 absorption)
    """

    slope: np.ndarray  # Per-pixel slope (2D array)
    intercept: np.ndarray  # Per-pixel intercept (2D array)
    r_squared: np.ndarray  # Per-pixel R² (2D array)
    scene_count: int  # Number of scenes used in model
    shape: tuple[int, int]  # Grid dimensions


def build_background_model(
    scenes: list[S2Scene],
    min_valid_fraction: float = 0.5,
) -> BackgroundModel:
    """Build per-pixel background model from S2 time series.

    For each pixel, fits B12 = slope * B11 + intercept using
    HuberRegressor (robust to CH4 outliers).

    Args:
        scenes: List of S2 scenes spanning 1+ year
        min_valid_fraction: Minimum fraction of scenes with valid data per pixel

    Returns:
        BackgroundModel with per-pixel regression coefficients
    """
    if len(scenes) < 10:
        raise ValueError(
            f"Need at least 10 scenes for background model, got {len(scenes)}"
        )

    shape = scenes[0].b11.shape
    n_scenes = len(scenes)

    # Stack all scenes into 3D arrays (time, rows, cols)
    b11_stack = np.stack([s.b11 for s in scenes], axis=0)
    b12_stack = np.stack([s.b12 for s in scenes], axis=0)

    # Initialize output arrays
    slope = np.full(shape, np.nan)
    intercept = np.full(shape, np.nan)
    r_squared = np.full(shape, np.nan)

    min_valid = int(n_scenes * min_valid_fraction)

    # Fit per-pixel regression
    for i in range(shape[0]):
        for j in range(shape[1]):
            b11_ts = b11_stack[:, i, j]
            b12_ts = b12_stack[:, i, j]

            # Valid timesteps (both bands not NaN)
            valid = ~np.isnan(b11_ts) & ~np.isnan(b12_ts)
            n_valid = valid.sum()

            if n_valid < min_valid:
                continue

            x = b11_ts[valid].reshape(-1, 1)
            y = b12_ts[valid]

            # Robust regression
            try:
                reg = HuberRegressor(epsilon=1.35, max_iter=200)
                reg.fit(x, y)

                slope[i, j] = reg.coef_[0]
                intercept[i, j] = reg.intercept_

                # R² for quality assessment
                y_pred = reg.predict(x)
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                r_squared[i, j] = 1 - ss_res / ss_tot if ss_tot > 0 else 0

            except Exception:
                continue

    valid_pixels = np.sum(~np.isnan(slope))
    total_pixels = shape[0] * shape[1]
    logger.info(
        "Background model built: %d/%d pixels (%.0f%%), %d scenes",
        valid_pixels, total_pixels, 100 * valid_pixels / total_pixels, n_scenes,
    )

    return BackgroundModel(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        scene_count=n_scenes,
        shape=shape,
    )


def save_background_model(model: BackgroundModel, facility_id: int) -> str | None:
    """Cache a fitted background model to S3 as numpy arrays.

    Saves slope, intercept, and r_squared as a single compressed NPZ file.
    Returns the S3 key, or None on failure.
    """
    settings = get_settings()
    s3_key = f"processed/sentinel2/{facility_id}/background_model.npz"

    try:
        buf = io.BytesIO()
        np.savez_compressed(
            buf,
            slope=model.slope,
            intercept=model.intercept,
            r_squared=model.r_squared,
            scene_count=np.array([model.scene_count]),
        )
        buf.seek(0)

        s3 = boto3.client("s3", region_name=settings.aws_region)
        s3.put_object(Bucket=settings.s3_bucket, Key=s3_key, Body=buf.read())

        logger.info("Cached background model to s3://%s/%s", settings.s3_bucket, s3_key)
        return s3_key

    except Exception as e:
        logger.warning("Failed to cache background model: %s", e)
        return None


def load_background_model(facility_id: int) -> BackgroundModel | None:
    """Load a cached background model from S3.

    Returns BackgroundModel if a cached model exists, None otherwise.
    """
    settings = get_settings()
    s3_key = f"processed/sentinel2/{facility_id}/background_model.npz"

    try:
        s3 = boto3.client("s3", region_name=settings.aws_region)
        response = s3.get_object(Bucket=settings.s3_bucket, Key=s3_key)

        buf = io.BytesIO(response["Body"].read())
        data = np.load(buf)

        model = BackgroundModel(
            slope=data["slope"],
            intercept=data["intercept"],
            r_squared=data["r_squared"],
            scene_count=int(data["scene_count"][0]),
            shape=tuple(data["slope"].shape),
        )

        logger.info(
            "Loaded cached background model for facility %d (%d scenes, %s)",
            facility_id, model.scene_count, model.shape,
        )
        return model

    except s3.exceptions.NoSuchKey:
        return None
    except Exception as e:
        logger.debug("No cached background model for facility %d: %s", facility_id, e)
        return None


def get_or_build_background_model(
    facility_id: int,
    scenes: list[S2Scene],
    force_rebuild: bool = False,
) -> BackgroundModel:
    """Load cached background model, or build and cache a new one.

    Args:
        facility_id: Facility ID for cache key
        scenes: S2 scenes for building model (used only if cache miss)
        force_rebuild: Force rebuild even if cached model exists

    Returns:
        BackgroundModel (from cache or freshly built)
    """
    if not force_rebuild:
        cached = load_background_model(facility_id)
        if cached is not None:
            return cached

    model = build_background_model(scenes)
    save_background_model(model, facility_id)
    return model


def predict_b12(model: BackgroundModel, b11: np.ndarray) -> np.ndarray:
    """Predict expected B12 from observed B11 using the background model.

    Args:
        model: Fitted background model
        b11: Observed B11 reflectance for a single scene

    Returns:
        Predicted B12 reflectance (same shape as b11)
    """
    return model.slope * b11 + model.intercept
