from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from app.models.sla import RevPenalClaim, RevPenalLetter, RevPenalBankResponse, RevPenalWaiver
from app.models.masters import RevAgencyBank
from app.schemas.sla import (
    DemandLetterRequest,
    BankResponseRequest,
    PenaltyWaiverRequest,
)
from app.core.exceptions import NotFoundException, BusinessValidationException

class SLAService:
    @staticmethod
    async def get_penal_claims(
        db: AsyncSession,
        bank_id: Optional[int] = None,
        status: Optional[str] = None,
        min_delay_days: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        query = select(RevPenalClaim)

        if bank_id:
            query = query.where(RevPenalClaim.bank_id == bank_id)
        if status:
            query = query.where(RevPenalClaim.status == status)
        if min_delay_days is not None:
            query = query.where(RevPenalClaim.delay_days >= min_delay_days)
        if search:
            query = query.where(RevPenalClaim.claim_no.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(RevPenalClaim.claim_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        claims = result.scalars().all()

        # Summary KPIs
        summary_query = select(
            func.count(RevPenalClaim.claim_id).label("total_claims"),
            func.coalesce(func.sum(RevPenalClaim.penal_interest_computed), Decimal("0.00")).label("total_computed"),
            func.coalesce(func.sum(RevPenalClaim.penal_interest_recovered), Decimal("0.00")).label("total_recovered"),
            func.coalesce(func.sum(RevPenalClaim.penal_interest_waived), Decimal("0.00")).label("total_waived"),
            func.coalesce(func.sum(RevPenalClaim.penal_interest_outstanding), Decimal("0.00")).label("total_outstanding"),
        )
        sum_res = (await db.execute(summary_query)).first()

        return {
            "total": total_count,
            "items": claims,
            "summary": {
                "total_claims": sum_res.total_claims if sum_res else 0,
                "total_computed": sum_res.total_computed if sum_res else Decimal("0.00"),
                "total_recovered": sum_res.total_recovered if sum_res else Decimal("0.00"),
                "total_waived": sum_res.total_waived if sum_res else Decimal("0.00"),
                "total_outstanding": sum_res.total_outstanding if sum_res else Decimal("0.00"),
            }
        }

    @staticmethod
    async def get_penal_claim_detail(db: AsyncSession, claim_id: int) -> Dict[str, Any]:
        claim = await db.get(RevPenalClaim, claim_id)
        if not claim:
            raise NotFoundException(f"Penal claim with ID {claim_id} not found")

        # Get letters
        letters_res = await db.execute(
            select(RevPenalLetter).where(RevPenalLetter.claim_id == claim_id).order_by(desc(RevPenalLetter.letter_id))
        )
        letters = letters_res.scalars().all()

        # Get responses
        responses_res = await db.execute(
            select(RevPenalBankResponse).where(RevPenalBankResponse.claim_id == claim_id).order_by(desc(RevPenalBankResponse.response_id))
        )
        responses = responses_res.scalars().all()

        # Get waivers
        waivers_res = await db.execute(
            select(RevPenalWaiver).where(RevPenalWaiver.claim_id == claim_id).order_by(desc(RevPenalWaiver.waiver_id))
        )
        waivers = waivers_res.scalars().all()

        # Bank info
        bank = await db.get(RevAgencyBank, claim.bank_id)
        bank_context = {
            "bank_name": bank.bank_name if bank else "",
            "bank_code": bank.bank_code if bank else "",
            "nodal_branch_name": bank.nodal_branch_name if bank else "",
        } if bank else None

        return {
            "claim": claim,
            "letters": letters,
            "responses": responses,
            "waivers": waivers,
            "bank_context": bank_context
        }

    @staticmethod
    async def issue_demand_letter(
        db: AsyncSession,
        claim_id: int,
        req: DemandLetterRequest,
        user_id: int,
    ) -> RevPenalLetter:
        claim = await db.get(RevPenalClaim, claim_id)
        if not claim:
            raise NotFoundException(f"Penal claim with ID {claim_id} not found")

        # Generate letter number
        seq_res = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "PENAL_LETTER_SEQ", "prefix": "DL", "fy": "2026-27"}
        )
        letter_no = seq_res.scalar() or f"DL-SLA-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        content = req.letter_content or req.remarks or f"Statutory Demand Notice for Penal Interest of Rs. {claim.penal_interest_outstanding} issued to {req.recipient_name or 'Bank Nodal Branch'}."

        letter = RevPenalLetter(
            letter_no=letter_no,
            claim_id=claim.claim_id,
            bank_id=claim.bank_id,
            issued_date=date.today(),
            total_demand_amount=claim.penal_interest_outstanding,
            letter_content=content,
            issued_by=user_id,
        )
        db.add(letter)
        await db.flush()

        claim.status = "DEMAND_ISSUED"
        claim.letter_id = letter.letter_id
        await db.commit()
        await db.refresh(letter)
        return letter

    @staticmethod
    async def record_bank_response(
        db: AsyncSession,
        claim_id: int,
        req: BankResponseRequest,
        user_id: int,
    ) -> Dict[str, Any]:
        claim = await db.get(RevPenalClaim, claim_id)
        if not claim:
            raise NotFoundException(f"Penal claim with ID {claim_id} not found")

        r_date = req.response_date or req.remittance_date or date.today()
        rem_amt = req.remitted_amount if (req.remitted_amount is not None and req.remitted_amount > 0) else (req.recovered_amount or Decimal("0.00"))
        remarks = req.bank_remarks or req.remarks or (f"Bank UTR: {req.bank_reference_no}" if req.bank_reference_no else "Bank recovery recorded")

        response = RevPenalBankResponse(
            claim_id=claim.claim_id,
            response_date=r_date,
            response_type=req.response_type or "PAYMENT",
            remitted_amount=rem_amt,
            bank_remarks=remarks,
            recorded_by=user_id,
        )
        db.add(response)

        if rem_amt > 0:
            claim.penal_interest_recovered += rem_amt
            claim.penal_interest_outstanding = max(
                Decimal("0.00"),
                claim.penal_interest_computed - claim.penal_interest_recovered - claim.penal_interest_waived
            )
            if claim.penal_interest_outstanding == Decimal("0.00"):
                claim.status = "RECOVERED"
            else:
                claim.status = "PARTIALLY_RECOVERED"

        await db.commit()
        await db.refresh(response)
        await db.refresh(claim)
        return {
            "response_id": response.response_id,
            "claim_id": claim.claim_id,
            "claim_no": claim.claim_no,
            "penal_interest_recovered": float(claim.penal_interest_recovered),
            "penal_interest_outstanding": float(claim.penal_interest_outstanding),
            "status": claim.status,
            "remitted_amount": float(rem_amt),
        }

    @staticmethod
    async def approve_penalty_waiver(
        db: AsyncSession,
        claim_id: int,
        req: PenaltyWaiverRequest,
        user_id: int,
    ) -> RevPenalWaiver:
        claim = await db.get(RevPenalClaim, claim_id)
        if not claim:
            raise NotFoundException(f"Penal claim with ID {claim_id} not found")

        if req.waived_amount > claim.penal_interest_outstanding:
            raise BusinessValidationException(
                f"Waiver amount ₹{req.waived_amount} cannot exceed outstanding amount ₹{claim.penal_interest_outstanding}"
            )

        waiver = RevPenalWaiver(
            claim_id=claim.claim_id,
            waived_amount=req.waived_amount,
            waiver_ground=req.waiver_ground,
            sanction_order_ref=req.sanction_order_ref,
            waiver_remarks=req.waiver_remarks,
            approved_by=user_id,
        )
        db.add(waiver)

        claim.penal_interest_waived += req.waived_amount
        claim.penal_interest_outstanding = max(
            Decimal("0.00"),
            claim.penal_interest_computed - claim.penal_interest_recovered - claim.penal_interest_waived
        )
        if claim.penal_interest_outstanding == Decimal("0.00"):
            claim.status = "WAIVED"
        else:
            claim.status = "PARTIALLY_RECOVERED"

        await db.commit()
        await db.refresh(waiver)
        return waiver
