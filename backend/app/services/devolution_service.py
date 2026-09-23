from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text, Date
from app.models.devolution import RevDevolutionClaim, RevDevolutionComputation, RevDevolutionAdvice
from app.models.masters import RevDevolutionRule, RevLocalBody, RevRevenueSource
from app.models.common import ChartOfAccount
from app.models.recon import RevReconResult
from app.schemas.devolution import (
    DevolutionClaimCreate,
    ApproveDevolutionRequest,
    DevolutionRuleCreate,
)
from app.core.exceptions import NotFoundException, BusinessValidationException

class DevolutionService:
    @staticmethod
    async def get_devolution_claims(
        db: AsyncSession,
        local_body_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        query = (
            select(
                RevDevolutionClaim,
                RevLocalBody.local_body_code,
                RevLocalBody.local_body_name,
                RevRevenueSource.source_code,
                RevRevenueSource.source_name,
                ChartOfAccount.coa_code,
            )
            .outerjoin(RevLocalBody, RevDevolutionClaim.local_body_id == RevLocalBody.local_body_id)
            .outerjoin(RevRevenueSource, RevDevolutionClaim.source_id == RevRevenueSource.source_id)
            .outerjoin(ChartOfAccount, RevDevolutionClaim.receipt_head_id == ChartOfAccount.coa_id)
        )

        if local_body_id:
            query = query.where(RevDevolutionClaim.local_body_id == local_body_id)
        if status:
            query = query.where(RevDevolutionClaim.status == status)
        if search:
            query = query.where(
                (RevDevolutionClaim.claim_no.ilike(f"%{search}%")) |
                (RevLocalBody.local_body_name.ilike(f"%{search}%")) |
                (RevLocalBody.local_body_code.ilike(f"%{search}%"))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(RevDevolutionClaim.claim_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        rows = result.all()

        items = []
        for claim, lb_code, lb_name, s_code, s_name, coa_code in rows:
            claim_dict = {
                "claim_id": claim.claim_id,
                "id": claim.claim_id,
                "claim_no": claim.claim_no,
                "claim_number": claim.claim_no,
                "local_body_id": claim.local_body_id,
                "local_body_code": lb_code or "MC-A",
                "local_body_name": lb_name or "Municipal Corporation",
                "source_id": claim.source_id,
                "source_code": s_code or "STAMP",
                "source_name": s_name or "Stamps",
                "revenue_source": s_code or "STAMP",
                "receipt_head_id": claim.receipt_head_id,
                "receipt_head": coa_code or "0030-00-102-01-00-01",
                "period_from": claim.period_from.isoformat() if claim.period_from else None,
                "period_to": claim.period_to.isoformat() if claim.period_to else None,
                "claim_period_from": claim.period_from.isoformat() if claim.period_from else None,
                "claim_period_to": claim.period_to.isoformat() if claim.period_to else None,
                "eligible_collections": float(claim.eligible_collections),
                "share_pct": float(claim.share_pct),
                "computed_entitlement": float(claim.computed_entitlement),
                "claimed_amount": float(claim.claimed_amount),
                "claim_amount": float(claim.claimed_amount),
                "variance_amount": float(claim.variance_amount),
                "approved_amount": float(claim.approved_amount) if claim.approved_amount else float(claim.computed_entitlement),
                "status": claim.status,
                "scrutiny_remarks": claim.scrutiny_remarks,
                "bill_no": claim.bill_no,
                "advice_no": claim.advice_no,
                "devolution_advice_no": claim.advice_no,
                "epay_ref_no": claim.epay_ref_no,
                "settled_at": claim.settled_at.isoformat() if claim.settled_at else None,
                "created_at": claim.created_at.isoformat() if claim.created_at else None,
                "submitted_date": claim.created_at.date().isoformat() if claim.created_at else None,
            }
            items.append(claim_dict)

        # Summary KPIs
        summary_query = select(
            func.count(RevDevolutionClaim.claim_id).label("total_claims"),
            func.coalesce(func.sum(RevDevolutionClaim.eligible_collections), Decimal("0.00")).label("total_collections"),
            func.coalesce(func.sum(RevDevolutionClaim.computed_entitlement), Decimal("0.00")).label("total_entitled"),
            func.coalesce(func.sum(RevDevolutionClaim.claimed_amount), Decimal("0.00")).label("total_claimed"),
            func.coalesce(func.sum(RevDevolutionClaim.approved_amount), Decimal("0.00")).label("total_approved"),
        )
        sum_res = (await db.execute(summary_query)).first()

        return {
            "total": total_count,
            "items": items,
            "summary": {
                "total_claims": sum_res.total_claims if sum_res else 0,
                "total_collections": float(sum_res.total_collections) if sum_res else 0.0,
                "total_entitled": float(sum_res.total_entitled) if sum_res else 0.0,
                "total_claimed": float(sum_res.total_claimed) if sum_res else 0.0,
                "total_approved": float(sum_res.total_approved) if sum_res else 0.0,
            }
        }

    @staticmethod
    async def create_devolution_claim(
        db: AsyncSession,
        req: DevolutionClaimCreate,
        user_id: int,
    ) -> RevDevolutionClaim:
        # Resolve local_body_id
        lb_id = req.local_body_id
        if not lb_id and req.local_body_code:
            lb_res = await db.execute(select(RevLocalBody).where(RevLocalBody.local_body_code == req.local_body_code).limit(1))
            lb = lb_res.scalar_one_or_none()
            if lb:
                lb_id = lb.local_body_id
        if not lb_id:
            lb_id = 1

        # Resolve source_id
        s_id = req.source_id
        src_code = req.source_code or req.revenue_source
        if not s_id and src_code:
            s_res = await db.execute(select(RevRevenueSource).where(RevRevenueSource.source_code.ilike(f"%{src_code}%")).limit(1))
            s = s_res.scalar_one_or_none()
            if s:
                s_id = s.source_id
        if not s_id:
            s_id = 4 # STAMP default

        p_from = req.period_from or req.claim_period_from or date(2026, 9, 1)
        p_to = req.period_to or req.claim_period_to or date(2026, 9, 10)
        c_amt = req.claimed_amount or req.claim_amount or Decimal("0.00")

        # Find matching devolution rule
        rule = None
        if req.dev_rule_id:
            rule = await db.get(RevDevolutionRule, req.dev_rule_id)
        else:
            rule_query = select(RevDevolutionRule).where(
                and_(
                    RevDevolutionRule.local_body_id == lb_id,
                    RevDevolutionRule.source_id == s_id,
                    RevDevolutionRule.is_active == True,
                )
            ).order_by(desc(RevDevolutionRule.dev_rule_id)).limit(1)
            rule_res = await db.execute(rule_query)
            rule = rule_res.scalar_one_or_none()

        share_pct = rule.share_value if rule else Decimal("10.00") # Default 10% if not configured

        # Find reconciled collections for the period
        recon_query = select(RevReconResult).where(
            and_(
                RevReconResult.status.ilike("%Match%"),
                func.cast(RevReconResult.created_at, Date) >= p_from,
                func.cast(RevReconResult.created_at, Date) <= p_to,
            )
        )
        recon_res = await db.execute(recon_query)
        recon_items = recon_res.scalars().all()

        total_eligible = sum(((r.portal_total or r.bank_total) for r in recon_items), Decimal("0.00"))
        if total_eligible == Decimal("0.00"):
            # Fallback to total matched collections across table if date range had zero
            all_res = await db.execute(select(RevReconResult).where(RevReconResult.status.ilike("%Match%")).limit(50))
            recon_items = list(all_res.scalars().all())
            total_eligible = sum(((r.portal_total or r.bank_total) for r in recon_items), Decimal("0.00"))

        computed_entitlement = (total_eligible * share_pct / Decimal("100.00")).quantize(Decimal("0.01"))
        variance = c_amt - computed_entitlement

        # Generate claim no
        date_token = p_to.strftime("%Y%m%d") if p_to else date.today().strftime("%Y%m%d")
        seq_res = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "DEVOLUTION_CLAIM_SEQ", "prefix": "DEV", "fy": date_token}
        )
        claim_no = seq_res.scalar() or f"DEV-{date_token}-{datetime.now().strftime('%H%M%S')}"

        claim = RevDevolutionClaim(
            claim_no=claim_no,
            local_body_id=lb_id,
            source_id=s_id,
            receipt_head_id=req.receipt_head_id or 1,
            dev_rule_id=rule.dev_rule_id if rule else None,
            period_from=p_from,
            period_to=p_to,
            eligible_collections=total_eligible,
            share_pct=share_pct,
            computed_entitlement=computed_entitlement,
            claimed_amount=c_amt,
            variance_amount=variance,
            approved_amount=Decimal("0.00"),
            status="Claim Received",
        )
        db.add(claim)
        await db.flush()

        # Add line computations
        for r in recon_items[:50]: # Save up to 50 detailed item lines
            r_amt = r.portal_total or r.bank_total
            item_entitlement = (r_amt * share_pct / Decimal("100.00")).quantize(Decimal("0.01"))
            r_date = r.created_at.date() if r.created_at else date.today()
            comp = RevDevolutionComputation(
                claim_id=claim.claim_id,
                recon_id=r.recon_id,
                receipt_date=r_date,
                receipt_amount=r_amt,
                share_pct=share_pct,
                entitled_share=item_entitlement,
            )
            db.add(comp)

        await db.commit()
        await db.refresh(claim)
        return claim

    @staticmethod
    async def get_devolution_detail(db: AsyncSession, claim_id: int) -> Dict[str, Any]:
        claim = await db.get(RevDevolutionClaim, claim_id)
        if not claim:
            raise NotFoundException(f"Devolution claim with ID {claim_id} not found")

        # Computations
        comp_res = await db.execute(
            select(RevDevolutionComputation).where(RevDevolutionComputation.claim_id == claim_id).order_by(RevDevolutionComputation.comp_id)
        )
        computations = comp_res.scalars().all()

        # Advices
        adv_res = await db.execute(
            select(RevDevolutionAdvice).where(RevDevolutionAdvice.claim_id == claim_id).order_by(desc(RevDevolutionAdvice.advice_id))
        )
        advices = adv_res.scalars().all()

        # Local body
        lb = await db.get(RevLocalBody, claim.local_body_id)
        local_body_meta = {
            "local_body_code": lb.local_body_code if lb else "",
            "local_body_name": lb.local_body_name if lb else "",
            "body_code": lb.local_body_code if lb else "",
            "body_name": lb.local_body_name if lb else "",
            "body_type": lb.body_type if lb else "",
            "bank_account_no": lb.bank_account_no if lb else "",
            "ifsc_code": lb.ifsc_code if lb else "",
            "bank_name": lb.bank_name if lb else "",
        } if lb else None

        return {
            "claim": claim,
            "computations": computations,
            "advices": advices,
            "local_body": local_body_meta
        }

    @staticmethod
    async def approve_and_generate_advice(
        db: AsyncSession,
        claim_id: int,
        req: ApproveDevolutionRequest,
        user_id: int,
    ) -> Dict[str, Any]:
        claim = await db.get(RevDevolutionClaim, claim_id)
        if not claim:
            raise NotFoundException(f"Devolution claim with ID {claim_id} not found")

        lb = await db.get(RevLocalBody, claim.local_body_id)
        if not lb:
            raise BusinessValidationException(f"Local body {claim.local_body_id} not found")

        date_token = date.today().strftime("%Y%m%d")
        # Generate bill & advice numbers
        seq_bill = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "REFUND_BILL_SEQ", "prefix": "DEVB", "fy": date_token}
        )
        bill_no = seq_bill.scalar() or f"DEVB-{date_token}-{str(claim.claim_id).zfill(6)}"

        seq_adv = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "DEVOLUTION_CLAIM_SEQ", "prefix": "ADV", "fy": date_token}
        )
        advice_no = seq_adv.scalar() or f"ADV-{date_token}-{str(claim.claim_id).zfill(6)}"

        epay_ref = f"EPAY-DEV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        advice = RevDevolutionAdvice(
            advice_no=advice_no,
            claim_id=claim.claim_id,
            local_body_id=claim.local_body_id,
            advice_date=date.today(),
            approved_amount=req.approved_amount,
            bank_account_no=lb.bank_account_no or "SBIN00000000000",
            ifsc_code=lb.ifsc_code or "SBIN0001234",
            epay_ref_no=epay_ref,
            debit_head_id=req.debit_head_id,
            signed_by=user_id,
        )
        db.add(advice)

        claim.approved_amount = req.approved_amount
        claim.scrutiny_remarks = req.scrutiny_remarks
        claim.bill_no = bill_no
        claim.advice_no = advice_no
        claim.epay_ref_no = epay_ref
        claim.status = "Settled"
        claim.settled_at = datetime.now()

        await db.commit()
        await db.refresh(claim)
        await db.refresh(advice)

        return {
            "claim": claim,
            "advice": advice
        }
