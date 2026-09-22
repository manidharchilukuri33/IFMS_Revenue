from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text, Date
from app.models.devolution import RevDevolutionClaim, RevDevolutionComputation, RevDevolutionAdvice
from app.models.masters import RevDevolutionRule, RevLocalBody
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
        query = select(RevDevolutionClaim)

        if local_body_id:
            query = query.where(RevDevolutionClaim.local_body_id == local_body_id)
        if status:
            query = query.where(RevDevolutionClaim.status == status)
        if search:
            query = query.where(RevDevolutionClaim.claim_no.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(RevDevolutionClaim.claim_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        claims = result.scalars().all()

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
            "items": claims,
            "summary": {
                "total_claims": sum_res.total_claims if sum_res else 0,
                "total_collections": sum_res.total_collections if sum_res else Decimal("0.00"),
                "total_entitled": sum_res.total_entitled if sum_res else Decimal("0.00"),
                "total_claimed": sum_res.total_claimed if sum_res else Decimal("0.00"),
                "total_approved": sum_res.total_approved if sum_res else Decimal("0.00"),
            }
        }

    @staticmethod
    async def create_devolution_claim(
        db: AsyncSession,
        req: DevolutionClaimCreate,
        user_id: int,
    ) -> RevDevolutionClaim:
        # Find matching devolution rule
        rule = None
        if req.dev_rule_id:
            rule = await db.get(RevDevolutionRule, req.dev_rule_id)
        else:
            rule_query = select(RevDevolutionRule).where(
                and_(
                    RevDevolutionRule.local_body_id == req.local_body_id,
                    RevDevolutionRule.source_id == req.source_id,
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
                func.cast(RevReconResult.created_at, Date) >= req.period_from,
                func.cast(RevReconResult.created_at, Date) <= req.period_to,
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
        variance = (req.claimed_amount or Decimal("0.00")) - computed_entitlement

        # Generate claim no
        seq_res = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "DEVOLUTION_CLAIM_SEQ", "prefix": "DEV", "fy": "2026-27"}
        )
        claim_no = seq_res.scalar() or f"DEV/{datetime.now().strftime('%Y%m%d%H%M%S')}"

        claim = RevDevolutionClaim(
            claim_no=claim_no,
            local_body_id=req.local_body_id,
            source_id=req.source_id,
            receipt_head_id=req.receipt_head_id or 1,
            dev_rule_id=rule.dev_rule_id if rule else None,
            period_from=req.period_from,
            period_to=req.period_to,
            eligible_collections=total_eligible,
            share_pct=share_pct,
            computed_entitlement=computed_entitlement,
            claimed_amount=req.claimed_amount or computed_entitlement,
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
            "body_code": lb.body_code if lb else "",
            "body_name": lb.body_name if lb else "",
            "body_type": lb.body_type if lb else "",
            "district_name": lb.district_name if lb else "",
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

        # Generate bill & advice numbers
        seq_bill = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "REFUND_BILL_SEQ", "prefix": "DEVB", "fy": "2026-27"}
        )
        bill_no = seq_bill.scalar()

        seq_adv = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "DEVOLUTION_CLAIM_SEQ", "prefix": "ADV", "fy": "2026-27"}
        )
        advice_no = seq_adv.scalar()

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
