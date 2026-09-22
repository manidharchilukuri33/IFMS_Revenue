from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["Audit Trail & CDC Logs"])

@router.get("", dependencies=[Depends(require_capability("nav.audit"))])
@router.get("/", dependencies=[Depends(require_capability("nav.audit"))])
async def list_audit_logs(
    table_name: Optional[str] = Query(None),
    record_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await AuditService.get_audit_logs(db, table_name, record_id, action, limit, offset)
