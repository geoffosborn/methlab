"""
DEKS integration API routes.

Provides endpoints for DEKS to query methane emissions data
by geographic bounds (project area). Used by the DEKS Container
to render the methane monitoring dashboard within a project context.
"""

import json
import logging

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from app.database import db_execute

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deks", tags=["deks"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class FacilitySummary(BaseModel):
    id: int
    name: str
    facility_type: str
    state: str | None = None
    operator: str | None = None
    latitude: float
    longitude: float
    status: str = "active"
    nger_id: str | None = None
    commodity: str | None = None


class TropomiPoint(BaseModel):
    period_start: str
    period_end: str
    mean_enhancement_ppb: float | None = None
    max_enhancement_ppb: float | None = None
    central_box_mean_ppb: float | None = None
    intensity_score: float | None = None
    sample_count: int | None = None
    mean_wind_speed: float | None = None
    viz_s3_key: str | None = None


class Detection(BaseModel):
    id: int
    scene_datetime: str
    emission_rate_kg_hr: float | None = None
    emission_rate_t_hr: float | None = None
    plume_length_m: float | None = None
    plume_area_m2: float | None = None
    confidence: str | None = None
    wind_speed_10m: float | None = None
    wind_direction: float | None = None


class AlertSummary(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    description: str | None = None
    acknowledged: bool = False
    created_at: str


class ComplianceSummary(BaseModel):
    nger_id: str | None = None
    nger_baseline: float | None = None
    latest_annual_intensity: float | None = None
    baseline_exceedance_pct: float | None = None
    status: str  # "compliant", "warning", "breach", "no_baseline"


class EmissionsTrend(BaseModel):
    direction: str  # "increasing", "decreasing", "stable", "insufficient_data"
    change_pct: float | None = None
    periods_compared: int = 0


class FacilityDashboard(BaseModel):
    facility: FacilitySummary
    tropomi_trend: list[TropomiPoint]
    latest_tropomi: TropomiPoint | None = None
    recent_detections: list[Detection]
    active_alerts: list[AlertSummary]
    compliance: ComplianceSummary
    trend: EmissionsTrend
    total_detections: int = 0
    detection_rate_per_year: float | None = None


class ProjectEmissionsResponse(BaseModel):
    """Full emissions payload for a DEKS project area."""
    matched_facilities: int
    facilities: list[FacilityDashboard]
    area_summary: dict  # aggregate stats across all matched facilities


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_bounds(bounds: str) -> str:
    """Parse bounds parameter into a PostGIS-compatible geometry.

    Accepts:
    - bbox string: "west,south,east,north"
    - GeoJSON geometry string: '{"type":"Polygon","coordinates":...}'

    Returns an EWKT string for use in ST_GeomFromEWKT / ST_GeomFromGeoJSON.
    """
    bounds = bounds.strip()

    # Try as GeoJSON
    if bounds.startswith("{"):
        try:
            geojson = json.loads(bounds)
            if "type" in geojson:
                return bounds  # return raw GeoJSON for ST_GeomFromGeoJSON
        except json.JSONDecodeError:
            pass

    # Try as bbox
    try:
        parts = [float(x.strip()) for x in bounds.split(",")]
        if len(parts) == 4:
            west, south, east, north = parts
            return json.dumps({
                "type": "Polygon",
                "coordinates": [[
                    [west, south], [east, south],
                    [east, north], [west, north],
                    [west, south],
                ]],
            })
    except ValueError:
        pass

    raise HTTPException(
        status_code=400,
        detail="bounds must be bbox (west,south,east,north) or GeoJSON geometry",
    )


def _compute_trend(tropomi_points: list[dict]) -> dict:
    """Compute emissions trend from TROPOMI time series."""
    scored = [p for p in tropomi_points if p.get("intensity_score") is not None]
    if len(scored) < 3:
        return {"direction": "insufficient_data", "change_pct": None, "periods_compared": len(scored)}

    # Compare average of most recent 2 vs oldest 2
    recent = sum(p["intensity_score"] for p in scored[:2]) / 2
    older = sum(p["intensity_score"] for p in scored[-2:]) / 2

    if older == 0:
        return {"direction": "stable", "change_pct": 0, "periods_compared": len(scored)}

    change_pct = ((recent - older) / older) * 100

    if change_pct > 15:
        direction = "increasing"
    elif change_pct < -15:
        direction = "decreasing"
    else:
        direction = "stable"

    return {
        "direction": direction,
        "change_pct": round(change_pct, 1),
        "periods_compared": len(scored),
    }


def _compute_compliance(facility: dict, tropomi_points: list[dict]) -> dict:
    """Compute NGER compliance status."""
    nger_id = facility.get("nger_id")
    nger_baseline = facility.get("nger_baseline")

    if not nger_baseline:
        return {
            "nger_id": nger_id,
            "nger_baseline": None,
            "latest_annual_intensity": None,
            "baseline_exceedance_pct": None,
            "status": "no_baseline",
        }

    # Find latest annual or use latest quarterly as proxy
    annual = [p for p in tropomi_points if p.get("aggregation_period") == "annual"]
    if annual:
        latest_intensity = annual[0].get("intensity_score")
    elif tropomi_points:
        latest_intensity = tropomi_points[0].get("intensity_score")
    else:
        latest_intensity = None

    if latest_intensity is None:
        return {
            "nger_id": nger_id,
            "nger_baseline": nger_baseline,
            "latest_annual_intensity": None,
            "baseline_exceedance_pct": None,
            "status": "no_baseline",
        }

    exceedance = ((latest_intensity - nger_baseline) / nger_baseline) * 100 if nger_baseline > 0 else 0

    if exceedance > 10:
        status = "breach"
    elif exceedance > 0:
        status = "warning"
    else:
        status = "compliant"

    return {
        "nger_id": nger_id,
        "nger_baseline": nger_baseline,
        "latest_annual_intensity": latest_intensity,
        "baseline_exceedance_pct": round(exceedance, 1),
        "status": status,
    }


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------


@router.get("/project-emissions", response_model=ProjectEmissionsResponse)
async def get_project_emissions(
    bounds: str | None = Query(
        None,
        description="Project area as bbox (west,south,east,north) or GeoJSON geometry",
    ),
    quarters: int = Query(12, ge=1, le=40, description="Number of quarters of history"),
    detection_limit: int = Query(20, ge=1, le=100, description="Max recent detections per facility"),
    x_deks_project_bounds: str | None = Header(None),
):
    """
    Get comprehensive methane emissions data for a DEKS project area.

    Matches methlab facilities whose centroid falls within the given bounds,
    then returns TROPOMI trends, S2 detections, alerts, and compliance
    status for each matched facility.
    """
    # Accept bounds from query param or X-DEKS-Project-Bounds header
    effective_bounds = bounds or x_deks_project_bounds
    if not effective_bounds:
        raise HTTPException(status_code=400, detail="bounds query param or X-DEKS-Project-Bounds header required")
    geojson_str = _parse_bounds(effective_bounds)

    # Find facilities within bounds
    facility_rows = db_execute(
        """
        SELECT id, name, facility_type, state, operator,
               ST_Y(centroid::geometry) as latitude,
               ST_X(centroid::geometry) as longitude,
               nger_id, nger_baseline, status, commodity
        FROM facilities
        WHERE ST_Intersects(
            centroid,
            ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
        )
        ORDER BY name
        """,
        [geojson_str],
    )

    if not facility_rows:
        return ProjectEmissionsResponse(
            matched_facilities=0,
            facilities=[],
            area_summary={
                "total_facilities": 0,
                "total_detections": 0,
                "max_intensity": None,
                "facilities_with_alerts": 0,
            },
        )

    dashboards = []
    total_detections_all = 0
    max_intensity_all = None
    facilities_with_alerts = 0

    for fac in facility_rows:
        fac_id = fac["id"]

        # TROPOMI quarterly trend
        tropomi_rows = db_execute(
            """
            SELECT period_start::text, period_end::text,
                   mean_enhancement_ppb, max_enhancement_ppb,
                   central_box_mean_ppb, intensity_score,
                   sample_count, mean_wind_speed, viz_s3_key,
                   aggregation_period
            FROM tropomi_observations
            WHERE facility_id = %s AND aggregation_period = 'quarterly'
            ORDER BY period_start DESC
            LIMIT %s
            """,
            [fac_id, quarters],
        )

        tropomi_points = [
            TropomiPoint(
                period_start=r["period_start"],
                period_end=r["period_end"],
                mean_enhancement_ppb=r["mean_enhancement_ppb"],
                max_enhancement_ppb=r["max_enhancement_ppb"],
                central_box_mean_ppb=r["central_box_mean_ppb"],
                intensity_score=r["intensity_score"],
                sample_count=r["sample_count"],
                mean_wind_speed=r["mean_wind_speed"],
                viz_s3_key=r["viz_s3_key"],
            )
            for r in (tropomi_rows or [])
        ]

        latest_tropomi = tropomi_points[0] if tropomi_points else None

        # Track max intensity across area
        if latest_tropomi and latest_tropomi.intensity_score is not None:
            if max_intensity_all is None or latest_tropomi.intensity_score > max_intensity_all:
                max_intensity_all = latest_tropomi.intensity_score

        # Recent S2 detections
        detection_rows = db_execute(
            """
            SELECT id, scene_datetime::text,
                   emission_rate_kg_hr,
                   emission_rate_kg_hr / 1000.0 as emission_rate_t_hr,
                   plume_length_m, plume_area_m2,
                   confidence, wind_speed_10m, wind_direction
            FROM s2_detections
            WHERE facility_id = %s
            ORDER BY scene_datetime DESC
            LIMIT %s
            """,
            [fac_id, detection_limit],
        )

        detections = [Detection(**r) for r in (detection_rows or [])]

        # Total detection count
        det_count_row = db_execute(
            "SELECT count(*) as cnt FROM s2_detections WHERE facility_id = %s",
            [fac_id],
            fetch="one",
        )
        total_det = det_count_row["cnt"] if det_count_row else 0
        total_detections_all += total_det

        # Detection rate (per year)
        det_rate_row = db_execute(
            """
            SELECT count(*) as cnt,
                   EXTRACT(EPOCH FROM (max(scene_datetime) - min(scene_datetime))) / 86400.0 as span_days
            FROM s2_detections
            WHERE facility_id = %s
            """,
            [fac_id],
            fetch="one",
        )
        detection_rate = None
        if det_rate_row and det_rate_row["span_days"] and det_rate_row["span_days"] > 30:
            detection_rate = round(det_rate_row["cnt"] / (det_rate_row["span_days"] / 365.25), 1)

        # Active (unacknowledged) alerts
        alert_rows = db_execute(
            """
            SELECT id, alert_type, severity, title, description,
                   acknowledged, created_at::text
            FROM alerts
            WHERE facility_id = %s AND acknowledged = false
            ORDER BY created_at DESC
            LIMIT 10
            """,
            [fac_id],
        )

        alerts = [AlertSummary(**r) for r in (alert_rows or [])]
        if alerts:
            facilities_with_alerts += 1

        # Compliance
        compliance = _compute_compliance(fac, tropomi_rows or [])

        # Trend
        trend = _compute_trend(tropomi_rows or [])

        dashboards.append(
            FacilityDashboard(
                facility=FacilitySummary(
                    id=fac["id"],
                    name=fac["name"],
                    facility_type=fac["facility_type"],
                    state=fac["state"],
                    operator=fac["operator"],
                    latitude=fac["latitude"],
                    longitude=fac["longitude"],
                    status=fac["status"],
                    nger_id=fac["nger_id"],
                    commodity=fac["commodity"],
                ),
                tropomi_trend=tropomi_points,
                latest_tropomi=latest_tropomi,
                recent_detections=detections,
                active_alerts=alerts,
                compliance=ComplianceSummary(**compliance),
                trend=EmissionsTrend(**trend),
                total_detections=total_det,
                detection_rate_per_year=detection_rate,
            )
        )

    # Sort facilities by intensity (highest first) for prioritization
    dashboards.sort(
        key=lambda d: d.latest_tropomi.intensity_score if d.latest_tropomi and d.latest_tropomi.intensity_score else 0,
        reverse=True,
    )

    return ProjectEmissionsResponse(
        matched_facilities=len(dashboards),
        facilities=dashboards,
        area_summary={
            "total_facilities": len(dashboards),
            "total_detections": total_detections_all,
            "max_intensity": max_intensity_all,
            "facilities_with_alerts": facilities_with_alerts,
        },
    )
