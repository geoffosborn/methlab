"""
TROPOMI CH4 data download via Microsoft Planetary Computer STAC API.

Uses the sentinel-5p-l2-ch4 collection to retrieve methane column
concentrations over a facility's area of interest.

Reference:
    Lorente et al. (2021) "Methane retrieved from TROPOMI: improvement
    of the data product and validation of the first 2 years of
    measurements", AMT.
"""

import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import h5py
import numpy as np
import planetary_computer
import requests
from pystac_client import Client

from tropomi.config import get_settings

logger = logging.getLogger(__name__)

# Local cache for downloaded TROPOMI files
TROPOMI_CACHE_DIR = Path("D:/tmp/tropomi")

STAC_API_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "sentinel-5p-l2-netcdf"
PRODUCT_FILTER = {"s5p:product_name": {"eq": "ch4"}}


@dataclass
class TropomiOverpass:
    """A single TROPOMI overpass extracted over a facility AOI."""

    datetime: datetime
    ch4_column: np.ndarray  # 2D array of XCH4 (ppb)
    latitude: np.ndarray  # 2D array of pixel latitudes
    longitude: np.ndarray  # 2D array of pixel longitudes
    qa_value: np.ndarray  # 2D array of quality flags
    solar_zenith: np.ndarray  # Solar zenith angle


