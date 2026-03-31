"""
Validation runner: compare pipeline output against published values
for known Australian coal mine emitters.

Reference sites with published TROPOMI data:
    - Moranbah North (Anglo American): High methane, published in Sadavarte 2021
    - Hail Creek (Glencore): Reference tear sheet in multiple publications
    - Goonyella Riverside (BHP): Major emitter, Bowen Basin

Expected TROPOMI intensity ranges for active Bowen Basin coal mines:
    - Active underground: 15-40 ppb central enhancement
    - Active open cut: 5-20 ppb
    - Care & maintenance: < 5 ppb

Published Varon controlled release validation:
    - 19/10/21: ground truth 7.2 t/h
    - 29/10/21: ground truth 5.0 t/h
    - 03/11/21: ground truth 1.4 t/h
    - Korpeje: published 11.2 ± 5.2 t/h

Usage:
    python scripts/validate_known_emitters.py --dry-run  # Check config only
    python scripts/validate_known_emitters.py            # Run validation
    python scripts/validate_known_emitters.py --site moranbah  # Single site
"""

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import date

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ValidationSite:
    """A validation site with expected metric ranges."""

    name: str
    facility_name: str  # Must match facilities table
    lat: float
    lon: float
    expected_enhancement_ppb: tuple[float, float]  # (min, max) expected range
    expected_intensity_score: tuple[float, float]  # (min, max)
    notes: str = ""


# Known validation sites
VALIDATION_SITES = [
    ValidationSite(
        name="moranbah",
        facility_name="Moranbah North",
        lat=-22.0833,
        lon=148.0500,
        expected_enhancement_ppb=(10.0, 40.0),
        expected_intensity_score=(25.0, 90.0),
        notes="Underground longwall, high methane. Published in Sadavarte et al. (2021).",
    ),
    ValidationSite(
        name="hail_creek",
        facility_name="Hail Creek",
        lat=-21.5167,
        lon=148.3667,
        expected_enhancement_ppb=(5.0, 25.0),
        expected_intensity_score=(15.0, 70.0),
        notes="Open cut + underground. Reference site in multiple TROPOMI publications.",
    ),
    ValidationSite(
        name="goonyella",
        facility_name="Goonyella Riverside",
        lat=-21.8167,
        lon=148.1167,
        expected_enhancement_ppb=(10.0, 35.0),
        expected_intensity_score=(20.0, 85.0),
        notes="Major Bowen Basin mine, BHP. High historical emissions.",
    ),
    ValidationSite(
        name="appin",
        facility_name="Appin",
        lat=-34.2000,
        lon=150.7833,
        expected_enhancement_ppb=(5.0, 30.0),
        expected_intensity_score=(15.0, 75.0),
        notes="Illawarra underground longwall, known high-emitter.",
    ),
    ValidationSite(
        name="hazelwood",
        facility_name="Hazelwood",
        lat=-38.2833,
        lon=146.3833,
        expected_enhancement_ppb=(0.0, 5.0),
        expected_intensity_score=(0.0, 15.0),
        notes="Closed brown coal mine. Should show minimal/no signal. Negative control.",
    ),
]


