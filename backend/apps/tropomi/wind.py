"""
ERA5 wind data retrieval for TROPOMI wind rotation.

Downloads 10m u/v wind components from the Copernicus Climate Data Store
(CDS) API concurrent with TROPOMI overpass times. Wind data is used to
rotate CH4 fields so that wind blows uniformly north, enabling temporal
averaging that preserves directional plume signals.

Reference:
    Ehret et al. (2022) "Quantification of methane emissions from
    satellite observations by wind rotation", ACP.
"""

import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from tropomi.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class WindField:
    """Wind data at a specific time and location."""

    datetime: datetime
    u10: float  # 10m eastward wind component (m/s)
    v10: float  # 10m northward wind component (m/s)

    @property
    def speed(self) -> float:
        """Wind speed magnitude (m/s)."""
        return float(np.sqrt(self.u10**2 + self.v10**2))

    @property
    def direction_from(self) -> float:
        """Meteorological wind direction (degrees, direction wind blows FROM).

        0 = from north, 90 = from east, 180 = from south, 270 = from west.
        """
        # atan2 gives angle of wind vector (direction wind blows TO)
        # Meteorological convention is direction FROM, so add 180
        angle_to = np.degrees(np.arctan2(-self.u10, -self.v10))
        return float(angle_to % 360)

    @property
    def rotation_angle(self) -> float:
        """Angle to rotate field so wind blows uniformly from south (toward north).

        This is the negative of the wind-from direction since we want
        to rotate the field so the wind direction aligns with north.
        """
        return -self.direction_from


def download_era5_wind(
    lat: float,
    lon: float,
    target_date: date,
    hour: int = 12,
) -> WindField | None:
    """Download ERA5 10m wind for a specific location and time.

    Uses the CDS API to retrieve u10/v10 wind components. In production,
    bulk-downloads monthly files for Australia and caches in S3.

    Args:
        lat: Latitude
        lon: Longitude
        target_date: Date of interest
        hour: Hour of day (UTC, default 12 for ~midday overpass)

    Returns:
        WindField with u10/v10 components, or None on failure
    """
    settings = get_settings()
    cache_dir = Path(settings.era5_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Cache file for this month
    cache_file = cache_dir / f"era5_wind_{target_date.strftime('%Y%m')}.nc"

    try:
        if cache_file.exists():
            return _extract_from_cache(cache_file, lat, lon, target_date, hour)

        # Download via CDS API
        import cdsapi

        client = cdsapi.Client()

        # Request wind data for the entire month (bulk efficiency)
        year = str(target_date.year)
        month = str(target_date.month).zfill(2)

        # Australia bounding box with margin
        area = [-10, 110, -45, 155]  # [N, W, S, E]

        client.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": ["10m_u_component_of_wind", "10m_v_component_of_wind"],
                "year": year,
                "month": month,
                "day": [str(d).zfill(2) for d in range(1, 32)],
                "time": [f"{h:02d}:00" for h in range(0, 24, 3)],  # 3-hourly
                "area": area,
                "format": "netcdf",
            },
            str(cache_file),
        )

        logger.info("Downloaded ERA5 wind data for %s-%s to %s", year, month, cache_file)
        return _extract_from_cache(cache_file, lat, lon, target_date, hour)

    except Exception as e:
        logger.warning("Failed to get ERA5 wind for %s: %s", target_date, e)
        return None


def _extract_from_cache(
    cache_file: Path,
    lat: float,
    lon: float,
    target_date: date,
    hour: int,
) -> WindField | None:
    """Extract wind at specific location/time from cached NetCDF file."""
    import xarray as xr

    try:
        ds = xr.open_dataset(cache_file)

        # CDS API may use 'valid_time' or 'time' as the time dimension
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"

        # Find nearest time
        target_dt = np.datetime64(datetime(target_date.year, target_date.month, target_date.day, hour))
        ds_point = ds.sel(
            latitude=lat,
            longitude=lon,
            **{time_dim: target_dt},
            method="nearest",
        )

        u10 = float(ds_point["u10"].values.item())
        v10 = float(ds_point["v10"].values.item())

        actual_time = ds_point[time_dim].values
        dt = datetime.utcfromtimestamp(
            np.datetime64(actual_time, "s").astype(int)
        )

        ds.close()

        return WindField(datetime=dt, u10=u10, v10=v10)

    except Exception as e:
        logger.warning("Failed to extract wind from cache: %s", e)
        return None


def get_wind_for_overpass(
    lat: float,
    lon: float,
    overpass_time: datetime,
) -> WindField | None:
    """Get wind data concurrent with a TROPOMI overpass.

    Finds the closest ERA5 time step to the overpass.

    Args:
        lat: Facility latitude
        lon: Facility longitude
        overpass_time: TROPOMI overpass datetime (UTC)

    Returns:
        WindField or None
    """
    return download_era5_wind(
        lat=lat,
        lon=lon,
        target_date=overpass_time.date(),
        hour=overpass_time.hour,
    )
