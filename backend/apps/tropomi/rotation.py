"""
Wind rotation of TROPOMI CH4 fields.

For each overpass, rotates the CH4 concentration field by the wind direction
so that wind blows uniformly from south to north. Averaging many rotated
fields suppresses noise and reveals persistent point-source plume signals.

Reference:
    Ehret et al. (2022) "Quantification of methane emissions from
    satellite observations by wind rotation", ACP.

    Sadavarte et al. (2021) "Methane emissions from superemitting
    coal mines in Australia quantified using TROPOMI satellite
    observations", Environ. Sci. Technol.
"""

import logging
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import rotate as ndimage_rotate

from tropomi.download import TropomiOverpass
from tropomi.wind import WindField

logger = logging.getLogger(__name__)


@dataclass
class RotatedField:
    """A wind-rotated CH4 anomaly field centered on a facility."""

    ch4_anomaly: np.ndarray  # 2D array, CH4 enhancement above background (ppb)
    wind_speed: float  # Wind speed at overpass time (m/s)
    wind_direction: float  # Wind direction FROM (degrees)
    rotation_angle: float  # Applied rotation angle (degrees)
    pixel_count: int  # Number of valid pixels
    background_ch4: float  # Estimated background CH4 (ppb)


def estimate_background(ch4: np.ndarray, percentile: float = 10.0) -> float:
    """Estimate background CH4 from the field.

    Uses a low percentile of valid values as the background estimate,
    following standard practice in TROPOMI point-source studies.

    Args:
        ch4: 2D CH4 concentration array (ppb), may contain NaN
        percentile: Percentile for background estimation

    Returns:
        Background CH4 value in ppb
    """
    valid = ch4[~np.isnan(ch4)]
    if len(valid) == 0:
        return 1850.0  # Global mean CH4 approximate

    return float(np.nanpercentile(valid, percentile))


def regrid_to_regular(
    ch4: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    center_lat: float,
    center_lon: float,
    grid_size: int = 30,
    pixel_size_km: float = 5.0,
) -> np.ndarray:
    """Regrid irregular TROPOMI swath onto a regular grid centered on facility.

    TROPOMI pixels are ~5.5x7 km; we create a regular grid at similar
    resolution centered on the facility.

    Args:
        ch4: CH4 values (may be 1D or 2D)
        lat: Latitude values
        lon: Longitude values
        center_lat: Facility latitude
        center_lon: Facility longitude
        grid_size: Output grid dimension (grid_size x grid_size)
        pixel_size_km: Grid pixel size in km

    Returns:
        2D regular grid (grid_size x grid_size), NaN where no data
    """
    ch4_flat = ch4.ravel()
    lat_flat = lat.ravel()
    lon_flat = lon.ravel()

    # Valid mask
    valid = ~np.isnan(ch4_flat)
    if valid.sum() == 0:
        return np.full((grid_size, grid_size), np.nan)

    # Convert lat/lon to km offsets from center
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * np.cos(np.radians(center_lat))

    x_km = (lon_flat - center_lon) * km_per_deg_lon
    y_km = (lat_flat - center_lat) * km_per_deg_lat

    # Grid extent
    extent_km = grid_size * pixel_size_km / 2

    # Bin into grid
    grid = np.full((grid_size, grid_size), np.nan)
    counts = np.zeros((grid_size, grid_size))

    for i in range(len(ch4_flat)):
        if not valid[i]:
            continue

        xi = int((x_km[i] + extent_km) / pixel_size_km)
        yi = int((y_km[i] + extent_km) / pixel_size_km)

        if 0 <= xi < grid_size and 0 <= yi < grid_size:
            if np.isnan(grid[yi, xi]):
                grid[yi, xi] = ch4_flat[i]
                counts[yi, xi] = 1
            else:
                grid[yi, xi] += ch4_flat[i]
                counts[yi, xi] += 1

    # Average where multiple pixels fell in same grid cell
    with np.errstate(invalid="ignore"):
        grid = np.where(counts > 0, grid / counts, np.nan)

    return grid


def rotate_field(
    overpass: TropomiOverpass,
    wind: WindField,
    center_lat: float,
    center_lon: float,
    grid_size: int = 30,
) -> RotatedField | None:
    """Rotate a TROPOMI CH4 field by wind direction.

    Steps:
    1. Regrid irregular TROPOMI data onto regular grid centered on facility
    2. Compute CH4 anomaly (subtract background)
    3. Rotate grid by wind direction so wind points north
    4. Return rotated anomaly field

    Args:
        overpass: TROPOMI overpass data
        wind: Concurrent wind data
        center_lat: Facility latitude
        center_lon: Facility longitude
        grid_size: Output grid dimension

    Returns:
        RotatedField or None if insufficient data
    """
    # Regrid to regular grid
    grid = regrid_to_regular(
        overpass.ch4_column,
        overpass.latitude,
        overpass.longitude,
        center_lat,
        center_lon,
        grid_size=grid_size,
    )

    valid_count = np.sum(~np.isnan(grid))
    if valid_count < 20:
        logger.debug("Insufficient valid pixels after regridding (%d)", valid_count)
        return None

    # Estimate and subtract background
    background = estimate_background(grid)
    anomaly = grid - background

    # Replace NaN with 0 for rotation (will be masked back after)
    nan_mask = np.isnan(anomaly)
    anomaly_filled = np.where(nan_mask, 0.0, anomaly)

    # Rotate by wind direction
    rotation_angle = wind.rotation_angle
    rotated = ndimage_rotate(anomaly_filled, rotation_angle, reshape=False, order=1, mode="constant", cval=0.0)

    # Also rotate the NaN mask to maintain valid pixel tracking
    nan_rotated = ndimage_rotate(nan_mask.astype(float), rotation_angle, reshape=False, order=0, mode="constant", cval=1.0)
    rotated = np.where(nan_rotated > 0.5, np.nan, rotated)

    return RotatedField(
        ch4_anomaly=rotated,
        wind_speed=wind.speed,
        wind_direction=wind.direction_from,
        rotation_angle=rotation_angle,
        pixel_count=int(valid_count),
        background_ch4=background,
    )


def compute_temporal_average(
    rotated_fields: list[RotatedField],
) -> np.ndarray:
    """Average multiple wind-rotated CH4 anomaly fields.

    Uses NaN-aware averaging so pixels with partial temporal coverage
    are still included with appropriate weighting.

    Args:
        rotated_fields: List of rotated anomaly fields

    Returns:
        2D averaged anomaly array (ppb above background)
    """
    if not rotated_fields:
        raise ValueError("No rotated fields to average")

    stack = np.stack([f.ch4_anomaly for f in rotated_fields], axis=0)

    with np.errstate(all="ignore"):
        avg = np.nanmean(stack, axis=0)

    return avg
