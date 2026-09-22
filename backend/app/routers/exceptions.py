from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.exceptions import (
    ExceptionResolveRequest,
    DiscrepancyLetterCreate,
    BulkAssignRequest,
)
from app.services.exception_service import ExceptionService

router = APIRouter(prefix="/api/exceptions", tags=["Exception Management"])

@router.get("", dependencies=[Depends(require_capability("nav.exceptions"))])
@router.get("/", dependencies=[Depends(require_capability("nav.exceptions"))])
async def list_exceptions(
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    svc = ExceptionService(db)
    items, total = await svc.list_exceptions(category, severity, status, False, page, limit)
    return items

@router.get("/{exception_id}", dependencies=[Depends(require_capability("nav.exceptions"))])
async def get_exception_detail(
    exception_id: int,
    db: AsyncSession = Depends(get_db),
):
    svc = ExceptionService(db)
    return await svc.get_exception_detail(exception_id)

@router.post("/{exception_id}/resolve", dependencies=[Depends(require_capability("exception.manage"))])
async def resolve_exception(
    exception_id: int,
    req: ExceptionResolveRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ExceptionService(db)
    return await svc.resolve_exception(exception_id, req.resolution_reason, req.resolution_remarks, user.user_id)

@router.post("/{exception_id}/discrepancy-letter", dependencies=[Depends(require_capability("penalty.letter"))])
@router.post("/{exception_id}/issue-letter", dependencies=[Depends(require_capability("penalty.letter"))])
async def issue_discrepancy_letter(
    exception_id: int,
    req: DiscrepancyLetterCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ExceptionService(db)
    return await svc.create_letter(
        exception_id=exception_id,
        recipient_type=req.recipient_type,
        recipient_name=req.recipient_name,
        recipient_address=req.recipient_address,
        subject=req.letter_subject,
        body=req.letter_body,
        user_id=user.user_id
    )

@router.post("/assign-bulk", dependencies=[Depends(require_capability("exception.manage"))])
async def bulk_assign_exceptions(
    req: BulkAssignRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ExceptionService(db)
    count = await svc.bulk_assign(req.exception_ids, req.assigned_user_id, user.user_id)
    return {"status": "SUCCESS", "assigned_count": count}

@router.post("/escalate-overdue", dependencies=[Depends(require_capability("exception.escalate"))])
async def escalate_overdue_exceptions(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ExceptionService(db)
    count = await svc.escalate_overdue(user.user_id)
    return {"status": "SUCCESS", "escalated_count": count}

