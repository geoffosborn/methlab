"""Alert API routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import db_execute, db_execute_returning
from app.services.alert_service import acknowledge_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    id: int
    facility_id: int
    alert_type: str
    severity: str
    title: str
    description: str | None = None
    metadata: dict | None = None
    acknowledged: bool = False
    acknowledged_by: str | None = None
    acknowledged_at: str | None = None
    created_at: str


class AlertListResponse(BaseModel):
    total_count: int
    items: list[AlertResponse]


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    facility_id: int | None = Query(None),
    severity: str | None = Query(None),
    acknowledged: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List alerts with optional filters."""
    conditions = []
    params: list = []

    if facility_id is not None:
        conditions.append("a.facility_id = %s")
        params.append(facility_id)
    if severity:
        conditions.append("a.severity = %s")
        params.append(severity)
    if acknowledged is not None:
        conditions.append("a.acknowledged = %s")
        params.append(acknowledged)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    count_row = db_execute(
        f"SELECT count(*) as cnt FROM alerts a {where}", params, fetch="one"
    )
    total = count_row["cnt"] if count_row else 0

    rows = db_execute(
        f"""
        SELECT a.id, a.facility_id, a.alert_type, a.severity, a.title,
               a.description, a.metadata,
               a.acknowledged, a.acknowledged_by,
               a.acknowledged_at::text, a.created_at::text
        FROM alerts a
        {where}
        ORDER BY a.created_at DESC
        LIMIT %s OFFSET %s
        """,
        params + [limit, offset],
    )

    return AlertListResponse(
        total_count=total,
        items=[AlertResponse(**row) for row in (rows or [])],
    )


class AcknowledgeRequest(BaseModel):
    acknowledged_by: str


@router.post("/{alert_id}/acknowledge")
async def ack_alert(alert_id: int, req: AcknowledgeRequest):
    """Acknowledge an alert."""
    acknowledge_alert(alert_id, req.acknowledged_by)
    return {"ok": True, "alert_id": alert_id}


@router.get("/summary")
async def alert_summary():
    """Get alert count summary by severity and status."""
    rows = db_execute(
        """
        SELECT severity, acknowledged,
               count(*) as count
        FROM alerts
        GROUP BY severity, acknowledged
        ORDER BY severity
        """,
    )

    unacknowledged = sum(r["count"] for r in (rows or []) if not r["acknowledged"])

    return {
        "total": sum(r["count"] for r in (rows or [])),
        "unacknowledged": unacknowledged,
        "by_severity": rows or [],
    }
