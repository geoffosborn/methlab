"""Run real TROPOMI pipeline for Moranbah North Q4 2024."""

import sys
sys.path.insert(0, "apps")
sys.path.insert(0, "packages/common")

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

from datetime import date
from tropomi.pipeline import run_facility_analysis, AggregationPeriod

# Full Q4 2024 — will download all files (cached ones skip)
result = run_facility_analysis(
    facility_id=1,
    lat=-22.0833,
    lon=148.0500,
    facility_name="Moranbah North",
    start_date=date(2024, 10, 1),
    end_date=date(2024, 12, 31),
    period=AggregationPeriod.QUARTERLY,
)

if result:
    print("\n=== RESULT ===")
    for k, v in result.items():
        if k != "metrics":
            print(f"  {k}: {v}")
    print("  metrics:")
    for k, v in result["metrics"].items():
        print(f"    {k}: {v}")
else:
    print("No result — insufficient data")
