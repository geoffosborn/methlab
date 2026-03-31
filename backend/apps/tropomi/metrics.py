"""
TROPOMI CH4 enhancement metrics for facility monitoring.

Computes quantitative metrics from wind-rotated CH4 anomaly fields:
- Mean/max enhancement above background over central region
- Sample count and temporal coverage
- Composite intensity score for facility ranking

Reference:
    Sadavarte et al. (2021) — central bounding box metric approach
    for Australian coal mine methane characterization.
"""

import logging
from dataclasses import dataclass

import numpy as np

from tropomi.rotation import RotatedField

logger = logging.getLogger(__name__)


@dataclass
class TropomiMetrics:
    """Quantitative CH4 enhancement metrics from TROPOMI analysis."""

    mean_enhancement_ppb: float  # Mean CH4 above background in central box
    max_enhancement_ppb: float  # Peak CH4 above background
    median_enhancement_ppb: float  # Median enhancement
    std_enhancement_ppb: float  # Standard deviation of enhancement
    central_box_mean_ppb: float  # Mean in facility-centered box (downwind)
    sample_count: int  # Number of overpasses averaged
    valid_pixel_fraction: float  # Fraction of grid with data
    mean_wind_speed: float  # Mean wind speed across overpasses (m/s)
    intensity_score: float  # Composite ranking score [0-100]
    background_ch4_ppb: float  # Mean estimated background


def compute_metrics(
    averaged_field: np.ndarray,
    rotated_fields: list[RotatedField],
    central_box_fraction: float = 0.5,
) -> TropomiMetrics:
    """Compute CH4 enhancement metrics from an averaged wind-rotated field.

    The central box captures the facility location and the downwind plume
    region (north half of grid after wind rotation). Enhancement is
    measured relative to the background-subtracted field.

    Args:
        averaged_field: 2D mean CH4 anomaly (ppb above background)
        rotated_fields: Individual rotated fields used in average
        central_box_fraction: Fraction of grid for central analysis box

    Returns:
        TropomiMetrics with all computed values
    """
    grid_size = averaged_field.shape[0]
    center = grid_size // 2

    # Central box dimensions (wider E-W for cross-wind, extended north for downwind)
    box_half = int(grid_size * central_box_fraction / 2)

    # Downwind box: centered horizontally, extends from center to north
    # (after wind rotation, plume extends northward from source)
    downwind_box = averaged_field[
        center : center + box_half * 2,  # North (downwind)
        center - box_half : center + box_half,  # E-W centered
    ]

    # Full central box (includes upwind for reference)
    full_box = averaged_field[
        center - box_half : center + box_half,
        center - box_half : center + box_half,
    ]

    # Valid pixel statistics
    valid_mask = ~np.isnan(averaged_field)
    valid_fraction = float(valid_mask.sum()) / averaged_field.size

    # Enhancement metrics
    valid_values = averaged_field[valid_mask]
    downwind_valid = downwind_box[~np.isnan(downwind_box)]
    central_valid = full_box[~np.isnan(full_box)]

    if len(valid_values) == 0:
        return _empty_metrics(rotated_fields)

    mean_enh = float(np.mean(valid_values))
    max_enh = float(np.max(valid_values))
    median_enh = float(np.median(valid_values))
    std_enh = float(np.std(valid_values))

    central_mean = float(np.mean(central_valid)) if len(central_valid) > 0 else 0.0

    # Wind statistics
    wind_speeds = [f.wind_speed for f in rotated_fields]
    mean_wind = float(np.mean(wind_speeds)) if wind_speeds else 0.0

    # Background CH4
    backgrounds = [f.background_ch4 for f in rotated_fields]
    mean_bg = float(np.mean(backgrounds)) if backgrounds else 1850.0

    # Intensity score: composite metric for ranking facilities
    # Combines central enhancement magnitude, sample confidence, and consistency
    intensity = _compute_intensity_score(
        central_mean=central_mean,
        max_enhancement=max_enh,
        sample_count=len(rotated_fields),
        valid_fraction=valid_fraction,
        std_enhancement=std_enh,
    )

    return TropomiMetrics(
        mean_enhancement_ppb=mean_enh,
        max_enhancement_ppb=max_enh,
        median_enhancement_ppb=median_enh,
        std_enhancement_ppb=std_enh,
        central_box_mean_ppb=central_mean,
        sample_count=len(rotated_fields),
        valid_pixel_fraction=valid_fraction,
        mean_wind_speed=mean_wind,
        intensity_score=intensity,
        background_ch4_ppb=mean_bg,
    )


def _compute_intensity_score(
    central_mean: float,
    max_enhancement: float,
    sample_count: int,
    valid_fraction: float,
    std_enhancement: float,
) -> float:
    """Compute a composite intensity score [0-100] for facility ranking.

    Higher scores indicate stronger, more consistent methane enhancement.
    Typical active coal mine values: 5-30 ppb above background.
    """
    # Enhancement magnitude (0-60 points)
    # 5 ppb = ~10 points, 15 ppb = ~30 points, 30 ppb = ~50 points
    mag_score = min(60, central_mean * 2.0) if central_mean > 0 else 0

    # Sample confidence (0-20 points)
    # More overpasses = more confidence in the signal
    conf_score = min(20, sample_count * 0.5)

    # Signal-to-noise (0-20 points)
    if std_enhancement > 0 and central_mean > 0:
        snr = central_mean / std_enhancement
        snr_score = min(20, snr * 5)
    else:
        snr_score = 0

    return float(min(100, mag_score + conf_score + snr_score))


def _empty_metrics(rotated_fields: list[RotatedField]) -> TropomiMetrics:
    """Return zero metrics when no valid data available."""
    return TropomiMetrics(
        mean_enhancement_ppb=0.0,
        max_enhancement_ppb=0.0,
        median_enhancement_ppb=0.0,
        std_enhancement_ppb=0.0,
        central_box_mean_ppb=0.0,
        sample_count=len(rotated_fields),
        valid_pixel_fraction=0.0,
        mean_wind_speed=0.0,
        intensity_score=0.0,
        background_ch4_ppb=1850.0,
    )
