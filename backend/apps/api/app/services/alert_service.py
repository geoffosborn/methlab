"""
Alert engine for methane monitoring.

Generates alerts based on:
    - Threshold exceedance: emission rate or intensity score above configured limits
    - New detection: first plume detected at a previously clean facility
    - NGER baseline breach: observed emissions exceed regulatory baseline
    - Trend: sustained increase in TROPOMI intensity over consecutive periods
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    THRESHOLD_EXCEEDANCE = "threshold_exceedance"
    NEW_DETECTION = "new_detection"
    NGER_BASELINE_BREACH = "nger_baseline_breach"
    TREND_INCREASE = "trend_increase"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AlertConfig:
    """Configurable thresholds for alert generation."""

    # S2 emission rate thresholds (kg/hr)
    emission_critical: float = 5000.0  # > 5 t/hr
    emission_high: float = 1000.0  # > 1 t/hr
    emission_medium: float = 200.0  # > 200 kg/hr

    # TROPOMI intensity score thresholds
    intensity_critical: float = 80.0
    intensity_high: float = 50.0
    intensity_medium: float = 25.0

    # NGER baseline breach margin (fraction above baseline)
    nger_breach_margin: float = 0.1  # 10% above baseline


def check_s2_detection_alerts(detection: dict, config: AlertConfig | None = None) -> list[dict]:
    """Check a new S2 detection against alert thresholds.

    Args:
        detection: S2 detection dict from pipeline
        config: Alert thresholds (default: AlertConfig())

    Returns:
        List of alert dicts to create
    """
    if config is None:
        config = AlertConfig()

    alerts = []
    emission = detection.get("emission_rate_kg_hr", 0) or 0
    facility_id = detection["facility_id"]

    # Threshold exceedance
    if emission >= config.emission_critical:
        severity = AlertSeverity.CRITICAL
    elif emission >= config.emission_high:
        severity = AlertSeverity.HIGH
    elif emission >= config.emission_medium:
        severity = AlertSeverity.MEDIUM
    else:
        severity = None

    if severity:
        alerts.append({
            "facility_id": facility_id,
            "alert_type": AlertType.THRESHOLD_EXCEEDANCE.value,
            "severity": severity.value,
            "title": f"Emission threshold exceeded: {emission:.0f} kg/hr",
            "description": (
                f"Sentinel-2 detected a methane plume with emission rate "
                f"{emission:.0f} kg/hr ({emission / 1000:.2f} t/hr). "
                f"Scene: {detection.get('scene_id', 'unknown')}. "
                f"Confidence: {detection.get('confidence', 'unknown')}."
            ),
            "metadata": {
                "emission_rate_kg_hr": emission,
                "scene_id": detection.get("scene_id"),
                "confidence": detection.get("confidence"),
            },
        })

    # New detection: check if this facility had no prior detections
    settings = get_settings()
    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT count(*) as cnt FROM s2_detections WHERE facility_id = %s",
                    [facility_id],
                )
                row = cur.fetchone()
                if row and row["cnt"] <= 1:  # This is the first detection
                    alerts.append({
                        "facility_id": facility_id,
                        "alert_type": AlertType.NEW_DETECTION.value,
                        "severity": AlertSeverity.MEDIUM.value,
                        "title": "First methane plume detected",
                        "description": (
                            f"First Sentinel-2 plume detection at this facility. "
                            f"Emission rate: {emission:.0f} kg/hr."
                        ),
                        "metadata": {"emission_rate_kg_hr": emission},
                    })
    except Exception as e:
        logger.warning("Failed to check prior detections: %s", e)

    return alerts


def check_tropomi_alerts(
    facility_id: int,
    intensity_score: float,
    config: AlertConfig | None = None,
) -> list[dict]:
    """Check TROPOMI intensity score against alert thresholds."""
    if config is None:
        config = AlertConfig()

    alerts = []

    if intensity_score >= config.intensity_critical:
        severity = AlertSeverity.CRITICAL
    elif intensity_score >= config.intensity_high:
        severity = AlertSeverity.HIGH
    elif intensity_score >= config.intensity_medium:
        severity = AlertSeverity.MEDIUM
    else:
        severity = None

    if severity:
        alerts.append({
            "facility_id": facility_id,
            "alert_type": AlertType.THRESHOLD_EXCEEDANCE.value,
            "severity": severity.value,
            "title": f"TROPOMI intensity score: {intensity_score:.0f}/100",
            "description": (
                f"TROPOMI wind-rotated CH4 screening shows elevated "
                f"methane signal with intensity score {intensity_score:.0f}/100."
            ),
            "metadata": {"intensity_score": intensity_score, "source": "tropomi"},
        })

    return alerts


def check_nger_baseline(
    facility_id: int,
    observed_annual_emissions_t: float,
    config: AlertConfig | None = None,
) -> list[dict]:
    """Check if observed emissions exceed NGER baseline."""
    if config is None:
        config = AlertConfig()

    settings = get_settings()
    alerts = []

    try:
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT nger_baseline FROM facilities WHERE id = %s",
                    [facility_id],
                )
                row = cur.fetchone()

                if row and row.get("nger_baseline"):
                    baseline = row["nger_baseline"]
                    breach_threshold = baseline * (1 + config.nger_breach_margin)

                    if observed_annual_emissions_t > breach_threshold:
                        exceedance_pct = (
                            (observed_annual_emissions_t - baseline) / baseline * 100
                        )
                        alerts.append({
                            "facility_id": facility_id,
                            "alert_type": AlertType.NGER_BASELINE_BREACH.value,
                            "severity": AlertSeverity.HIGH.value,
                            "title": f"NGER baseline exceeded by {exceedance_pct:.0f}%",
                            "description": (
                                f"Observed annual emissions ({observed_annual_emissions_t:.0f} t CO2-e) "
                                f"exceed NGER baseline ({baseline:.0f} t CO2-e) by "
                                f"{exceedance_pct:.1f}%. This may trigger Safeguard Mechanism obligations."
                            ),
                            "metadata": {
                                "observed_t": observed_annual_emissions_t,
                                "baseline_t": baseline,
                                "exceedance_pct": exceedance_pct,
                            },
                        })
    except Exception as e:
        logger.warning("Failed to check NGER baseline: %s", e)

    return alerts


def create_alerts(alerts: list[dict]):
    """Write alert records to the database."""
    if not alerts:
        return

    settings = get_settings()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            for alert in alerts:
                cur.execute(
                    """
                    INSERT INTO alerts (
                        facility_id, alert_type, severity, title, description, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    [
                        alert["facility_id"],
                        alert["alert_type"],
                        alert["severity"],
                        alert["title"],
                        alert["description"],
                        __import__("json").dumps(alert.get("metadata", {})),
                    ],
                )
            conn.commit()

    logger.info("Created %d alerts", len(alerts))


def acknowledge_alert(alert_id: int, acknowledged_by: str):
    """Mark an alert as acknowledged."""
    settings = get_settings()

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE alerts SET
                    acknowledged = true,
                    acknowledged_by = %s,
                    acknowledged_at = now()
                WHERE id = %s
                """,
                [acknowledged_by, alert_id],
            )
            conn.commit()
