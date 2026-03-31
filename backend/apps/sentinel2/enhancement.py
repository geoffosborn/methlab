"""
Sentinel-2 methane enhancement detection.

Computes the residual between predicted and observed B12/B11 ratio,
applies Gaussian smoothing, and masks using upwind statistics
to isolate genuine plume signals from noise.

Reference:
    Varon et al. (2021) — Section 2.2: "The methane enhancement
    is computed as the difference between the predicted and observed
    B12 reflectance, normalized by the predicted B12..."
"""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter

from sentinel2.background import BackgroundModel, predict_b12
from sentinel2.download import S2Scene

logger = logging.getLogger(__name__)


@dataclass
class EnhancementResult:
    """Methane enhancement map from a single S2 scene."""

    scene_id: str
    enhancement: np.ndarray  # 2D ΔXCH4 or ΔB12 enhancement
    plume_mask: np.ndarray  # Boolean mask of plume pixels (after thresholding)
    sigma_threshold: float  # N-sigma threshold used
    upwind_std: float  # Standard deviation of upwind region
    mean_enhancement: float  # Mean enhancement over plume region
    max_enhancement: float  # Peak enhancement


def compute_enhancement(
    scene: S2Scene,
    model: BackgroundModel,
    wind_direction: float,
    gaussian_sigma: float = 0.7,
    sigma_threshold: float = 2.0,
) -> EnhancementResult | None:
    """Compute methane enhancement for a single scene.

    Steps:
    1. Predict B12 from B11 using background model
    2. Compute residual: enhancement = predicted_B12 - observed_B12
    3. Apply Gaussian smoothing (σ=0.7 pixels)
    4. Estimate upwind noise (StdDev of pixels upwind of source)
    5. Mask: plume = pixels where enhancement > N × upwind_σ

    Positive enhancement indicates CH4 absorption (B12 lower than expected).

    Args:
        scene: S2 scene with B11, B12 data
        model: Background regression model
        wind_direction: Meteorological wind direction (degrees, FROM)
        gaussian_sigma: Gaussian smoothing sigma
        sigma_threshold: N-sigma threshold for plume masking

    Returns:
        EnhancementResult or None if insufficient valid data
    """
    # Predict expected B12
    b12_predicted = predict_b12(model, scene.b11)

    # Raw enhancement: positive = CH4 absorption
    raw_enhancement = b12_predicted - scene.b12

    # Mask where model or data is invalid
    valid = ~np.isnan(raw_enhancement) & ~np.isnan(model.slope)
    if valid.sum() < 100:
        logger.debug("Insufficient valid pixels (%d)", valid.sum())
        return None

    # Gaussian smoothing to reduce noise
    # Fill NaN with 0 for filtering, then re-mask
    enhancement = np.where(valid, raw_enhancement, 0.0)
    enhancement = gaussian_filter(enhancement, sigma=gaussian_sigma)
    enhancement = np.where(valid, enhancement, np.nan)

    # Compute upwind statistics for adaptive thresholding
    upwind_mask = _get_upwind_mask(
        shape=scene.b11.shape,
        wind_direction=wind_direction,
    )

    upwind_values = enhancement[upwind_mask & valid]
    if len(upwind_values) < 20:
        # Fall back to full-field statistics
        upwind_values = enhancement[valid]

    upwind_std = float(np.std(upwind_values))
    upwind_mean = float(np.mean(upwind_values))

    if upwind_std <= 0:
        logger.debug("Zero upwind StdDev, skipping scene")
        return None

    # Plume mask: downwind pixels exceeding N-sigma above upwind noise
    threshold = upwind_mean + sigma_threshold * upwind_std
    downwind_mask = ~upwind_mask
    plume_mask = (enhancement > threshold) & valid & downwind_mask

    plume_values = enhancement[plume_mask]
    mean_enh = float(np.mean(plume_values)) if len(plume_values) > 0 else 0.0
    max_enh = float(np.max(plume_values)) if len(plume_values) > 0 else 0.0

    return EnhancementResult(
        scene_id=scene.scene_id,
        enhancement=enhancement,
        plume_mask=plume_mask,
        sigma_threshold=sigma_threshold,
        upwind_std=upwind_std,
        mean_enhancement=mean_enh,
        max_enhancement=max_enh,
    )


def _get_upwind_mask(
    shape: tuple[int, int],
    wind_direction: float,
) -> np.ndarray:
    """Create a boolean mask for the upwind half of the image.

    The facility is assumed to be at the center. Wind direction is
    meteorological (direction FROM). Upwind half = sector the wind
    is coming FROM.

    Args:
        shape: Image (rows, cols)
        wind_direction: Meteorological wind direction (degrees, FROM)

    Returns:
        Boolean mask where True = upwind pixel
    """
    rows, cols = shape
    cy, cx = rows // 2, cols // 2

    # Create coordinate grids relative to center
    y, x = np.mgrid[0:rows, 0:cols]
    dy = y - cy
    dx = x - cx

    # Angle of each pixel from center (mathematical convention)
    pixel_angle = np.degrees(np.arctan2(dy, dx)) % 360

    # Wind FROM direction → the upwind half is centered on this angle
    # Convert meteorological (FROM north, clockwise) to math convention
    wind_from_math = (90 - wind_direction) % 360

    # Angular difference
    diff = np.abs(pixel_angle - wind_from_math)
    diff = np.minimum(diff, 360 - diff)

    # Upwind = within 90° of wind-from direction
    upwind_mask = diff < 90

    return upwind_mask
