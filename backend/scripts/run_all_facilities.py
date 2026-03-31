"""Run TROPOMI pipeline for all active Safeguard facilities.

Processes recent quarters (default: last 4) and stores results in the database.
Cleans TROPOMI cache between facilities to manage disk space.

Usage:
    cd backend
    .venv/bin/python scripts/run_all_facilities.py                    # Last 4 quarters
    .venv/bin/python scripts/run_all_facilities.py --quarters 6       # Last 6 quarters
    .venv/bin/python scripts/run_all_facilities.py --facility-id 1    # Single facility
    .venv/bin/python scripts/run_all_facilities.py --dry-run          # Preview only
"""

import os
os.environ["PROJ_DATA"] = ""
os.environ["PROJ_LIB"] = ""

import sys
sys.path.insert(0, "apps")
sys.path.insert(0, "packages/common")

import argparse
import gc
import logging
import shutil
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import psycopg
from psycopg.rows import dict_row

from tropomi.config import get_settings
from tropomi.download import TROPOMI_CACHE_DIR
from tropomi.pipeline import AggregationPeriod, run_facility_analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("batch")


def get_quarters(n: int) -> list[tuple[date, date]]:
    """Return the last N complete quarters as (start, end) pairs."""
    today = date.today()
    # Current quarter start
    q = (today.month - 1) // 3
    current_q_start = date(today.year, q * 3 + 1, 1)

    quarters = []
    dt = current_q_start
    for _ in range(n):
        # Go back one quarter
        if dt.month <= 3:
            dt = date(dt.year - 1, 10, 1)
        else:
            dt = date(dt.year, dt.month - 3, 1)
        # End of this quarter
        if dt.month >= 10:
            end = date(dt.year, 12, 31)
        else:
            end = date(dt.year, dt.month + 3, 1) - timedelta(days=1)
        quarters.append((dt, end))

    return list(reversed(quarters))


def get_facilities(facility_id: int | None = None) -> list[dict]:
    """Fetch active facilities from database."""
    settings = get_settings()
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if facility_id:
                cur.execute("""
                    SELECT id, name,
                           ST_Y(centroid::geometry) as latitude,
                           ST_X(centroid::geometry) as longitude
                    FROM facilities
                    WHERE id = %s
                """, [facility_id])
            else:
                cur.execute("""
                    SELECT id, name,
                           ST_Y(centroid::geometry) as latitude,
                           ST_X(centroid::geometry) as longitude
                    FROM facilities
                    WHERE status = 'active' AND safeguard_covered = true
                    ORDER BY name
                """)
            return cur.fetchall()


def clean_tropomi_cache():
    """Delete cached TROPOMI files to free disk space."""
    if TROPOMI_CACHE_DIR.exists():
        for f in TROPOMI_CACHE_DIR.glob("*.nc"):
            f.unlink()
        for f in TROPOMI_CACHE_DIR.glob("*.tmp"):
            try:
                f.unlink()
            except OSError:
                pass
    gc.collect()


def main():
    parser = argparse.ArgumentParser(description="Batch TROPOMI analysis for Safeguard facilities")
    parser.add_argument("--quarters", type=int, default=4, help="Number of recent quarters (default: 4)")
    parser.add_argument("--facility-id", type=int, help="Run single facility by ID")
    parser.add_argument("--dry-run", action="store_true", help="Preview facilities and quarters only")
    args = parser.parse_args()

    quarters = get_quarters(args.quarters)
    facilities = get_facilities(args.facility_id)

    print(f"\nMethLab Batch TROPOMI Runner")
    print(f"{'=' * 60}")
    print(f"Facilities: {len(facilities)}")
    print(f"Quarters:   {len(quarters)}")
    for start, end in quarters:
        q = (start.month - 1) // 3 + 1
        print(f"  {start.year} Q{q}: {start} to {end}")
    print(f"Total runs: {len(facilities) * len(quarters)}")
    print()

    if args.dry_run:
        for fac in facilities:
            print(f"  [{fac['id']:>3}] {fac['name']} ({fac['latitude']:.4f}, {fac['longitude']:.4f})")
        print("\n(dry run — no data processed)")
        return

    results = []
    total = len(facilities) * len(quarters)
    done = 0

    for fac in facilities:
        for start, end in quarters:
            done += 1
            q = (start.month - 1) // 3 + 1
            label = f"{start.year} Q{q}"

            logger.info(
                "[%d/%d] %s — %s",
                done, total, fac["name"], label,
            )

            try:
                result = run_facility_analysis(
                    facility_id=fac["id"],
                    lat=fac["latitude"],
                    lon=fac["longitude"],
                    facility_name=fac["name"],
                    start_date=start,
                    end_date=end,
                    period=AggregationPeriod.QUARTERLY,
                )

                if result:
                    m = result["metrics"]
                    results.append({
                        "facility": fac["name"],
                        "quarter": label,
                        "status": "ok",
                        "mean_ppb": round(m["mean_enhancement_ppb"], 1),
                        "intensity": round(m["intensity_score"], 0),
                        "samples": m["sample_count"],
                    })
                    logger.info(
                        "  %s: mean=%.1f ppb, score=%.0f, samples=%d",
                        fac["name"], m["mean_enhancement_ppb"],
                        m["intensity_score"], m["sample_count"],
                    )
                else:
                    results.append({
                        "facility": fac["name"],
                        "quarter": label,
                        "status": "insufficient",
                    })

            except Exception as e:
                logger.error("  Failed: %s", e, exc_info=True)
                results.append({
                    "facility": fac["name"],
                    "quarter": label,
                    "status": "error",
                    "error": str(e),
                })

            # Clean cache between runs to manage disk
            clean_tropomi_cache()

    # Summary
    print(f"\n{'=' * 60}")
    print("BATCH RESULTS")
    print(f"{'=' * 60}")

    ok = [r for r in results if r["status"] == "ok"]
    insuf = [r for r in results if r["status"] == "insufficient"]
    errs = [r for r in results if r["status"] == "error"]

    print(f"  Success: {len(ok)}, Insufficient data: {len(insuf)}, Errors: {len(errs)}")
    print()

    if ok:
        # Top 10 by intensity
        top = sorted(ok, key=lambda r: r["intensity"], reverse=True)[:10]
        print("Top 10 by intensity score:")
        for r in top:
            print(f"  {r['facility']:30s} {r['quarter']:8s}  mean={r['mean_ppb']:5.1f} ppb  score={r['intensity']:.0f}  n={r['samples']}")

    if errs:
        print(f"\nErrors:")
        for r in errs:
            print(f"  {r['facility']:30s} {r['quarter']:8s}  {r.get('error', 'unknown')}")


if __name__ == "__main__":
    main()
