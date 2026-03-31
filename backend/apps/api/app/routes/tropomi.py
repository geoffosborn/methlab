"""TROPOMI observation API routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import db_execute

router = APIRouter(prefix="/tropomi", tags=["tropomi"])


class TropomiObservationResponse(BaseModel):
    id: int
    facility_id: int
    period_start: str
    period_end: str
    aggregation_period: str
    mean_enhancement_ppb: float | None = None
    max_enhancement_ppb: float | None = None
    central_box_mean_ppb: float | None = None
    sample_count: int | None = None
    valid_pixel_fraction: float | None = None
    mean_wind_speed: float | None = None
    intensity_score: float | None = None
    background_ch4_ppb: float | None = None
    viz_s3_key: str | None = None
    metrics_s3_key: str | None = None


class TropomiListResponse(BaseModel):
    total_count: int
    items: list[TropomiObservationResponse]


@router.get("/facilities/{facility_id}", response_model=TropomiListResponse)
async def get_facility_tropomi(
    facility_id: int,
    aggregation_period: str | None = Query(None, description="monthly, quarterly, annual"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get TROPOMI observations for a facility, ordered by period descending."""
    conditions = ["facility_id = %s"]
    params: list = [facility_id]

    if aggregation_period:
        conditions.append("aggregation_period = %s")
        params.append(aggregation_period)

    where = " AND ".join(conditions)

    count_row = db_execute(
        f"SELECT count(*) as cnt FROM tropomi_observations WHERE {where}",
        params,
        fetch="one",
    )
    total = count_row["cnt"] if count_row else 0

    rows = db_execute(
        f"""
        SELECT id, facility_id, period_start::text, period_end::text,
               aggregation_period, mean_enhancement_ppb, max_enhancement_ppb,
               central_box_mean_ppb, sample_count, valid_pixel_fraction,
               mean_wind_speed, intensity_score, background_ch4_ppb,
               viz_s3_key, metrics_s3_key
        FROM tropomi_observations
        WHERE {where}
        ORDER BY period_start DESC
        LIMIT %s OFFSET %s
        """,
        params + [limit, offset],
    )

    return TropomiListResponse(
        total_count=total,
        items=[TropomiObservationResponse(**row) for row in (rows or [])],
    )


@router.get("/rankings", response_model=list[dict])
async def get_tropomi_rankings(
    aggregation_period: str = Query("quarterly"),
    limit: int = Query(20, ge=1, le=100),
):
    """Get facilities ranked by latest TROPOMI intensity score."""
    rows = db_execute(
        """
        SELECT DISTINCT ON (t.facility_id)
               t.facility_id, f.name as facility_name, f.state, f.operator,
               t.intensity_score, t.central_box_mean_ppb,
               t.mean_enhancement_ppb, t.sample_count,
               t.period_start::text, t.period_end::text
        FROM tropomi_observations t
        JOIN facilities f ON f.id = t.facility_id
        WHERE t.aggregation_period = %s
        ORDER BY t.facility_id, t.period_start DESC
        """,
        [aggregation_period],
    )

    if not rows:
        return []

    # Sort by intensity score descending
    ranked = sorted(rows, key=lambda r: r.get("intensity_score") or 0, reverse=True)
    return ranked[:limit]
