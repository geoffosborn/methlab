"""
Sentinel-2 L2A data download for methane plume detection.

Downloads B11 (1610nm SWIR1) and B12 (2190nm SWIR2) bands from
Copernicus Data Space Ecosystem (CDSE) STAC API. B12 has strong
CH4 absorption; B11 is the reference band.

Reference:
    Varon et al. (2021) "High-frequency monitoring of anomalous
    methane point sources with multispectral Sentinel-2 satellite
    observations", ACP.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import numpy as np
import requests
import rasterio
from pystac_client import Client

from sentinel2.config import get_settings

logger = logging.getLogger(__name__)

# CDSE Keycloak token endpoint
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

_cdse_token: str | None = None


def _get_cdse_token() -> str:
    """Get CDSE OAuth access token using username/password."""
    global _cdse_token
    if _cdse_token is not None:
        return _cdse_token

    settings = get_settings()
    if not settings.cdse_username or not settings.cdse_password:
        raise RuntimeError("CDSE credentials not configured (CDSE_USERNAME, CDSE_PASSWORD)")

    resp = requests.post(CDSE_TOKEN_URL, data={
        "grant_type": "password",
        "username": settings.cdse_username,
        "password": settings.cdse_password,
        "client_id": "cdse-public",
    })
    resp.raise_for_status()
    _cdse_token = resp.json()["access_token"]
    return _cdse_token

# Copernicus Data Space Ecosystem STAC endpoint
CDSE_STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac"
COLLECTION = "sentinel-2-l2a"


@dataclass
class S2Scene:
    """A single Sentinel-2 scene with SWIR bands over facility AOI."""

    scene_id: str
    datetime: datetime
    b11: np.ndarray  # SWIR1 1610nm (20m resolution)
    b12: np.ndarray  # SWIR2 2190nm (20m resolution)
    transform: rasterio.transform.Affine  # Geospatial transform
    crs: str
    cloud_cover: float
    solar_zenith: float  # Solar zenith angle (degrees)
    view_zenith: float  # Viewing zenith angle (degrees)
    bounds: tuple[float, float, float, float]  # (west, south, east, north)


def get_aoi_bbox(
    lat: float, lon: float, radius_km: float
) -> tuple[float, float, float, float]:
    """Compute bounding box around a point. Returns (west, south, east, north)."""
    deg_lat = radius_km / 111.32
    deg_lon = radius_km / (111.32 * np.cos(np.radians(lat)))
    return (lon - deg_lon, lat - deg_lat, lon + deg_lon, lat + deg_lat)


def search_scenes(
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    max_cloud_cover: float | None = None,
) -> list[dict]:
    """Search CDSE STAC for Sentinel-2 L2A scenes over a facility.

    Args:
        lat: Facility latitude
        lon: Facility longitude
        start_date: Start of search window
        end_date: End of search window
        max_cloud_cover: Maximum cloud cover percentage

    Returns:
        List of STAC items sorted by date
    """
    settings = get_settings()
    if max_cloud_cover is None:
        max_cloud_cover = settings.max_cloud_cover

    bbox = get_aoi_bbox(lat, lon, settings.aoi_radius_km)

    catalog = Client.open(CDSE_STAC_URL)

    search = catalog.search(
        collections=[COLLECTION],
        bbox=bbox,
        datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
        query={"eo:cloud_cover": {"lte": max_cloud_cover}},
    )

    items = list(search.items())
    items.sort(key=lambda x: x.datetime)

    logger.info(
        "Found %d S2 scenes for (%.2f, %.2f) with <%.0f%% cloud, %s to %s",
        len(items), lat, lon, max_cloud_cover, start_date, end_date,
    )

    return items


def extract_bands(
    item: dict,
    lat: float,
    lon: float,
) -> S2Scene | None:
    """Extract B11 and B12 bands from a STAC item over facility AOI.

    Args:
        item: STAC item from search_scenes
        lat: Facility latitude
        lon: Facility longitude

    Returns:
        S2Scene with band data, or None on failure
    """
    settings = get_settings()
    bbox = get_aoi_bbox(lat, lon, settings.aoi_radius_km)

    try:
        # Get band asset URLs
        b11_href = item.assets["B11"].href
        b12_href = item.assets["B12"].href

        # Authenticate via GDAL /vsicurl/ bearer token
        token = _get_cdse_token()
        gdal_env = rasterio.Env(
            GDAL_HTTP_HEADERS=f"Authorization: Bearer {token}",
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        )

        # Read B11 (SWIR1, 20m)
        with gdal_env, rasterio.open(b11_href) as src:
            window = rasterio.windows.from_bounds(*bbox, transform=src.transform)
            b11 = src.read(1, window=window).astype(np.float32)
            transform = rasterio.windows.transform(window, src.transform)
            crs = str(src.crs)

        # Read B12 (SWIR2, 20m) — same grid
        with gdal_env, rasterio.open(b12_href) as src:
            window = rasterio.windows.from_bounds(*bbox, transform=src.transform)
            b12 = src.read(1, window=window).astype(np.float32)

        # Validate shapes match
        if b11.shape != b12.shape:
            logger.warning("Band shape mismatch: B11=%s, B12=%s", b11.shape, b12.shape)
            return None

        # Convert to reflectance (S2 L2A stores as int, scale factor 10000)
        b11 = b11 / 10000.0
        b12 = b12 / 10000.0

        # Mask invalid values
        valid = (b11 > 0) & (b12 > 0) & (b11 < 1) & (b12 < 1)
        b11 = np.where(valid, b11, np.nan)
        b12 = np.where(valid, b12, np.nan)

        # Extract metadata
        cloud_cover = item.properties.get("eo:cloud_cover", 0)
        solar_zenith = item.properties.get("view:sun_elevation", 45)
        solar_zenith = 90 - solar_zenith  # Convert elevation to zenith
        view_zenith = item.properties.get("view:off_nadir", 0)

        dt = item.datetime
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

        return S2Scene(
            scene_id=item.id,
            datetime=dt,
            b11=b11,
            b12=b12,
            transform=transform,
            crs=crs,
            cloud_cover=cloud_cover,
            solar_zenith=solar_zenith,
            view_zenith=view_zenith,
            bounds=bbox,
        )

    except Exception as e:
        logger.warning("Failed to extract bands from %s: %s", item.id, e)
        return None


def download_facility_scenes(
    facility_id: int,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
) -> list[S2Scene]:
    """Download all S2 scenes for a facility in a date range.

    Returns list of S2Scene objects with valid B11/B12 data.
    """
    items = search_scenes(lat, lon, start_date, end_date)

    scenes = []
    for item in items:
        scene = extract_bands(item, lat, lon)
        if scene is not None:
            scenes.append(scene)

    logger.info(
        "Extracted %d valid scenes (of %d) for facility %d",
        len(scenes), len(items), facility_id,
    )

    return scenes
