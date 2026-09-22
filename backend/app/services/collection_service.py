from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text, and_
from app.models.staging import RevUploadBatch, RevPortalTransactionStaging, RevAgencyBankScrollStaging, RevRbiLuggageStaging
from app.models.recon import RevReconResult, RevReconLegLinkage
from app.schemas.collection import ManualCollectionCreate
from app.core.exceptions import NotFoundException

class CollectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_transactions(
        self,
        source: Optional[str] = None,
        dept: Optional[str] = None,
        pao: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[RevPortalTransactionStaging], int]:
        conditions = [RevPortalTransactionStaging.is_valid == True]
        if source:
            conditions.append(RevPortalTransactionStaging.revenue_source == source)
        if dept:
            conditions.append(RevPortalTransactionStaging.dept_code == dept)
        if pao:
            conditions.append(RevPortalTransactionStaging.pao_code == pao)
        if from_date:
            conditions.append(RevPortalTransactionStaging.payment_date >= from_date)
        if to_date:
            conditions.append(RevPortalTransactionStaging.payment_date <= to_date)
        if search:
            s_term = f"%{search}%"
            conditions.append(
                (RevPortalTransactionStaging.challan_no.ilike(s_term)) |
                (RevPortalTransactionStaging.cin.ilike(s_term)) |
                (RevPortalTransactionStaging.payer_name.ilike(s_term)) |
                (RevPortalTransactionStaging.portal_transaction_id.ilike(s_term))
            )

        # Count total
        count_q = select(func.count(RevPortalTransactionStaging.portal_item_id)).where(and_(*conditions))
        count_res = await self.db.execute(count_q)
        total = count_res.scalar() or 0

        # Items
        query = (
            select(RevPortalTransactionStaging)
            .where(and_(*conditions))
            .order_by(RevPortalTransactionStaging.payment_date.desc(), RevPortalTransactionStaging.portal_item_id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        res = await self.db.execute(query)
        items = list(res.scalars().all())
        return items, total

    async def get_transaction_detail(self, portal_item_id: int) -> Dict[str, Any]:
        item = await self.db.get(RevPortalTransactionStaging, portal_item_id)
        if not item:
            raise NotFoundException("Portal Transaction", portal_item_id)

        # Look for matching recon result
        recon_q = (
            select(RevReconResult)
            .join(RevReconLegLinkage, RevReconLegLinkage.recon_id == RevReconResult.recon_id)
            .where(RevReconLegLinkage.portal_item_id == portal_item_id)
        )
        recon_res = await self.db.execute(recon_q)
        recon = recon_res.scalar_one_or_none()

        bank_legs = []
        rbi_legs = []
        if recon:
            links_q = select(RevReconLegLinkage).where(RevReconLegLinkage.recon_id == recon.recon_id)
            links_res = await self.db.execute(links_q)
            for l in links_res.scalars():
                if l.scroll_item_id:
                    b = await self.db.get(RevAgencyBankScrollStaging, l.scroll_item_id)
                    if b:
                        bank_legs.append({"bank_code": b.bank_code, "scroll_no": b.scroll_no, "amount": float(b.amount), "remittance_date": str(b.bank_remittance_date), "utr": b.utr_no})
                if l.rbi_item_id:
                    r = await self.db.get(RevRbiLuggageStaging, l.rbi_item_id)
                    if r:
                        rbi_legs.append({"rbi_ref": r.rbi_reference_no, "amount": float(r.amount), "credit_date": str(r.rbi_credit_date), "status": r.rbi_status})

        return {
            "transaction": item,
            "recon_result": recon,
            "bank_legs": bank_legs,
            "rbi_legs": rbi_legs
        }

    async def create_manual_receipt(self, data: ManualCollectionCreate, user_id: int) -> RevPortalTransactionStaging:
        # Generate sequence for manual batch
        seq_res = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('BATCH_SEQ', 'BAT-MANUAL', '2026-27')"))
        batch_no = seq_res.scalar() or f"BAT-MAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        batch = RevUploadBatch(
            batch_no=batch_no,
            batch_type="MANUAL_ENTRY",
            source_filename="manual_user_entry",
            data_date=data.payment_date,
            revenue_source_code=data.revenue_source,
            total_records=1,
            valid_records=1,
            control_total=data.amount,
            status="APPROVED", # manual receipts entered by authenticated officer are pre-approved
            uploaded_by=user_id,
            uploaded_at=datetime.now(),
            checker_user_id=user_id,
            approved_at=datetime.now()
        )
        self.db.add(batch)
        await self.db.flush()

        item_seq = await self.db.execute(text("SELECT ifms_budget.fn_rev_next_seq('TXN_SEQ', 'TXN-MAN', '2026-27')"))
        txn_id = item_seq.scalar() or f"TXN-MAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        challan_no = data.challan_no or f"CHL-MAN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        service_date = data.service_date or data.payment_date
        ddo_code = data.ddo_code or "DDO01"
        service_description = data.service_description or data.narration or "Manual Collection Receipt"

        item = RevPortalTransactionStaging(
            batch_id=batch.batch_id,
            portal_name=data.portal_name,
            revenue_source=data.revenue_source,
            dept_code=data.dept_code,
            pao_code=data.pao_code,
            ddo_code=ddo_code,
            portal_transaction_id=txn_id,
            challan_no=challan_no,
            cpin=data.cpin,
            cin=data.cin,
            payer_id=data.payer_id,
            payer_name=data.payer_name,
            payment_date=data.payment_date,
            service_date=service_date,
            payment_mode=data.payment_mode.upper(),
            amount=data.amount,
            receipt_head=data.receipt_head,
            service_description=service_description,
            penalty_amount=data.penalty_amount,
            portal_status="PAID",
            dept_validated=True,
            dept_validated_by=user_id,
            dept_validated_at=datetime.now(),
            is_valid=True
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def validate_departmental(self, portal_item_ids: List[int], user_id: int) -> int:
        if not portal_item_ids:
            return 0
        stmt = (
            update(RevPortalTransactionStaging)
            .where(RevPortalTransactionStaging.portal_item_id.in_(portal_item_ids))
            .values(dept_validated=True, dept_validated_by=user_id, dept_validated_at=func.clock_timestamp())
        )
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount
