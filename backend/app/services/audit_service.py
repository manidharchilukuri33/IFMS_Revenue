from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from app.models.common import AuditChangeLog, AppUser

class AuditService:
    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        query = select(AuditChangeLog)

        if table_name:
            query = query.where(AuditChangeLog.table_name == table_name)
        if record_id:
            query = query.where(AuditChangeLog.row_pk == str(record_id))
        if action:
            query = query.where(AuditChangeLog.operation == action)

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(AuditChangeLog.audit_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        logs = result.scalars().all()

        items = []
        for log in logs:
            user_name = "System"
            if log.changed_by:
                user = await db.get(AppUser, log.changed_by)
                if user:
                    user_name = user.full_name or user.login_name

            items.append({
                "audit_id": log.audit_id,
                "log_id": log.audit_id,
                "schema_name": log.schema_name,
                "table_name": log.table_name,
                "operation": log.operation,
                "action": log.operation,
                "row_pk": log.row_pk,
                "record_id": log.row_pk,
                "old_data": log.old_data,
                "new_data": log.new_data,
                "changed_by": log.changed_by,
                "user_name": user_name,
                "changed_at": log.changed_at.strftime("%Y-%m-%d %H:%M:%S") if log.changed_at else "",
                "txid": log.txid,
            })

        return {
            "total": total_count,
            "items": items
        }
