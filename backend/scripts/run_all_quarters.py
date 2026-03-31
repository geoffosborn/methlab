"""Run TROPOMI pipeline for Moranbah North — all quarters since S5P launch.

Generates tear sheet PNGs and GeoTIFFs for each quarter.
Cleans up downloaded TROPOMI files after each quarter to manage disk space.
ERA5 wind files are kept (small, reusable across quarters).
"""

import os
# Avoid PROJ conflict with PostGIS installation
os.environ["PROJ_DATA"] = ""
os.environ["PROJ_LIB"] = ""

import sys
sys.path.insert(0, "apps")
sys.path.insert(0, "packages/common")

import gc
import logging
import shutil
from datetime import date
from pathlib import Path

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("batch")

from tropomi.download import download_facility_overpasses, TROPOMI_CACHE_DIR
from tropomi.wind import get_wind_for_overpass
from tropomi.rotation import rotate_field, compute_temporal_average
from tropomi.metrics import compute_metrics
from tropomi.visualization import render_tear_sheet, export_geotiff

# Moranbah North
FACILITY_ID = 1
LAT, LON = -22.0833, 148.0500
FACILITY_NAME = "Moranbah North"

# Output directory
OUTPUT_DIR = Path("D:/tmp/methlab_output/moranbah_north")

# Quarters: S5P CH4 operational from Q3 2018
QUARTERS = []
for year in range(2018, 2025):
    for q in range(1, 5):
        if year == 2018 and q < 3:
            continue  # No data before Q3 2018
        month_start = (q - 1) * 3 + 1
        start = date(year, month_start, 1)
        # End of quarter = day before next quarter starts
        if q == 4:
            end = date(year, 12, 31)
        else:
            end = date(year, q * 3 + 1, 1) - __import__("datetime").timedelta(days=1)
        QUARTERS.append((year, q, start, end))


def disk_free_gb(path: str = "D:/") -> float:
    """Return free disk space in GB."""
    usage = shutil.disk_usage(path)
    return usage.free / (1024 ** 3)


def clean_tropomi_cache():
    """Delete cached TROPOMI NetCDF files to free disk space."""
    if TROPOMI_CACHE_DIR.exists():
        for f in TROPOMI_CACHE_DIR.glob("*.nc"):
            f.unlink()
        for f in TROPOMI_CACHE_DIR.glob("*.tmp"):
            try:
                f.unlink()
            except OSError:
                pass
    gc.collect()


def run_quarter(year: int, quarter: int, start: date, end: date) -> dict | None:
    """Run pipeline for a single quarter."""
    label = f"{year} Q{quarter}"
    quarter_dir = OUTPUT_DIR / f"{year}_Q{quarter}"
    quarter_dir.mkdir(parents=True, exist_ok=True)

    # Skip if already processed
    tiff_path = quarter_dir / "ch4_enhancement.tif"
    png_path = quarter_dir / "tear_sheet.png"
    if tiff_path.exists() and png_path.exists():
        logger.info("Skipping %s — already processed", label)
        return {"quarter": label, "status": "skipped"}

    free_gb = disk_free_gb()
    logger.info("=== %s === (%.1f GB free)", label, free_gb)

    if free_gb < 5.0:
        logger.warning("Low disk space (%.1f GB), cleaning cache first", free_gb)
        clean_tropomi_cache()
        free_gb = disk_free_gb()
        if free_gb < 3.0:
            logger.error("Insufficient disk space (%.1f GB), stopping", free_gb)
            return None

    # Step 1: Download & extract
    overpasses = download_facility_overpasses(FACILITY_ID, LAT, LON, start, end)
    if len(overpasses) < 3:
        logger.warning("%s: only %d overpasses, skipping", label, len(overpasses))
        clean_tropomi_cache()
        return {"quarter": label, "status": "insufficient_data", "overpasses": len(overpasses)}

    # Step 2: Wind + rotation
    rotated = []
    for op in overpasses:
        wind = get_wind_for_overpass(LAT, LON, op.datetime)
        if wind and wind.speed >= 1.0:
            r = rotate_field(op, wind, LAT, LON)
            if r:
                rotated.append(r)

    # Free overpass data before continuing
    del overpasses
    clean_tropomi_cache()

    if len(rotated) < 3:
        logger.warning("%s: only %d rotated fields, skipping", label, len(rotated))
        return {"quarter": label, "status": "insufficient_wind", "rotated": len(rotated)}

    # Step 3: Average + metrics
    avg = compute_temporal_average(rotated)
    metrics = compute_metrics(avg, rotated)

    # Step 4: GeoTIFF
    export_geotiff(avg, LAT, LON, tiff_path)

    # Step 5: Tear sheet PNG
    png = render_tear_sheet(avg, metrics, FACILITY_NAME, label)
    png_path.write_bytes(png)
    logger.info("Saved tear sheet to %s (%d KB)", png_path, len(png) // 1024)

    result = {
        "quarter": label,
        "status": "success",
        "overpasses": metrics.sample_count,
        "mean_ppb": round(metrics.mean_enhancement_ppb, 1),
        "peak_ppb": round(metrics.max_enhancement_ppb, 1),
        "intensity": round(metrics.intensity_score, 0),
    }
    logger.info("%s result: %s", label, result)
    return result


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for year, q, start, end in QUARTERS:
        try:
            result = run_quarter(year, q, start, end)
            if result is None:
                break  # Disk space failure
            results.append(result)
        except Exception as e:
            logger.error("Failed %d Q%d: %s", year, q, e, exc_info=True)
            results.append({"quarter": f"{year} Q{q}", "status": "error", "error": str(e)})
            clean_tropomi_cache()

    # Summary
    print("\n" + "=" * 60)
    print("BATCH RESULTS — Moranbah North")
    print("=" * 60)
    for r in results:
        if r["status"] == "success":
            print(f"  {r['quarter']:10s}  mean={r['mean_ppb']:5.1f} ppb  peak={r['peak_ppb']:5.1f} ppb  score={r['intensity']:.0f}")
        else:
            print(f"  {r['quarter']:10s}  {r['status']}")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
