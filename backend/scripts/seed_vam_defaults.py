"""
Seed VAM (Ventilation Air Methane) defaults into WellKnown facility_link metadata.

Pre-populates the material balance VAM term with realistic values derived from:
  - Sadavarte et al. 2021 TROPOMI cluster emissions (190/150 Gg/yr)
  - CSIRO CataVAM field trials (0.15-0.5% CH4)
  - EPA CMM Primer ventilation flow rates (142-566 m3/s)
  - Anglo American ESG disclosures (60% drainage abatement)

These defaults enable the WellKnown material balance waterfall to show the
VAM term without requiring manual configuration per mine.

Run against the tempo database (WellKnown):
  python scripts/seed_vam_defaults.py
"""

import json
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

# VAM defaults per mine, derived from published literature
# Flow rates in m3/s, CH4 concentration in %, observation period in months
VAM_DEFAULTS = {
    "Moranbah North": {
        "vam_flow_rate_m3s": 200,
        "vam_ch4_pct": 0.35,
        "vam_months": 12,
        "vam_source": "Derived from Sadavarte 2021 S2 cluster (190 Gg/yr, 3 mines), CSIRO field data",
        "nger_tco2e_annual": 1_300_000,
    },
    "Grosvenor": {
        "vam_flow_rate_m3s": 220,
        "vam_ch4_pct": 0.40,
        "vam_months": 12,
        "vam_source": "Derived from Sadavarte 2021 S2 cluster, EDL 36.5MW gas power = high gas make",
        "nger_tco2e_annual": 1_700_000,
    },
    "Grasstree": {
        "vam_flow_rate_m3s": 250,
        "vam_ch4_pct": 0.45,
        "vam_months": 12,
        "vam_source": "Derived from Sadavarte 2021 S3 cluster (150 Gg/yr, 2 mines), German Creek seam super-emitter",
        "nger_tco2e_annual": 1_800_000,
    },
    "Broadmeadow": {
        "vam_flow_rate_m3s": 180,
        "vam_ch4_pct": 0.30,
        "vam_months": 12,
        "vam_source": "Derived from Sadavarte 2021 S2 cluster, moderate depth Goonyella Middle seam",
        "nger_tco2e_annual": 800_000,
    },
    "North Goonyella": {
        "vam_flow_rate_m3s": 150,
        "vam_ch4_pct": 0.35,
        "vam_months": 12,
        "vam_source": "Estimated from reduced operations post-2018 fire, Goonyella Middle seam",
        "nger_tco2e_annual": 600_000,
    },
    "Oaky North": {
        "vam_flow_rate_m3s": 200,
        "vam_ch4_pct": 0.40,
        "vam_months": 12,
        "vam_source": "Derived from Sadavarte 2021 S3 cluster, German Creek seam, identified super-emitter",
        "nger_tco2e_annual": 1_200_000,
    },
}


def main():
    env_path = Path(__file__).parent.parent / "apps" / "wellknown" / ".env"
    if not env_path.exists():
        env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    # Connect to WellKnown's tempo database
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "tempo")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "")

    conn_str = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_pass}"

    with psycopg.connect(conn_str, row_factory=dict_row) as conn:
        # Check if facility_link table exists
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'wellknown'
                    AND table_name = 'facility_link'
                )
            """)
            if not cur.fetchone()["exists"]:
                print("ERROR: wellknown.facility_link table does not exist.")
                print("Run migrations/004_facility_link.sql first.")
                sys.exit(1)

        # Get existing facility links
        with conn.cursor() as cur:
            cur.execute("SELECT id, facility_name, metadata FROM wellknown.facility_link")
            links = cur.fetchall()

        if not links:
            print("No facility links found. Link facilities first via the WellKnown UI or API.")
            print("Available VAM defaults for: " + ", ".join(VAM_DEFAULTS.keys()))
            sys.exit(0)

        updated = 0
        for link in links:
            name = link["facility_name"]
            if name not in VAM_DEFAULTS:
                print(f"  SKIP {name}: no VAM defaults available")
                continue

            defaults = VAM_DEFAULTS[name]
            existing_meta = link.get("metadata") or {}

            # Don't overwrite if already configured
            if existing_meta.get("vam_flow_rate_m3s"):
                print(f"  SKIP {name}: VAM already configured (flow={existing_meta['vam_flow_rate_m3s']} m3/s)")
                continue

            # Merge defaults into metadata
            new_meta = {**existing_meta, **defaults}

            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE wellknown.facility_link SET metadata = %s::jsonb WHERE id = %s",
                    [json.dumps(new_meta), link["id"]],
                )
            conn.commit()

            vam_t_hr = (
                defaults["vam_flow_rate_m3s"]
                * (defaults["vam_ch4_pct"] / 100)
                * 0.668  # CH4 density kg/m3
                * 3.6  # seconds to hours factor (×3600/1000 for t/hr)
            )
            print(
                f"  {name}: flow={defaults['vam_flow_rate_m3s']} m3/s, "
                f"CH4={defaults['vam_ch4_pct']}%, "
                f"~{vam_t_hr:.1f} t/hr VAM emissions"
            )
            updated += 1

        print(f"\nUpdated {updated} facility links with VAM defaults")


if __name__ == "__main__":
    main()