def validate_tropomi(
    site: ValidationSite,
    start_date: date,
    end_date: date,
) -> dict:
    """Run TROPOMI validation for a single site.

    Returns dict with pass/fail status and metrics.
    """
    from tropomi.pipeline import AggregationPeriod, run_facility_analysis

    logger.info("=" * 60)
    logger.info("Validating: %s", site.name)
    logger.info("  Facility: %s (%.4f, %.4f)", site.facility_name, site.lat, site.lon)
    logger.info("  Period: %s to %s", start_date, end_date)
    logger.info("  Expected enhancement: %.1f - %.1f ppb", *site.expected_enhancement_ppb)
    logger.info("  Expected intensity: %.0f - %.0f", *site.expected_intensity_score)
    logger.info("  Notes: %s", site.notes)

    result = run_facility_analysis(
        facility_id=0,  # Dummy ID for validation
        lat=site.lat,
        lon=site.lon,
        facility_name=site.facility_name,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.ANNUAL,
    )

    if result is None:
        logger.warning("  RESULT: No data (insufficient overpasses)")
        return {"site": site.name, "status": "no_data", "metrics": None}

    metrics = result["metrics"]
    enhancement = metrics["central_box_mean_ppb"]
    intensity = metrics["intensity_score"]
    sample_count = metrics["sample_count"]

    # Check against expected ranges
    enh_pass = site.expected_enhancement_ppb[0] <= enhancement <= site.expected_enhancement_ppb[1]
    int_pass = site.expected_intensity_score[0] <= intensity <= site.expected_intensity_score[1]

    status = "PASS" if (enh_pass and int_pass) else "FAIL"

    logger.info("  RESULT: %s", status)
    logger.info("    Enhancement: %.1f ppb (expected %.1f-%.1f) %s",
                enhancement, *site.expected_enhancement_ppb, "OK" if enh_pass else "FAIL")
    logger.info("    Intensity:   %.0f (expected %.0f-%.0f) %s",
                intensity, *site.expected_intensity_score, "OK" if int_pass else "FAIL")
    logger.info("    Samples:     %d overpasses", sample_count)
    logger.info("    Wind speed:  %.1f m/s mean", metrics["mean_wind_speed"])
    logger.info("    Background:  %.0f ppb", metrics["background_ch4_ppb"])

    return {
        "site": site.name,
        "status": status,
        "enhancement_ppb": enhancement,
        "intensity_score": intensity,
        "sample_count": sample_count,
        "enh_pass": enh_pass,
        "int_pass": int_pass,
        "metrics": metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate pipeline against known emitters")
    parser.add_argument("--site", type=str, help="Run single site (name)")
    parser.add_argument("--start", type=str, default="2024-01-01", help="Start date")
    parser.add_argument("--end", type=str, default="2024-12-31", help="End date")
    parser.add_argument("--dry-run", action="store_true", help="Print config only")
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)

    # Filter sites
    if args.site:
        sites = [s for s in VALIDATION_SITES if s.name == args.site]
        if not sites:
            print(f"Unknown site: {args.site}")
            print(f"Available: {', '.join(s.name for s in VALIDATION_SITES)}")
            sys.exit(1)
    else:
        sites = VALIDATION_SITES

    print(f"\nMethLab Validation Runner")
    print(f"{'=' * 60}")
    print(f"Sites: {len(sites)}")
    print(f"Period: {start_date} to {end_date}")
    print()

    if args.dry_run:
        for site in sites:
            print(f"  {site.name}: {site.facility_name}")
            print(f"    Expected: {site.expected_enhancement_ppb[0]}-{site.expected_enhancement_ppb[1]} ppb")
            print(f"    Notes: {site.notes}")
        print("\n(dry run — no data processed)")
        return

    results = []
    for site in sites:
        try:
            result = validate_tropomi(site, start_date, end_date)
            results.append(result)
        except Exception as e:
            logger.error("Failed validation for %s: %s", site.name, e, exc_info=True)
            results.append({"site": site.name, "status": "error", "error": str(e)})

    # Summary
    print(f"\n{'=' * 60}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 60}")

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    no_data = sum(1 for r in results if r["status"] == "no_data")
    errors = sum(1 for r in results if r["status"] == "error")

    for r in results:
        symbol = {"PASS": "OK", "FAIL": "FAIL", "no_data": "SKIP", "error": "ERR"}
        print(f"  [{symbol.get(r['status'], '?'):>4}] {r['site']}", end="")
        if r.get("enhancement_ppb") is not None:
            print(f"  — {r['enhancement_ppb']:.1f} ppb, score {r['intensity_score']:.0f}", end="")
        print()

    print(f"\n  Passed: {passed}, Failed: {failed}, No data: {no_data}, Errors: {errors}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
