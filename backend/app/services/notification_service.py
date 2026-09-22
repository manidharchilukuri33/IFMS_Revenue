from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.common import SystemNotification

async def notify_system(
    db: AsyncSession,
    title: str,
    text: str,
    level: str = "info",
    target_role: Optional[str] = None,
    action_module: Optional[str] = None,
    reference_id: Optional[str] = None,
):
    """
    Centralized system alert dispatcher for backend event-driven notifications.
    Automatically generates incremental notification codes and commits within transaction.
    """
    try:
        seq_res = await db.execute(select(func.coalesce(func.max(SystemNotification.notification_id), 0)))
        next_id = (seq_res.scalar() or 0) + 1
        code = f"NTF-{next_id:05d}"
        
        ntf = SystemNotification(
            notification_code=code,
            title=title,
            text=text,
            level=level,
            target_role=target_role,
            action_module=action_module,
            reference_id=reference_id,
            is_read=False,
        )
        db.add(ntf)
        await db.flush()
    except Exception as e:
        # Prevent notification logging from disrupting core business transaction
        print(f"[WARN] Failed to write notification: {e}")
