from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, func, desc, or_

from app.core.database import get_db
from app.models.common import SystemNotification

router = APIRouter(prefix="/api/notifications", tags=["System Notifications"])

class NotificationCreate(BaseModel):
    title: str
    text: str
    level: str = "info" # 'ok', 'warn', 'err', 'info'
    target_role: Optional[str] = None
    action_module: Optional[str] = None
    reference_id: Optional[str] = None

class MarkReadRequest(BaseModel):
    notification_id: Optional[int] = None
    role: Optional[str] = None
    all: bool = True

def format_timestamp(dt: datetime) -> str:
    if not dt:
        return ""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{dt.day:02d}-{months[dt.month - 1]}-{dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"

async def seed_default_notifications_if_empty(session: AsyncSession):
    count_res = await session.execute(select(func.count()).select_from(SystemNotification))
    count = count_res.scalar() or 0
    if count == 0:
        defaults = [
            {
                "notification_code": "NTF-00001",
                "title": "Upload batch UPB-PRT-2026-0001 posted",
                "text": "16 record(s) totalling ₹ 11,05,700.00 awaiting PAO Checker approval.",
                "level": "info",
                "target_role": "PAO_CHECK",
                "action_module": "upload",
                "reference_id": "UPB-PRT-2026-0001",
                "is_read": False,
            },
            {
                "notification_code": "NTF-00002",
                "title": "Upload batch UPB-BNK-2026-0002 posted",
                "text": "19 record(s) totalling ₹ 11,03,700.00 awaiting PAO Checker approval.",
                "level": "info",
                "target_role": "PAO_CHECK",
                "action_module": "upload",
                "reference_id": "UPB-BNK-2026-0002",
                "is_read": False,
            },
            {
                "notification_code": "NTF-00003",
                "title": "Upload batch UPB-RBI-2026-0003 posted",
                "text": "18 record(s) totalling ₹ 10,88,700.00 awaiting PAO Checker approval.",
                "level": "info",
                "target_role": "PAO_CHECK",
                "action_module": "upload",
                "reference_id": "UPB-RBI-2026-0003",
                "is_read": False,
            },
            {
                "notification_code": "NTF-00004",
                "title": "Reconciliation exceptions raised",
                "text": "1 suspense, 1 RAT, 1 mismatch and 1 duplicate case(s) require action.",
                "level": "warn",
                "target_role": "ALL",
                "action_module": "recon",
                "reference_id": "RECON-001",
                "is_read": False,
            },
            {
                "notification_code": "NTF-00005",
                "title": "Demo environment ready",
                "text": "16 portal, 19 bank and 18 RBI records loaded and reconciled. 6 exception(s) raised.",
                "level": "ok",
                "target_role": "ALL",
                "action_module": "system",
                "reference_id": "INIT",
                "is_read": False,
            },
            {
                "notification_code": "NTF-00006",
                "title": "Reconciliation exceptions raised",
                "text": "1 suspense, 1 RAT, 1 mismatch and 1 duplicate case(s) require action.",
                "level": "warn",
                "target_role": "ALL",
                "action_module": "recon",
                "reference_id": "RECON-002",
                "is_read": False,
            },
        ]
        for d in defaults:
            session.add(SystemNotification(**d))
        await session.commit()

@router.get("")
async def get_notifications(
    role: Optional[str] = Query(None, description="Active user role"),
    unread_only: bool = Query(False, description="Filter unread notifications only"),
    limit: int = Query(40, description="Max notifications to retrieve"),
    session: AsyncSession = Depends(get_db),
):
    """Retrieve system alerts and notifications filtered dynamically by role and status."""
    await seed_default_notifications_if_empty(session)

    stmt = select(SystemNotification)

    # Role-based filtering: Include alerts for this role OR global alerts for all roles
    if role and role != "SYSADMIN" and role != "TRE_ADMIN":
        stmt = stmt.where(
            or_(
                SystemNotification.target_role.is_(None),
                SystemNotification.target_role == "ALL",
                SystemNotification.target_role == role,
            )
        )

    if unread_only:
        stmt = stmt.where(SystemNotification.is_read == False)

    stmt = stmt.order_by(desc(SystemNotification.notification_id)).limit(limit)

    res = await session.execute(stmt)
    records = res.scalars().all()

    # Calculate unread count for this role
    unread_stmt = select(func.count()).select_from(SystemNotification).where(SystemNotification.is_read == False)
    if role and role != "SYSADMIN" and role != "TRE_ADMIN":
        unread_stmt = unread_stmt.where(
            or_(
                SystemNotification.target_role.is_(None),
                SystemNotification.target_role == "ALL",
                SystemNotification.target_role == role,
            )
        )
    unread_res = await session.execute(unread_stmt)
    unread_count = unread_res.scalar() or 0

    items = []
    for r in records:
        items.append({
            "id": r.notification_code,
            "notification_id": r.notification_id,
            "ts": format_timestamp(r.created_at),
            "title": r.title,
            "text": r.text,
            "level": r.level,
            "target_role": r.target_role or "ALL",
            "action_module": r.action_module or "general",
            "reference_id": r.reference_id,
            "read": r.is_read,
        })

    return {
        "unread_count": unread_count,
        "total": len(items),
        "notifications": items,
    }

@router.post("/mark-read")
async def mark_notifications_read(
    req: MarkReadRequest,
    session: AsyncSession = Depends(get_db),
):
    """Mark all or specific notifications as read in the database."""
    stmt = update(SystemNotification).values(is_read=True)

    if req.notification_id:
        stmt = stmt.where(SystemNotification.notification_id == req.notification_id)
    elif req.role and req.role != "SYSADMIN" and req.role != "TRE_ADMIN":
        stmt = stmt.where(
            or_(
                SystemNotification.target_role.is_(None),
                SystemNotification.target_role == "ALL",
                SystemNotification.target_role == req.role,
            )
        )

    res = await session.execute(stmt)
    await session.commit()

    return {
        "status": "SUCCESS",
        "message": "Notifications marked as read",
        "affected_rows": res.rowcount,
    }

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate,
    session: AsyncSession = Depends(get_db),
):
    """Create a new dynamic system notification."""
    seq_res = await session.execute(select(func.coalesce(func.max(SystemNotification.notification_id), 0)))
    next_id = (seq_res.scalar() or 0) + 1
    code = f"NTF-{next_id:05d}"

    new_ntf = SystemNotification(
        notification_code=code,
        title=data.title,
        text=data.text,
        level=data.level,
        target_role=data.target_role,
        action_module=data.action_module,
        reference_id=data.reference_id,
        is_read=False,
    )
    session.add(new_ntf)
    await session.commit()
    await session.refresh(new_ntf)

    return {
        "id": new_ntf.notification_code,
        "notification_id": new_ntf.notification_id,
        "ts": format_timestamp(new_ntf.created_at),
        "title": new_ntf.title,
        "text": new_ntf.text,
        "level": new_ntf.level,
        "target_role": new_ntf.target_role or "ALL",
        "action_module": new_ntf.action_module,
        "reference_id": new_ntf.reference_id,
        "read": new_ntf.is_read,
    }