def get_aoi_bbox(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Compute bounding box around a point.

    Returns (west, south, east, north) in degrees.
    """
    # Approximate degrees per km at given latitude
    deg_lat = radius_km / 111.32
    deg_lon = radius_km / (111.32 * np.cos(np.radians(lat)))

    return (
        lon - deg_lon,  # west
        lat - deg_lat,  # south
        lon + deg_lon,  # east
        lat + deg_lat,  # north
    )


def search_overpasses(
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    radius_km: float | None = None,
) -> list[dict]:
    """Search Planetary Computer for TROPOMI CH4 overpasses over a facility.

    Args:
        lat: Facility latitude
        lon: Facility longitude
        start_date: Start of search window
        end_date: End of search window
        radius_km: AOI radius (default from config)

    Returns:
        List of STAC item dicts with signed asset URLs
    """
    settings = get_settings()
    if radius_km is None:
        radius_km = settings.aoi_radius_km

    bbox = get_aoi_bbox(lat, lon, radius_km)

    catalog = Client.open(STAC_API_URL, modifier=planetary_computer.sign_inplace)

    search = catalog.search(
        collections=[COLLECTION],
        bbox=bbox,
        datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
        query=PRODUCT_FILTER,
    )

    items = list(search.items())
    logger.info(
        "Found %d TROPOMI overpasses for (%.2f, %.2f) between %s and %s",
        len(items),
        lat,
        lon,
        start_date,
        end_date,
    )

    return items


def extract_aoi(
    item: dict,
    lat: float,
    lon: float,
    radius_km: float | None = None,
) -> TropomiOverpass | None:
    """Extract CH4 data over facility AOI from a STAC item.

    Opens the NetCDF asset, subsets to the AOI bounding box, and applies
    quality filtering.

    Args:
        item: STAC item from search_overpasses
        lat: Facility latitude
        lon: Facility longitude
        radius_km: AOI radius

    Returns:
        TropomiOverpass with extracted data, or None if insufficient data
    """
    settings = get_settings()
    if radius_km is None:
        radius_km = settings.aoi_radius_km

    bbox = get_aoi_bbox(lat, lon, radius_km)

    try:
        # Download file to local cache (S5P L2 NetCDF can't be opened remotely)
        local_path = _download_to_cache(item)
        if local_path is None:
            return None

        # S5P L2 CH4 files use HDF5 groups under PRODUCT/
        with h5py.File(local_path, "r") as f:
            product = f["PRODUCT"]

            # Use bias-corrected destriped XCH4 (best quality)
            if "methane_mixing_ratio_bias_corrected_destriped" in product:
                ch4 = product["methane_mixing_ratio_bias_corrected_destriped"][0]
            elif "methane_mixing_ratio_bias_corrected" in product:
                ch4 = product["methane_mixing_ratio_bias_corrected"][0]
            else:
                ch4 = product["methane_mixing_ratio"][0]

            lats = product["latitude"][0]
            lons = product["longitude"][0]
            # qa_value is stored as uint8 [0-100] representing percentage
            qa_raw = product["qa_value"][0]
            qa = qa_raw.astype(np.float32) / 100.0

            # Solar zenith from support data if available
            try:
                solar_zenith = f["PRODUCT/SUPPORT_DATA/GEOLOCATIONS/solar_zenith_angle"][0]
            except KeyError:
                solar_zenith = np.zeros_like(ch4)

        # Subset to AOI
        lat_mask = (lats >= bbox[1]) & (lats <= bbox[3])
        lon_mask = (lons >= bbox[0]) & (lons <= bbox[2])
        aoi_mask = lat_mask & lon_mask

        if aoi_mask.sum() < 10:
            logger.debug("Insufficient pixels in AOI (%d), skipping", aoi_mask.sum())
            return None

        # Apply quality filter
        qa_mask = qa >= settings.min_qa_value
        valid_mask = aoi_mask & qa_mask

        if valid_mask.sum() < 5:
            logger.debug("Insufficient quality pixels (%d), skipping", valid_mask.sum())
            return None

        # Parse datetime from item
        dt = item.datetime
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

        logger.debug(
            "Extracted %d valid pixels from %s",
            valid_mask.sum(), item.id,
        )

        return TropomiOverpass(
            datetime=dt,
            ch4_column=np.where(valid_mask, ch4, np.nan).astype(np.float32),
            latitude=lats.astype(np.float32),
            longitude=lons.astype(np.float32),
            qa_value=qa,
            solar_zenith=solar_zenith.astype(np.float32),
        )

    except Exception as e:
        logger.warning("Failed to extract AOI from item %s: %s", item.id, e)
        return None


def _download_to_cache(item) -> Path | None:
    """Download a TROPOMI NetCDF file to local cache, skipping if already cached."""
    TROPOMI_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = TROPOMI_CACHE_DIR / f"{item.id}.nc"

    if local_path.exists():
        logger.debug("Using cached %s", item.id)
        return local_path

    asset_href = item.assets["ch4"].href

    try:
        logger.info("Downloading %s...", item.id)
        resp = requests.get(asset_href, stream=True, timeout=120)
        resp.raise_for_status()

        # Write to temp file first, then rename (atomic)
        tmp_path = local_path.with_suffix(".tmp")
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=128 * 1024):
                f.write(chunk)
        tmp_path.rename(local_path)

        size_mb = local_path.stat().st_size / 1024 / 1024
        logger.info("Downloaded %s (%.1f MB)", item.id, size_mb)
        return local_path

    except Exception as e:
        logger.warning("Download failed for %s: %s", item.id, e)
        return None


def download_facility_overpasses(
    facility_id: int,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
) -> list[TropomiOverpass]:
    """Download all TROPOMI overpasses for a facility in a date range.

    Args:
        facility_id: Database facility ID
        lat: Facility latitude
        lon: Facility longitude
        start_date: Start date
        end_date: End date

    Returns:
        List of TropomiOverpass objects with valid data
    """
    items = search_overpasses(lat, lon, start_date, end_date)

    # Pre-download files in parallel (2 concurrent), then extract sequentially
    _prefetch_items(items, max_workers=2)

    overpasses = []
    for item in items:
        overpass = extract_aoi(item, lat, lon)
        if overpass is not None:
            overpasses.append(overpass)

    logger.info(
        "Extracted %d valid overpasses (of %d total) for facility %d",
        len(overpasses),
        len(items),
        facility_id,
    )

    return overpasses


def _prefetch_items(items: list, max_workers: int = 2) -> None:
    """Download TROPOMI files in parallel using a thread pool."""
    # Filter to items not yet cached
    to_download = [
        item for item in items
        if not (TROPOMI_CACHE_DIR / f"{item.id}.nc").exists()
    ]

    if not to_download:
        logger.info("All %d files already cached", len(items))
        return

    logger.info(
        "Downloading %d files (%d already cached), %d parallel workers",
        len(to_download), len(items) - len(to_download), max_workers,
    )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_download_to_cache, item): item for item in to_download}
        done = 0
        for future in as_completed(futures):
            done += 1
            item = futures[future]
            try:
                path = future.result()
                if path and done % 10 == 0:
                    logger.info("Download progress: %d/%d", done, len(to_download))
            except Exception as e:
                logger.warning("Download failed for %s: %s", item.id, e)
