"""Facility API routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import db_execute

router = APIRouter(prefix="/facilities", tags=["facilities"])


class FacilityResponse(BaseModel):
    id: int
    name: str
    facility_type: str
    state: str | None = None
    operator: str | None = None
    latitude: float
    longitude: float
    nger_id: str | None = None
    status: str = "active"
    commodity: str | None = None
    metadata: dict | None = None


class FacilityListResponse(BaseModel):
    total_count: int
    items: list[FacilityResponse]


@router.get("", response_model=FacilityListResponse)
async def list_facilities(
    facility_type: str | None = Query(None, description="Filter by type (e.g. coal_mine)"),
    state: str | None = Query(None, description="Filter by state (e.g. QLD, NSW)"),
    status: str | None = Query(None, description="Filter by status"),
    commodity: str | None = Query(None, description="Filter by commodity (e.g. thermal coal)"),
    q: str | None = Query(None, description="Text search by name or operator"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List all monitored facilities."""
    conditions = []
    params: list = []

    if facility_type:
        conditions.append("facility_type = %s")
        params.append(facility_type)
    if state:
        conditions.append("state = %s")
        params.append(state)
    if status:
        conditions.append("status = %s")
        params.append(status)
    if commodity:
        conditions.append("commodity = %s")
        params.append(commodity)
    if q:
        conditions.append("(name ILIKE %s OR operator ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    count_row = db_execute(f"SELECT count(*) as cnt FROM facilities {where}", params, fetch="one")
    total = count_row["cnt"] if count_row else 0

    rows = db_execute(
        f"""
        SELECT id, name, facility_type, state, operator,
               ST_Y(centroid::geometry) as latitude,
               ST_X(centroid::geometry) as longitude,
               nger_id, status, commodity, metadata
        FROM facilities
        {where}
        ORDER BY name
        LIMIT %s OFFSET %s
        """,
        params + [limit, offset],
    )

    return FacilityListResponse(
        total_count=total,
        items=[FacilityResponse(**row) for row in (rows or [])],
    )


@router.get("/search", response_model=FacilityListResponse)
async def search_facilities(
    q: str | None = Query(None, description="Text search by name or operator"),
    bbox: str | None = Query(None, description="Bounding box: west,south,east,north"),
    limit: int = Query(200, ge=1, le=1000),
):
    """Search facilities by text query and/or bounding box."""
    conditions = []
    params: list = []

    if q:
        conditions.append("(name ILIKE %s OR operator ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    if bbox:
        try:
            west, south, east, north = [float(x) for x in bbox.split(",")]
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="bbox must be west,south,east,north")
        envelope = f"SRID=4326;POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
        conditions.append("ST_Intersects(centroid, ST_GeomFromEWKT(%s))")
        params.append(envelope)

    if not conditions:
        raise HTTPException(status_code=400, detail="Provide q (text search) and/or bbox")

    where = "WHERE " + " AND ".join(conditions)

    rows = db_execute(
        f"""
        SELECT id, name, facility_type, state, operator,
               ST_Y(centroid::geometry) as latitude,
               ST_X(centroid::geometry) as longitude,
               nger_id, status, commodity, metadata
        FROM facilities
        {where}
        ORDER BY name
        LIMIT %s
        """,
        params + [limit],
    )

    items = [FacilityResponse(**row) for row in (rows or [])]
    return FacilityListResponse(total_count=len(items), items=items)


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(facility_id: int):
    """Get a single facility by ID."""
    row = db_execute(
        """
        SELECT id, name, facility_type, state, operator,
               ST_Y(centroid::geometry) as latitude,
               ST_X(centroid::geometry) as longitude,
               nger_id, status, commodity, metadata
        FROM facilities
        WHERE id = %s
        """,
        [facility_id],
        fetch="one",
    )

    if not row:
        raise HTTPException(status_code=404, detail="Facility not found")

    return FacilityResponse(**row)
