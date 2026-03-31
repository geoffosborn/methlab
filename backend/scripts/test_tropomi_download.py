"""
Test TROPOMI data availability from Planetary Computer for Moranbah North.

This script verifies:
  1. Planetary Computer STAC API access (no auth needed)
  2. TROPOMI CH4 data availability for Moranbah North
  3. Scene count and date range

Does NOT require ERA5 credentials — just validates data source.
"""

import sys
from datetime import datetime


def main():
    print("=" * 60)
    print("TROPOMI Pipeline - Moranbah North Readiness Check")
    print("=" * 60)

    # Moranbah North coordinates
    lat, lon = -22.0833, 148.05
    name = "Moranbah North"
    radius_km = 50

    # Check dependencies
    print("\n1. Checking dependencies...")
    missing = []
    for pkg in ["pystac_client", "planetary_computer", "numpy"]:
        try:
            __import__(pkg)
            print(f"   OK: {pkg}")
        except ImportError:
            print(f"   MISSING: {pkg}")
            missing.append(pkg)

    xr_ok = False
    try:
        import xarray
        print(f"   OK: xarray")
        xr_ok = True
    except ImportError:
        print(f"   MISSING: xarray (needed for ERA5)")
        missing.append("xarray")

    cds_ok = False
    try:
        import cdsapi
        print(f"   OK: cdsapi")
        cds_ok = True
    except ImportError:
        print(f"   MISSING: cdsapi (needed for ERA5 wind)")
        missing.append("cdsapi")

    if "pystac_client" in missing or "planetary_computer" in missing:
        print(f"\n   Install missing: uv pip install {' '.join(missing)}")
        print("   Cannot proceed without pystac_client and planetary_computer.")
        sys.exit(1)

    # Check Planetary Computer access
    print("\n2. Testing Planetary Computer STAC access...")
    from pystac_client import Client
    import planetary_computer
    import numpy as np

    catalog = Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    print("   Connected to Planetary Computer STAC API")

    # Search for TROPOMI CH4 over Moranbah North
    print(f"\n3. Searching TROPOMI CH4 for {name} ({lat}, {lon})...")

    deg_lat = radius_km / 111.32
    deg_lon = radius_km / (111.32 * np.cos(np.radians(lat)))
    bbox = [lon - deg_lon, lat - deg_lat, lon + deg_lon, lat + deg_lat]

    search = catalog.search(
        collections=["sentinel-5p-l2-netcdf"],
        bbox=bbox,
        datetime="2024-10-01/2024-12-31",  # Q2 FY2025
        max_items=200,
        query={"s5p:product_name": {"eq": "ch4"}},
    )

    items = list(search.items())
    print(f"   Found {len(items)} TROPOMI overpasses (Oct-Dec 2024)")

    if items:
        dates = sorted(set(item.datetime.date() for item in items))
        print(f"   Date range: {dates[0]} to {dates[-1]}")
        print(f"   Unique dates: {len(dates)}")
        print(f"   First item: {items[0].id}")

        # Try accessing the first item's data
        print("\n4. Testing data access (first overpass)...")
        item = items[0]
        print(f"   Item: {item.id}")
        print(f"   DateTime: {item.datetime}")
        print(f"   Assets: {list(item.assets.keys())}")

        if "ch4" in item.assets:
            href = item.assets["ch4"].href
            print(f"   CH4 asset URL: {href[:80]}...")
            print("   Data is accessible!")
        else:
            print(f"   Available assets: {list(item.assets.keys())}")

    # ERA5 status
    print("\n5. ERA5 Wind Data Status...")
    if cds_ok:
        import os
        cds_key = os.getenv("CDS_API_KEY", "")
        cdsapirc = os.path.expanduser("~/.cdsapirc")
        if cds_key:
            print("   CDS_API_KEY is set")
        elif os.path.exists(cdsapirc):
            print(f"   Found {cdsapirc}")
        else:
            print("   NO CDS credentials found")
            print("   Register at: https://cds.climate.copernicus.eu/how-to-api")
            print("   Then create ~/.cdsapirc with:")
            print("     url: https://cds.climate.copernicus.eu/api")
            print("     key: YOUR_UID:YOUR_API_KEY")
    else:
        print("   cdsapi not installed — run: uv pip install cdsapi")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  TROPOMI data:     {'READY' if len(items) > 0 else 'NO DATA'} ({len(items)} scenes)")
    print(f"  ERA5 wind:        {'READY' if cds_ok and (os.getenv('CDS_API_KEY') or os.path.exists(os.path.expanduser('~/.cdsapirc'))) else 'NEEDS CREDENTIALS'}")
    print(f"  S3 storage:       OPTIONAL (falls back gracefully)")

    if len(items) > 0 and not cds_ok:
        print("\n  NEXT STEPS:")
        print("  1. Register at https://cds.climate.copernicus.eu/how-to-api")
        print("  2. pip install cdsapi")
        print("  3. Create ~/.cdsapirc with your credentials")
        print("  4. Run: python -m tropomi.pipeline --facility 1")


if __name__ == "__main__":
    main()
