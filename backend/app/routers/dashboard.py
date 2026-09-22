from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard & MIS"])

@router.get("/summary", dependencies=[Depends(require_capability("nav.dashboard"))])
async def get_dashboard_summary(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_dashboard_summary(db, from_date, to_date)
