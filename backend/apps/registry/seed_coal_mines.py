"""
Seed Australian coal mine facilities into the database.

Sources:
- Geoscience Australia Australian Mines Atlas
- Queensland Government mining tenements
- NSW Resources Regulator
- NGER reporting data (Clean Energy Regulator)

Coordinates sourced from public mine location datasets.
"""

import json
import sys

import psycopg
from psycopg.rows import dict_row

# fmt: off
AUSTRALIAN_COAL_MINES: list[dict] = [
    # === QUEENSLAND - Bowen Basin ===
    {"name": "Moranbah North", "state": "QLD", "operator": "Anglo American", "lat": -22.0833, "lon": 148.0500, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Grosvenor", "state": "QLD", "operator": "Anglo American", "lat": -22.1167, "lon": 148.1333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Grasstree", "state": "QLD", "operator": "Anglo American", "lat": -22.0500, "lon": 148.1167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Capcoal (Aquila)", "state": "QLD", "operator": "Anglo American", "lat": -23.1000, "lon": 148.3167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Dawson", "state": "QLD", "operator": "Anglo American", "lat": -23.6833, "lon": 149.3333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Hail Creek", "state": "QLD", "operator": "Glencore", "lat": -21.5167, "lon": 148.3667, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Goonyella Riverside", "state": "QLD", "operator": "BHP", "lat": -21.8167, "lon": 148.1167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Peak Downs", "state": "QLD", "operator": "BHP", "lat": -22.2500, "lon": 148.1833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Saraji", "state": "QLD", "operator": "BHP", "lat": -22.4167, "lon": 148.1333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Broadmeadow", "state": "QLD", "operator": "BHP", "lat": -21.8500, "lon": 148.0833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Caval Ridge", "state": "QLD", "operator": "BHP", "lat": -22.0667, "lon": 148.1500, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Daunia", "state": "QLD", "operator": "BHP", "lat": -22.0167, "lon": 148.1000, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Blackwater", "state": "QLD", "operator": "BHP", "lat": -23.5333, "lon": 148.8833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "South Walker Creek", "state": "QLD", "operator": "BHP", "lat": -21.8000, "lon": 148.4500, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Poitrel", "state": "QLD", "operator": "BHP", "lat": -21.8333, "lon": 148.4333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Curragh", "state": "QLD", "operator": "Coronado Global Resources", "lat": -23.4500, "lon": 148.9500, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Oaky Creek", "state": "QLD", "operator": "Glencore", "lat": -22.7333, "lon": 148.4167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Rolleston", "state": "QLD", "operator": "Glencore", "lat": -24.3833, "lon": 148.6333, "commodity": "thermal coal", "status": "active"},
    {"name": "Clermont", "state": "QLD", "operator": "Glencore", "lat": -22.7500, "lon": 147.6333, "commodity": "thermal coal", "status": "active"},
    {"name": "Collinsville", "state": "QLD", "operator": "Glencore", "lat": -20.5500, "lon": 147.8500, "commodity": "thermal coal", "status": "active"},
    {"name": "Newlands", "state": "QLD", "operator": "Glencore", "lat": -21.1833, "lon": 148.1333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Coppabella", "state": "QLD", "operator": "Peabody Energy", "lat": -21.9500, "lon": 148.2333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Moorvale", "state": "QLD", "operator": "Peabody Energy", "lat": -22.0000, "lon": 148.2000, "commodity": "metallurgical coal", "status": "active"},
    {"name": "North Goonyella", "state": "QLD", "operator": "Peabody Energy", "lat": -21.7333, "lon": 148.1000, "commodity": "metallurgical coal", "status": "care_and_maintenance"},
    {"name": "Middlemount", "state": "QLD", "operator": "Peabody/Yancoal", "lat": -22.8000, "lon": 148.6833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Isaac Plains", "state": "QLD", "operator": "Stanmore Resources", "lat": -22.1667, "lon": 148.2167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Lake Vermont", "state": "QLD", "operator": "Bowen Coking Coal", "lat": -22.4833, "lon": 148.3333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Foxleigh", "state": "QLD", "operator": "Realm Resources", "lat": -22.7833, "lon": 148.5000, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Jellinbah", "state": "QLD", "operator": "Jellinbah Group", "lat": -23.3667, "lon": 148.7500, "commodity": "metallurgical coal", "status": "active"},
    {"name": "German Creek (Aquila)", "state": "QLD", "operator": "Anglo American", "lat": -23.0833, "lon": 148.2833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Carborough Downs", "state": "QLD", "operator": "Fitzroy Australia Resources", "lat": -22.1000, "lon": 148.2333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Cook", "state": "QLD", "operator": "Yancoal", "lat": -23.4667, "lon": 148.7667, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Millennium", "state": "QLD", "operator": "Peabody Energy", "lat": -22.1667, "lon": 148.1833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Burton", "state": "QLD", "operator": "Peabody Energy", "lat": -21.9833, "lon": 148.1333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Kestrel", "state": "QLD", "operator": "EMR Capital/Adaro", "lat": -23.4833, "lon": 148.5500, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Ensham", "state": "QLD", "operator": "Idemitsu", "lat": -23.4333, "lon": 148.3333, "commodity": "thermal coal", "status": "active"},
    {"name": "Yarrabee", "state": "QLD", "operator": "Yancoal", "lat": -23.3167, "lon": 148.6667, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Gregory Crinum", "state": "QLD", "operator": "Sojitz", "lat": -23.2167, "lon": 148.5333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "South Blackwater (Bluff)", "state": "QLD", "operator": "BHP", "lat": -23.6167, "lon": 149.0167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Minerva", "state": "QLD", "operator": "Stanmore Resources", "lat": -22.1333, "lon": 148.2500, "commodity": "metallurgical coal", "status": "active"},

    # === QUEENSLAND - Surat Basin ===
    {"name": "New Acland", "state": "QLD", "operator": "New Hope Group", "lat": -27.3167, "lon": 151.6833, "commodity": "thermal coal", "status": "active"},
    {"name": "Cameby Downs", "state": "QLD", "operator": "Yancoal", "lat": -26.5167, "lon": 150.3667, "commodity": "thermal coal", "status": "active"},
    {"name": "Commodore", "state": "QLD", "operator": "Intergen", "lat": -26.8000, "lon": 150.9167, "commodity": "thermal coal", "status": "active"},

    # === QUEENSLAND - Other ===
    {"name": "Meandu (Tarong)", "state": "QLD", "operator": "Stanwell", "lat": -26.7833, "lon": 151.9167, "commodity": "thermal coal", "status": "active"},
    {"name": "Callide", "state": "QLD", "operator": "Batchfire Resources", "lat": -24.3833, "lon": 150.5167, "commodity": "thermal coal", "status": "active"},
    {"name": "Baralaba", "state": "QLD", "operator": "Baralaba Coal", "lat": -24.1667, "lon": 149.6167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Blair Athol", "state": "QLD", "operator": "TerraCom", "lat": -22.6500, "lon": 147.5667, "commodity": "thermal coal", "status": "active"},
    {"name": "Sonoma", "state": "QLD", "operator": "ATEC Resources", "lat": -20.6833, "lon": 147.8667, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Byerwen", "state": "QLD", "operator": "QCoal", "lat": -21.2167, "lon": 148.3000, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Meteor Downs South", "state": "QLD", "operator": "Meteor Downs South", "lat": -24.0667, "lon": 148.6000, "commodity": "thermal coal", "status": "active"},
    {"name": "Mackenzie", "state": "QLD", "operator": "Pembroke Resources", "lat": -22.7667, "lon": 148.5333, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Olive Downs", "state": "QLD", "operator": "Pembroke Resources", "lat": -22.5500, "lon": 148.3833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Vulcan", "state": "QLD", "operator": "Vitrinite", "lat": -22.0500, "lon": 148.3000, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Lenton", "state": "QLD", "operator": "Jellinbah Group", "lat": -23.4000, "lon": 148.7833, "commodity": "metallurgical coal", "status": "active"},

    # === NEW SOUTH WALES - Hunter Valley ===
    {"name": "Mount Arthur", "state": "NSW", "operator": "BHP", "lat": -32.3333, "lon": 150.8667, "commodity": "thermal coal", "status": "active"},
    {"name": "Wambo", "state": "NSW", "operator": "Peabody Energy", "lat": -32.5167, "lon": 150.9500, "commodity": "thermal coal", "status": "active"},
    {"name": "Hunter Valley Operations", "state": "NSW", "operator": "Yancoal", "lat": -32.3667, "lon": 151.0667, "commodity": "thermal coal", "status": "active"},
    {"name": "Mount Pleasant", "state": "NSW", "operator": "MACH Energy", "lat": -32.2500, "lon": 150.8667, "commodity": "thermal coal", "status": "active"},
    {"name": "Bengalla", "state": "NSW", "operator": "New Hope Group", "lat": -32.3000, "lon": 150.8500, "commodity": "thermal coal", "status": "active"},
    {"name": "Mangoola", "state": "NSW", "operator": "Glencore", "lat": -32.2167, "lon": 150.7000, "commodity": "thermal coal", "status": "active"},
    {"name": "Liddell", "state": "NSW", "operator": "Glencore", "lat": -32.3667, "lon": 150.9500, "commodity": "thermal coal", "status": "active"},
    {"name": "Ravensworth", "state": "NSW", "operator": "Glencore", "lat": -32.4167, "lon": 151.0000, "commodity": "thermal coal", "status": "active"},
    {"name": "United (Warkworth)", "state": "NSW", "operator": "Yancoal", "lat": -32.5000, "lon": 151.0500, "commodity": "thermal coal", "status": "active"},
    {"name": "Bulga", "state": "NSW", "operator": "Glencore", "lat": -32.6500, "lon": 151.0667, "commodity": "thermal coal", "status": "active"},
    {"name": "Rix's Creek", "state": "NSW", "operator": "The Bloomfield Group", "lat": -32.3833, "lon": 151.0667, "commodity": "thermal coal", "status": "active"},
    {"name": "Integra", "state": "NSW", "operator": "Glencore", "lat": -32.5167, "lon": 150.9667, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Ashton", "state": "NSW", "operator": "Yancoal", "lat": -32.4167, "lon": 151.0500, "commodity": "thermal coal", "status": "active"},
    {"name": "Glendell", "state": "NSW", "operator": "Glencore", "lat": -32.3500, "lon": 151.0167, "commodity": "thermal coal", "status": "active"},
    {"name": "Muswellbrook", "state": "NSW", "operator": "Idemitsu", "lat": -32.2833, "lon": 150.8833, "commodity": "thermal coal", "status": "active"},
    {"name": "Maxwell", "state": "NSW", "operator": "Malabar Resources", "lat": -32.3500, "lon": 150.8333, "commodity": "metallurgical coal", "status": "active"},

    # === NEW SOUTH WALES - Western Coalfields ===
    {"name": "Springvale", "state": "NSW", "operator": "Centennial Coal", "lat": -33.4500, "lon": 150.0500, "commodity": "thermal coal", "status": "active"},
    {"name": "Angus Place", "state": "NSW", "operator": "Centennial Coal", "lat": -33.4167, "lon": 150.0333, "commodity": "thermal coal", "status": "care_and_maintenance"},
    {"name": "Clarence", "state": "NSW", "operator": "Centennial Coal", "lat": -33.4667, "lon": 150.1833, "commodity": "thermal coal", "status": "active"},
    {"name": "Airly", "state": "NSW", "operator": "Centennial Coal", "lat": -33.3333, "lon": 150.0333, "commodity": "thermal coal", "status": "active"},

    # === NEW SOUTH WALES - Newcastle/Maitland ===
    {"name": "Myuna", "state": "NSW", "operator": "Centennial Coal", "lat": -33.0833, "lon": 151.5500, "commodity": "thermal coal", "status": "active"},
    {"name": "Mandalong", "state": "NSW", "operator": "Centennial Coal", "lat": -33.1000, "lon": 151.5000, "commodity": "thermal coal", "status": "active"},
    {"name": "Abel", "state": "NSW", "operator": "Yancoal", "lat": -32.8833, "lon": 151.4167, "commodity": "thermal coal", "status": "active"},
    {"name": "Austar", "state": "NSW", "operator": "Yancoal", "lat": -32.9167, "lon": 151.4000, "commodity": "thermal coal", "status": "active"},
    {"name": "Donaldson", "state": "NSW", "operator": "Yancoal", "lat": -32.7333, "lon": 151.5167, "commodity": "thermal coal", "status": "active"},
    {"name": "Chain Valley", "state": "NSW", "operator": "Delta Coal", "lat": -33.1833, "lon": 151.5333, "commodity": "thermal coal", "status": "active"},

    # === NEW SOUTH WALES - Gunnedah Basin ===
    {"name": "Werris Creek", "state": "NSW", "operator": "Whitehaven Coal", "lat": -31.3333, "lon": 150.6667, "commodity": "thermal coal", "status": "active"},
    {"name": "Maules Creek", "state": "NSW", "operator": "Whitehaven Coal", "lat": -30.5500, "lon": 149.8333, "commodity": "thermal coal", "status": "active"},
    {"name": "Narrabri", "state": "NSW", "operator": "Whitehaven Coal", "lat": -30.2667, "lon": 149.6167, "commodity": "thermal coal", "status": "active"},
    {"name": "Tarrawonga", "state": "NSW", "operator": "Whitehaven Coal", "lat": -30.5667, "lon": 149.8500, "commodity": "thermal coal", "status": "active"},
    {"name": "Rocglen", "state": "NSW", "operator": "Whitehaven Coal", "lat": -30.6000, "lon": 149.8667, "commodity": "thermal coal", "status": "active"},
    {"name": "Vickery", "state": "NSW", "operator": "Whitehaven Coal", "lat": -30.5333, "lon": 149.8167, "commodity": "thermal coal", "status": "active"},
    {"name": "Boggabri", "state": "NSW", "operator": "Idemitsu", "lat": -30.6333, "lon": 149.9000, "commodity": "thermal coal", "status": "active"},

    # === NEW SOUTH WALES - Illawarra ===
    {"name": "Appin", "state": "NSW", "operator": "South32", "lat": -34.2000, "lon": 150.7833, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Dendrobium", "state": "NSW", "operator": "South32", "lat": -34.3833, "lon": 150.8167, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Russell Vale", "state": "NSW", "operator": "Wollongong Coal", "lat": -34.3667, "lon": 150.8500, "commodity": "metallurgical coal", "status": "active"},
    {"name": "Wongawilli", "state": "NSW", "operator": "Wollongong Coal", "lat": -34.4167, "lon": 150.8167, "commodity": "metallurgical coal", "status": "care_and_maintenance"},
    {"name": "NRE No. 1", "state": "NSW", "operator": "Wollongong Coal", "lat": -34.4333, "lon": 150.8167, "commodity": "metallurgical coal", "status": "active"},

    # === NEW SOUTH WALES - Other ===
    {"name": "Stratford/Duralie", "state": "NSW", "operator": "Yancoal", "lat": -32.1000, "lon": 151.9833, "commodity": "thermal coal", "status": "active"},
    {"name": "Moolarben", "state": "NSW", "operator": "Yancoal", "lat": -32.2833, "lon": 149.7167, "commodity": "thermal coal", "status": "active"},
    {"name": "Wilpinjong", "state": "NSW", "operator": "Peabody Energy", "lat": -32.3000, "lon": 149.6667, "commodity": "thermal coal", "status": "active"},
    {"name": "Ulan", "state": "NSW", "operator": "Glencore", "lat": -32.2667, "lon": 149.7333, "commodity": "thermal coal", "status": "active"},

    # === VICTORIA ===
    {"name": "Loy Yang", "state": "VIC", "operator": "AGL Energy", "lat": -38.2667, "lon": 146.5500, "commodity": "brown coal", "status": "active"},
    {"name": "Yallourn", "state": "VIC", "operator": "EnergyAustralia", "lat": -38.1833, "lon": 146.3500, "commodity": "brown coal", "status": "active"},
    {"name": "Hazelwood", "state": "VIC", "operator": "ENGIE", "lat": -38.2833, "lon": 146.3833, "commodity": "brown coal", "status": "closed"},

    # === WESTERN AUSTRALIA ===
    {"name": "Collie (Premier)", "state": "WA", "operator": "Premier Coal", "lat": -33.3667, "lon": 116.1500, "commodity": "thermal coal", "status": "active"},
    {"name": "Collie (Griffin)", "state": "WA", "operator": "Griffin Coal", "lat": -33.3833, "lon": 116.1667, "commodity": "thermal coal", "status": "active"},

    # === SOUTH AUSTRALIA ===
    {"name": "Leigh Creek", "state": "SA", "operator": "Alinta Energy", "lat": -30.5833, "lon": 138.5000, "commodity": "brown coal", "status": "closed"},

    # === TASMANIA ===
    {"name": "Fingal", "state": "TAS", "operator": "Cornwall Coal", "lat": -41.6333, "lon": 147.9833, "commodity": "thermal coal", "status": "active"},
]
# fmt: on


def seed_facilities(conn_string: str, dry_run: bool = False) -> int:
    """Insert coal mine facilities into the database.

    Returns the number of facilities inserted.
    """
    inserted = 0

    with psycopg.connect(conn_string) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            for mine in AUSTRALIAN_COAL_MINES:
                # Check if already exists by name + state
                cur.execute(
                    "SELECT id FROM facilities WHERE name = %s AND state = %s",
                    [mine["name"], mine["state"]],
                )
                if cur.fetchone():
                    print(f"  SKIP (exists): {mine['name']}, {mine['state']}")
                    continue

                if dry_run:
                    print(f"  DRY RUN: {mine['name']}, {mine['state']}")
                    inserted += 1
                    continue

                point_wkt = f"SRID=4326;POINT({mine['lon']} {mine['lat']})"

                cur.execute(
                    """
                    INSERT INTO facilities (name, facility_type, state, operator, commodity,
                                            centroid, status, metadata)
                    VALUES (%s, %s, %s, %s, %s,
                            ST_GeogFromText(%s), %s, %s)
                    """,
                    [
                        mine["name"],
                        "coal_mine",
                        mine["state"],
                        mine.get("operator"),
                        mine.get("commodity"),
                        point_wkt,
                        mine.get("status", "active"),
                        json.dumps({}),
                    ],
                )
                inserted += 1
                print(f"  INSERT: {mine['name']}, {mine['state']} ({mine['operator']})")

            if not dry_run:
                conn.commit()

    return inserted


def main():
    import os

    from dotenv import load_dotenv

    load_dotenv()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "methlab")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")

    conn_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}"

    dry_run = "--dry-run" in sys.argv

    print(f"Seeding Australian coal mines into {db_name}...")
    if dry_run:
        print("(DRY RUN - no changes will be made)")

    count = seed_facilities(conn_string, dry_run=dry_run)
    print(f"\nDone. {count} facilities {'would be ' if dry_run else ''}inserted.")
    print(f"Total in seed data: {len(AUSTRALIAN_COAL_MINES)}")


if __name__ == "__main__":
    main()
