"""Report generation and export routes."""

from datetime import date

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.services.report_service import generate_compliance_summary, generate_facility_csv

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/facilities/{facility_id}/export")
async def export_facility_data(
    facility_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    report_type: str = Query("detections", description="detections or tropomi"),
):
    """Export facility monitoring data as CSV."""
    csv_bytes = generate_facility_csv(
        facility_id=facility_id,
        start_date=start_date,
        end_date=end_date,
        report_type=report_type,
    )

    if not csv_bytes:
        return Response(content="No data for the specified period.", status_code=404)

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename=methlab_{report_type}_{facility_id}"
                f"_{start_date}_{end_date}.csv"
            ),
        },
    )


@router.get("/facilities/{facility_id}/compliance")
async def get_compliance_report(
    facility_id: int,
    year: int = Query(..., description="Reporting year"),
):
    """Get NGER compliance summary for a facility."""
    return generate_compliance_summary(facility_id=facility_id, year=year)
