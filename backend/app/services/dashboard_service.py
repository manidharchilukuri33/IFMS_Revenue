from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from app.models import (
    RevPortalTransactionStaging, RevAgencyBankScrollStaging, RevRbiLuggageStaging,
    RevReconResult, RevException, RevPenalClaim, RevRefundCase,
    RevDevolutionClaim, AccountVoucher, RevSuspenseRegister
)

class DashboardService:
    @staticmethod
    async def get_dashboard_summary(
        db: AsyncSession,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        # 1. Gross Collections from valid Portal records
        portal_sum_q = select(
            func.count(RevPortalTransactionStaging.portal_item_id).label("total_receipts"),
            func.coalesce(func.sum(RevPortalTransactionStaging.amount), Decimal("0.00")).label("gross_amount")
        ).where(RevPortalTransactionStaging.is_valid == True)
        p_res = (await db.execute(portal_sum_q)).first()
        gross_amount = p_res.gross_amount if p_res else Decimal("0.00")
        total_receipts = p_res.total_receipts if p_res else 0

        # 2. Recon breakdown
        recon_q = select(
            func.count(RevReconResult.recon_id).label("total_recons"),
            func.coalesce(func.sum(RevReconResult.portal_total), Decimal("0.00")).label("total_portal"),
            func.coalesce(func.sum(RevReconResult.portal_total).filter(RevReconResult.status == "Matched"), Decimal("0.00")).label("matched_amount"),
            func.count(RevReconResult.recon_id).filter(RevReconResult.status == "Matched").label("matched_count"),
            func.coalesce(func.sum(RevReconResult.portal_total).filter(RevReconResult.status != "Matched"), Decimal("0.00")).label("unmatched_amount"),
            func.count(RevReconResult.recon_id).filter(RevReconResult.status != "Matched").label("unmatched_count"),
        )
        r_res = (await db.execute(recon_q)).first()
        matched_amount = r_res.matched_amount if r_res else Decimal("0.00")
        matched_count = r_res.matched_count if r_res else 0
        unmatched_amount = r_res.unmatched_amount if r_res else Decimal("0.00")
        unmatched_count = r_res.unmatched_count if r_res else 0

        # Match rate
        match_rate = round((float(matched_amount) / float(gross_amount) * 100), 1) if gross_amount > 0 else 0.0

        # 3. Open Exceptions
        exc_q = select(
            func.count(RevException.exception_id).label("open_exceptions_count"),
            func.coalesce(func.sum(RevReconResult.portal_total), Decimal("0.00")).label("open_exceptions_amount")
        ).select_from(RevException).join(RevReconResult, RevReconResult.recon_id == RevException.recon_id).where(RevException.status.in_(["Open", "Assigned", "Escalated"]))
        e_res = (await db.execute(exc_q)).first()

        # 4. Penal Claims
        penal_q = select(
            func.count(RevPenalClaim.claim_id).label("penal_claims_count"),
            func.coalesce(func.sum(RevPenalClaim.penal_interest_computed), Decimal("0.00")).label("penal_computed"),
            func.coalesce(func.sum(RevPenalClaim.penal_interest_recovered), Decimal("0.00")).label("penal_recovered"),
            func.coalesce(func.sum(RevPenalClaim.penal_interest_outstanding), Decimal("0.00")).label("penal_outstanding")
        )
        pen_res = (await db.execute(penal_q)).first()

        # 5. Refunds
        refund_q = select(
            func.count(RevRefundCase.refund_id).label("pending_refunds_count"),
            func.coalesce(func.sum(RevRefundCase.refundable_amount), Decimal("0.00")).label("pending_refunds_amount")
        ).where(RevRefundCase.status != "Paid")
        ref_res = (await db.execute(refund_q)).first()

        # 6. Devolution
        dev_q = select(
            func.count(RevDevolutionClaim.claim_id).label("devolution_count"),
            func.coalesce(func.sum(RevDevolutionClaim.computed_entitlement), Decimal("0.00")).label("devolution_entitlement"),
            func.coalesce(func.sum(RevDevolutionClaim.approved_amount), Decimal("0.00")).label("devolution_approved")
        ).where(RevDevolutionClaim.status != "Settled")
        dev_res = (await db.execute(dev_q)).first()

        # 7. Vouchers
        vch_q = select(
            func.count(AccountVoucher.voucher_id).label("draft_vouchers_count"),
            func.coalesce(func.sum(AccountVoucher.amount), Decimal("0.00")).label("draft_vouchers_amount")
        ).where(AccountVoucher.status == "Draft")
        vch_res = (await db.execute(vch_q)).first()

        # 8. Source-wise distribution
        src_sql = text("""
            SELECT 
                s.source_code,
                s.source_name,
                COALESCE(SUM(p.amount), 0.00) as total_amt,
                COALESCE(SUM(CASE WHEN r.status = 'Matched' THEN p.amount ELSE 0.00 END), 0.00) as matched_amt
            FROM ifms_budget.rev_revenue_source s
            LEFT JOIN ifms_budget.rev_portal_transaction_staging p ON p.revenue_source = s.source_code AND p.is_valid = true
            LEFT JOIN ifms_budget.rev_recon_result r ON r.challan_no = p.challan_no
            GROUP BY s.source_code, s.source_name
            ORDER BY total_amt DESC
        """)
        src_res = await db.execute(src_sql)
        source_breakdown = []
        for row in src_res:
            source_breakdown.append({
                "source_code": row.source_code,
                "source_name": row.source_name,
                "total_amount": float(row.total_amt),
                "matched_amount": float(row.matched_amt),
            })

        # 9. Daily Collections vs Reconciled trend (recent 7 dates)
        daily_sql = text("""
            SELECT 
                p.payment_date,
                COALESCE(SUM(p.amount), 0.00) as gross_amt,
                COALESCE(SUM(CASE WHEN r.status = 'Matched' THEN p.amount ELSE 0.00 END), 0.00) as matched_amt
            FROM ifms_budget.rev_portal_transaction_staging p
            LEFT JOIN ifms_budget.rev_recon_result r ON r.challan_no = p.challan_no
            WHERE p.is_valid = true
            GROUP BY p.payment_date
            ORDER BY p.payment_date DESC
            LIMIT 7
        """)
        daily_res = await db.execute(daily_sql)
        daily_trend = []
        for row in reversed(daily_res.all()):
            daily_trend.append({
                "date": row.payment_date.isoformat() if row.payment_date else "",
                "gross": float(row.gross_amt),
                "matched": float(row.matched_amt),
            })

        return {
            "kpis": {
                "gross_collections": float(gross_amount),
                "total_receipts": total_receipts,
                "matched_amount": float(matched_amount),
                "matched_count": matched_count,
                "unmatched_amount": float(unmatched_amount),
                "unmatched_count": unmatched_count,
                "match_rate": match_rate,
                "open_exceptions_count": e_res.open_exceptions_count if e_res else 0,
                "open_exceptions_amount": float(e_res.open_exceptions_amount if e_res else 0),
                "penal_interest_computed": float(pen_res.penal_computed if pen_res else 0),
                "penal_interest_recovered": float(pen_res.penal_recovered if pen_res else 0),
                "penal_interest_outstanding": float(pen_res.penal_outstanding if pen_res else 0),
                "pending_refunds_count": ref_res.pending_refunds_count if ref_res else 0,
                "pending_refunds_amount": float(ref_res.pending_refunds_amount if ref_res else 0),
                "devolution_payable": float(dev_res.devolution_entitlement if dev_res else 0),
                "draft_vouchers_count": vch_res.draft_vouchers_count if vch_res else 0,
                "draft_vouchers_amount": float(vch_res.draft_vouchers_amount if vch_res else 0),
            },
            "source_breakdown": source_breakdown,
            "daily_trend": daily_trend,
        }
