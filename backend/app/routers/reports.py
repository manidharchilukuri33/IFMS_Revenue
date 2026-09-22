import io
import csv
from fastapi import APIRouter, Depends, Query, Response
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["Reports & MIS Engine"])

@router.get("", dependencies=[Depends(require_capability("nav.reports"))])
@router.get("/list", dependencies=[Depends(require_capability("nav.reports"))])
async def list_reports_metadata():
    return await ReportService.get_report_metadata()


@router.get("/{report_id}", dependencies=[Depends(require_capability("nav.reports"))])
async def get_report_data(
    report_id: str,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source_id: Optional[int] = Query(None),
    bank_id: Optional[int] = Query(None),
    pao_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await ReportService.generate_report(
        db, report_id, from_date, to_date, source_id, bank_id, pao_code
    )

@router.get("/{report_id}/export", dependencies=[Depends(require_capability("export"))])
async def export_report_csv(
    report_id: str,
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    source_id: Optional[int] = Query(None),
    bank_id: Optional[int] = Query(None),
    pao_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    dataset = await ReportService.generate_report(
        db, report_id, from_date, to_date, source_id, bank_id, pao_code
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(dataset.headers)
    for row in dataset.rows:
        writer.writerow(row)

    content = output.getvalue()
    filename = f"{dataset.report_id}_{dataset.report_name.replace(' ', '_').lower()}.csv"

    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
