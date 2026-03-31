"""Run Sentinel-2 plume detection for top TROPOMI emitters.

Queries the database for facilities with the highest TROPOMI intensity scores,
then runs S2 detection for recent dates.

Usage:
    cd backend
    .venv/bin/python scripts/run_s2_top_emitters.py              # Top 10
    .venv/bin/python scripts/run_s2_top_emitters.py --top 5      # Top 5
    .venv/bin/python scripts/run_s2_top_emitters.py --dry-run    # Preview only
"""

import os
os.environ["PROJ_DATA"] = ""
os.environ["PROJ_LIB"] = ""

import sys
sys.path.insert(0, "apps")
sys.path.insert(0, "packages/common")

import argparse
import logging
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()

import psycopg
from psycopg.rows import dict_row

from sentinel2.config import get_settings as get_s2_settings
from sentinel2.pipeline import run_facility_detection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("s2_top")


def get_top_emitters(n: int) -> list[dict]:
    """Get top N facilities by TROPOMI intensity score."""
    from tropomi.config import get_settings
    settings = get_settings()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT
                    f.id, f.name,
                    ST_Y(f.centroid::geometry) as latitude,
                    ST_X(f.centroid::geometry) as longitude,
                    MAX(t.intensity_score) as max_intensity,
                    AVG(t.intensity_score) as avg_intensity,
                    MAX(t.mean_enhancement_ppb) as max_enhancement,
                    COUNT(t.id) as observations
                FROM facilities f
                JOIN tropomi_observations t ON t.facility_id = f.id
                WHERE t.viz_s3_key IS NOT NULL  -- real data only
                GROUP BY f.id, f.name, f.centroid
                HAVING MAX(t.intensity_score) > 0
                ORDER BY MAX(t.intensity_score) DESC
                LIMIT %s
            """, [n])
            return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(description="S2 detection for top TROPOMI emitters")
    parser.add_argument("--top", type=int, default=10, help="Number of top facilities (default: 10)")
    parser.add_argument("--target-date", type=str, help="Target date (default: 30 days ago)")
    parser.add_argument("--wind-speed", type=float, default=5.0, help="Default wind speed m/s")
    parser.add_argument("--wind-direction", type=float, default=270.0, help="Default wind direction")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()

    target = date.fromisoformat(args.target_date) if args.target_date else date.today() - timedelta(days=30)

    emitters = get_top_emitters(args.top)

    print(f"\nS2 Plume Detection — Top {args.top} Emitters")
    print(f"{'=' * 60}")
    print(f"Target date: {target}")
    print(f"Facilities found: {len(emitters)}")
    print()

    for e in emitters:
        print(f"  [{e['id']:>3}] {e['name']:30s}  intensity={e['max_intensity']:.0f}  enhancement={e['max_enhancement']:.1f} ppb  obs={e['observations']}")

    if args.dry_run:
        print("\n(dry run — no S2 processing)")
        return

    if not emitters:
        print("No facilities with real TROPOMI data yet. Run the batch TROPOMI pipeline first.")
        return

    print()
    results = []
    for e in emitters:
        logger.info("Running S2 detection for %s (intensity=%.0f)", e["name"], e["max_intensity"])
        try:
            result = run_facility_detection(
                facility_id=e["id"],
                lat=e["latitude"],
                lon=e["longitude"],
                target_date=target,
                wind_speed=args.wind_speed,
                wind_direction=args.wind_direction,
            )
            if result:
                results.append({"facility": e["name"], "status": "detected", **result})
                logger.info("  Detection: %.1f kg/hr ± %.1f", result.get("emission_rate_kg_hr", 0), result.get("uncertainty_kg_hr", 0))
            else:
                results.append({"facility": e["name"], "status": "no_detection"})
                logger.info("  No plume detected")
        except Exception as ex:
            logger.error("  Failed: %s", ex, exc_info=True)
            results.append({"facility": e["name"], "status": "error", "error": str(ex)})

    # Summary
    print(f"\n{'=' * 60}")
    print("S2 DETECTION SUMMARY")
    print(f"{'=' * 60}")
    detected = [r for r in results if r["status"] == "detected"]
    print(f"  Detected: {len(detected)}, No detection: {len([r for r in results if r['status'] == 'no_detection'])}, Errors: {len([r for r in results if r['status'] == 'error'])}")
    if detected:
        print("\nDetections:")
        for r in detected:
            print(f"  {r['facility']:30s}  {r.get('emission_rate_kg_hr', 0):.1f} kg/hr ± {r.get('uncertainty_kg_hr', 0):.1f}")


if __name__ == "__main__":
    main()
