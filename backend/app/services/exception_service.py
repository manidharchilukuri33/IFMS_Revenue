from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text, and_
from app.models.exceptions import RevException, RevExceptionNote, RevExceptionLetter
from app.models.recon import RevReconResult
from app.models.common import AppUser
from app.core.exceptions import NotFoundException, InvalidStateTransitionException

class ExceptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_exceptions(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        overdue_only: bool = False,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[RevException], int]:
        conditions = []
        if category:
            conditions.append(RevException.category == category)
        if severity:
            conditions.append(RevException.severity == severity)
        if status:
            conditions.append(RevException.status == status)
        if overdue_only:
            conditions.append(and_(RevException.due_date < date.today(), RevException.status.in_(["Open", "Assigned", "Escalated"])))

        where_clause = and_(*conditions) if conditions else True
        count_q = select(func.count(RevException.exception_id)).where(where_clause)
        count_res = await self.db.execute(count_q)
        total = count_res.scalar() or 0

        query = (
            select(RevException)
            .where(where_clause)
            .order_by(RevException.exception_id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        res = await self.db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def get_exception_detail(self, exception_id: int) -> Dict[str, Any]:
        exc = await self.db.get(RevException, exception_id)
        if not exc:
            raise NotFoundException("Exception", exception_id)

        notes_q = select(RevExceptionNote).where(RevExceptionNote.exception_id == exception_id).order_by(RevExceptionNote.note_id.asc())
        notes_res = await self.db.execute(notes_q)
        notes = list(notes_res.scalars().all())

        letters_q = select(RevExceptionLetter).where(RevExceptionLetter.exception_id == exception_id).order_by(RevExceptionLetter.letter_id.desc())
        letters_res = await self.db.execute(letters_q)
        letters = list(letters_res.scalars().all())

        recon_context = None
        if exc.recon_id:
            rc = await self.db.get(RevReconResult, exc.recon_id)
            if rc:
                recon_context = {
                    "rev_transaction_id": rc.rev_transaction_id,
                    "challan_no": rc.challan_no,
                    "cin": rc.cin,
                    "portal_total": float(rc.portal_total),
                    "bank_total": float(rc.bank_total),
                    "rbi_total": float(rc.rbi_total),
                    "amount_difference": float(rc.amount_difference),
                    "status": rc.status,
                    "match_reason": rc.match_reason
                }

        return {
            "exception": exc,
            "notes": notes,
            "letters": letters,
            "recon_context": recon_context
        }

    async def resolve_exception(self, exception_id: int, reason: str, remarks: str, user_id: int) -> RevException:
        exc = await self.db.get(RevException, exception_id)
        if not exc:
            raise NotFoundException("Exception", exception_id)

        exc.status = "Resolved"
        exc.resolution_reason = reason
        exc.resolution_remarks = remarks
        exc.resolved_by = user_id
        exc.resolved_at = datetime.now()

        # Add timeline note
        note = RevExceptionNote(
            exception_id=exception_id,
            action_type="RESOLVED",
            note_text=f"Resolved with reason '{reason}': {remarks}",
            created_by=user_id
        )
        self.db.add(note)

        await self.db.commit()
        await self.db.refresh(exc)
        return exc

    async def create_letter(
        self,
        exception_id: int,
        recipient_type: str,
        recipient_name: str,
        recipient_address: Optional[str],
        subject: str,
        body: str,
        user_id: int
    ) -> RevExceptionLetter:
        exc = await self.db.get(RevException, exception_id)
        if not exc:
            raise NotFoundException("Exception", exception_id)

        seq_res = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('LETTER_SEQ', 'LTR-EXC', '2026-27')"))
        letter_no = seq_res.scalar() or f"LTR-EXC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        letter = RevExceptionLetter(
            letter_no=letter_no,
            exception_id=exception_id,
            recipient_type=recipient_type,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            letter_subject=subject,
            letter_body=body,
            issued_date=date.today(),
            issued_by=user_id,
            status="ISSUED"
        )
        self.db.add(letter)

        note = RevExceptionNote(
            exception_id=exception_id,
            action_type="LETTER_ISSUED",
            note_text=f"Discrepancy notice {letter_no} issued to {recipient_name} ({recipient_type})",
            created_by=user_id
        )
        self.db.add(note)

        await self.db.commit()
        await self.db.refresh(letter)
        return letter

    async def bulk_assign(self, exception_ids: List[int], assigned_user_id: int, user_id: int) -> int:
        if not exception_ids:
            return 0
        stmt = (
            update(RevException)
            .where(RevException.exception_id.in_(exception_ids))
            .values(assigned_user_id=assigned_user_id, status="Assigned")
        )
        res = await self.db.execute(stmt)

        for eid in exception_ids:
            self.db.add(RevExceptionNote(
                exception_id=eid,
                action_type="ASSIGNED",
                note_text=f"Assigned to officer ID {assigned_user_id}",
                created_by=user_id
            ))

        await self.db.commit()
        return res.rowcount

    async def escalate_overdue(self, user_id: int) -> int:
        today = date.today()
        stmt = (
            update(RevException)
            .where(and_(RevException.due_date < today, RevException.status.in_(["Open", "Assigned"])))
            .values(
                status="Escalated",
                escalation_count=RevException.escalation_count + 1,
                last_escalated_at=func.clock_timestamp()
            )
        )
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount

    async def add_note(self, exception_id: int, note_text: str, user_id: int, action_type: str = "COMMENT") -> RevExceptionNote:
        exc = await self.db.get(RevException, exception_id)
        if not exc:
            raise NotFoundException("Exception", exception_id)
        note = RevExceptionNote(
            exception_id=exception_id,
            action_type=action_type,
            note_text=note_text,
            created_by=user_id
        )
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note
