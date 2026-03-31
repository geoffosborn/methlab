"""Sentinel-2 detection API routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import db_execute

router = APIRouter(prefix="/sentinel2", tags=["sentinel2"])


class S2DetectionResponse(BaseModel):
    id: int
    facility_id: int
    scene_id: str
    scene_datetime: str
    emission_rate_kg_hr: float | None = None
    emission_rate_t_hr: float | None = None
    uncertainty_kg_hr: float | None = None
    ime_kg: float | None = None
    effective_wind_m_s: float | None = None
    plume_length_m: float | None = None
    plume_area_m2: float | None = None
    plume_pixels: int | None = None
    mean_enhancement: float | None = None
    max_enhancement: float | None = None
    wind_speed_10m: float | None = None
    wind_direction: float | None = None
    confidence: str | None = None
    viz_s3_key: str | None = None


class S2DetectionListResponse(BaseModel):
    total_count: int
    items: list[S2DetectionResponse]


@router.get("/facilities/{facility_id}", response_model=S2DetectionListResponse)
async def get_facility_detections(
    facility_id: int,
    confidence: str | None = Query(None, description="Filter by confidence level"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get S2 plume detections for a facility, ordered by date descending."""
    conditions = ["facility_id = %s"]
    params: list = [facility_id]

    if confidence:
        conditions.append("confidence = %s")
        params.append(confidence)

    where = " AND ".join(conditions)

    count_row = db_execute(
        f"SELECT count(*) as cnt FROM s2_detections WHERE {where}",
        params,
        fetch="one",
    )
    total = count_row["cnt"] if count_row else 0

    rows = db_execute(
        f"""
        SELECT id, facility_id, scene_id, scene_datetime::text,
               emission_rate_kg_hr,
               CASE WHEN emission_rate_kg_hr IS NOT NULL
                    THEN emission_rate_kg_hr / 1000.0
                    ELSE NULL END as emission_rate_t_hr,
               uncertainty_kg_hr, ime_kg, effective_wind_m_s,
               plume_length_m, plume_area_m2, plume_pixels,
               mean_enhancement, max_enhancement,
               wind_speed_10m, wind_direction, confidence, viz_s3_key
        FROM s2_detections
        WHERE {where}
        ORDER BY scene_datetime DESC
        LIMIT %s OFFSET %s
        """,
        params + [limit, offset],
    )

    return S2DetectionListResponse(
        total_count=total,
        items=[S2DetectionResponse(**row) for row in (rows or [])],
    )


@router.get("/detections/recent", response_model=list[dict])
async def get_recent_detections(
    limit: int = Query(20, ge=1, le=100),
):
    """Get most recent S2 detections across all facilities."""
    rows = db_execute(
        """
        SELECT d.id, d.facility_id, f.name as facility_name, f.state,
               d.scene_datetime::text, d.emission_rate_kg_hr,
               d.emission_rate_kg_hr / 1000.0 as emission_rate_t_hr,
               d.plume_pixels, d.confidence,
               d.wind_speed_10m, d.wind_direction
        FROM s2_detections d
        JOIN facilities f ON f.id = d.facility_id
        ORDER BY d.scene_datetime DESC
        LIMIT %s
        """,
        [limit],
    )

    return rows or []
