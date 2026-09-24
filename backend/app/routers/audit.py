from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["Audit Trail & CDC Logs"])

@router.get("/summary", dependencies=[Depends(require_capability("nav.audit"))])
async def get_audit_summary(
    db: AsyncSession = Depends(get_db),
):
    """Retrieve aggregate KPI statistics for the audit trail dashboard."""
    return await AuditService.get_audit_summary(db)

@router.get("", dependencies=[Depends(require_capability("nav.audit"))])
@router.get("/", dependencies=[Depends(require_capability("nav.audit"))])
async def list_audit_logs(
    table_name: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    record_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve paginated and filtered audit trail records from ifms_budget.audit_change_log."""
    return await AuditService.get_audit_logs(
        db=db,
        table_name=table_name,
        module=module,
        record_id=record_id,
        action=action,
        user=user,
        from_date=from_date,
        to_date=to_date,
        search=search,
        limit=limit,
        offset=offset,
    )
