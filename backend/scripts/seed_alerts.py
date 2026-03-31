"""
Seed alerts from NGER exceedance data and TROPOMI observations.

Generates:
  - nger_baseline_breach: for facilities exceeding their NGER baseline
  - threshold_exceedance: for facilities with high TROPOMI intensity scores
  - trend_increase: for facilities showing increasing emissions trend
"""

import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


def main():
    env_path = Path(__file__).parent.parent / "apps" / "api" / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "methlab")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")

    with psycopg.connect(
        host=db_host, port=int(db_port), dbname=db_name,
        user=db_user, password=db_password,
    ) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Clear existing alerts
            cur.execute("DELETE FROM alerts")
            print("Cleared existing alerts.")

            # Get facilities with NGER data
            cur.execute("""
                SELECT id, name, state, operator, metadata
                FROM facilities
                WHERE nger_id IS NOT NULL
                ORDER BY (metadata->>'nger_reported_2024')::int DESC
            """)
            facilities = cur.fetchall()
            print(f"Found {len(facilities)} NGER-mapped facilities")

            alert_count = 0
            now = datetime.now(timezone.utc)
            random.seed(42)

            for fac in facilities:
                meta = fac["metadata"] or {}
                baseline = meta.get("nger_baseline_2024", 0)
                reported = meta.get("nger_reported_2024", 0)

                if not baseline or not reported:
                    continue

                exceedance = reported - baseline
                exceedance_pct = (exceedance / baseline) * 100 if baseline else 0

                # NGER baseline breach alerts
                if exceedance > 0:
                    if exceedance_pct > 50:
                        severity = "critical"
                    elif exceedance_pct > 20:
                        severity = "high"
                    elif exceedance_pct > 5:
                        severity = "medium"
                    else:
                        severity = "low"

                    created = now - timedelta(
                        days=random.randint(1, 30),
                        hours=random.randint(0, 23),
                    )

                    cur.execute("""
                        INSERT INTO alerts (facility_id, alert_type, severity, title, description, metadata, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [
                        fac["id"],
                        "nger_baseline_breach",
                        severity,
                        f"{fac['name']}: NGER baseline exceeded by {exceedance_pct:.0f}%",
                        f"Reported emissions of {reported:,} tCO2e exceed the 2023-24 "
                        f"Safeguard baseline of {baseline:,} tCO2e by {exceedance:,} tCO2e "
                        f"({exceedance_pct:.1f}%). Under the reformed Safeguard Mechanism, "
                        f"this facility must surrender ACCUs or apply for a multi-year "
                        f"monitoring period.",
                        json.dumps({
                            "baseline_tco2e": baseline,
                            "reported_tco2e": reported,
                            "exceedance_tco2e": exceedance,
                            "exceedance_pct": round(exceedance_pct, 1),
                            "nger_emitter": meta.get("nger_emitter", ""),
                        }),
                        created,
                    ])
                    alert_count += 1
                    print(f"  BREACH {severity:8s}  {fac['name']:30s}  +{exceedance_pct:.0f}% ({exceedance:,} tCO2e)")

            # Get facilities with high TROPOMI scores for threshold alerts
            cur.execute("""
                SELECT DISTINCT ON (t.facility_id)
                       t.facility_id, f.name, f.state, t.intensity_score,
                       t.central_box_mean_ppb, t.period_start, t.period_end
                FROM tropomi_observations t
                JOIN facilities f ON f.id = t.facility_id
                WHERE t.intensity_score >= 70
                ORDER BY t.facility_id, t.period_start DESC
            """)
            high_tropomi = cur.fetchall()

            for obs in high_tropomi:
                severity = "critical" if obs["intensity_score"] >= 90 else "high"
                created = now - timedelta(
                    days=random.randint(1, 14),
                    hours=random.randint(0, 23),
                )

                cur.execute("""
                    INSERT INTO alerts (facility_id, alert_type, severity, title, description, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    obs["facility_id"],
                    "threshold_exceedance",
                    severity,
                    f"{obs['name']}: TROPOMI intensity score {obs['intensity_score']:.0f}",
                    f"Wind-rotated TROPOMI CH4 screening detected elevated methane "
                    f"enhancement of {obs['central_box_mean_ppb']:.0f} ppb above background "
                    f"at {obs['name']} ({obs['state']}). Intensity score: "
                    f"{obs['intensity_score']:.0f}/100. "
                    f"Period: {obs['period_start']} to {obs['period_end']}. "
                    f"Recommend Sentinel-2 SWIR follow-up for plume-level quantification.",
                    json.dumps({
                        "intensity_score": obs["intensity_score"],
                        "central_box_ppb": obs["central_box_mean_ppb"],
                        "period": f"{obs['period_start']} to {obs['period_end']}",
                    }),
                    created,
                ])
                alert_count += 1
                print(f"  TROPOMI {severity:8s}  {obs['name']:30s}  score={obs['intensity_score']:.0f}")

            # Trend increase alerts for top 5 facilities with biggest quarter-over-quarter increases
            cur.execute("""
                WITH ranked AS (
                    SELECT facility_id, period_start, central_box_mean_ppb,
                           LAG(central_box_mean_ppb) OVER (
                               PARTITION BY facility_id ORDER BY period_start
                           ) as prev_ppb
                    FROM tropomi_observations
                    WHERE aggregation_period = 'quarterly'
                )
                SELECT r.facility_id, f.name, f.state,
                       r.central_box_mean_ppb as current_ppb,
                       r.prev_ppb,
                       r.period_start,
                       ((r.central_box_mean_ppb - r.prev_ppb) / NULLIF(r.prev_ppb, 0) * 100) as pct_increase
                FROM ranked r
                JOIN facilities f ON f.id = r.facility_id
                WHERE r.prev_ppb IS NOT NULL
                  AND r.central_box_mean_ppb > r.prev_ppb * 1.15
                ORDER BY pct_increase DESC
                LIMIT 8
            """)
            trends = cur.fetchall()

            for trend in trends:
                pct = trend["pct_increase"]
                severity = "high" if pct > 40 else "medium"
                created = now - timedelta(
                    days=random.randint(3, 21),
                    hours=random.randint(0, 23),
                )

                cur.execute("""
                    INSERT INTO alerts (facility_id, alert_type, severity, title, description, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    trend["facility_id"],
                    "trend_increase",
                    severity,
                    f"{trend['name']}: CH4 enhancement increased {pct:.0f}% quarter-over-quarter",
                    f"TROPOMI central box enhancement at {trend['name']} increased from "
                    f"{trend['prev_ppb']:.0f} ppb to {trend['current_ppb']:.0f} ppb "
                    f"({pct:.0f}% increase). This may indicate new or worsening fugitive "
                    f"emissions sources. Recommend site investigation.",
                    json.dumps({
                        "current_ppb": round(trend["current_ppb"], 1),
                        "previous_ppb": round(trend["prev_ppb"], 1),
                        "pct_increase": round(pct, 1),
                    }),
                    created,
                ])
                alert_count += 1
                print(f"  TREND  {severity:8s}  {trend['name']:30s}  +{pct:.0f}%")

            conn.commit()

            # Summary
            cur.execute("""
                SELECT severity, count(*) as cnt
                FROM alerts
                GROUP BY severity
                ORDER BY CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                END
            """)
            summary = cur.fetchall()

            print(f"\nDone. {alert_count} alerts created:")
            for row in summary:
                print(f"  {row['severity']:10s}: {row['cnt']}")


if __name__ == "__main__":
    main()
