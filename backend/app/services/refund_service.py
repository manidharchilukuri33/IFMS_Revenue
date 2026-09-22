from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from app.models.refunds import RevRefundCase, RevRefundVerification, RevRefundBill
from app.models.recon import RevReconResult
from app.models.staging import RevPortalTransactionStaging
from app.schemas.refunds import (
    RefundCaseCreate,
    AdvanceStageRequest,
)
from app.core.exceptions import NotFoundException, BusinessValidationException

NON_JUDICIAL_STAGES = [
    (1, "Application Submission", "DDO"),
    (2, "Document Verification", "DDO"),
    (3, "SHCIL / Sub-Registrar Verification", "PAO_MAKER"),
    (4, "Challan Defacement & Register Entry", "DDO"),
    (5, "Sanctioning Authority Order", "FINANCE"),
    (6, "Refund Bill Preparation", "PAO_MAKER"),
    (7, "PAO Maker Scrutiny", "PAO_MAKER"),
    (8, "PAO Checker Approval", "PAO_CHECK"),
    (9, "e-Payment Instruction Release", "BANK_OPS"),
    (10, "Payment Settlement Completed", "TRE_ADMIN"),
]

JUDICIAL_STAGES = [
    (1, "Application & Court Order Submission", "DDO"),
    (2, "Court Certificate Verification", "PAO_MAKER"),
    (3, "Challan Defacement", "DDO"),
    (4, "Refund Bill Preparation", "PAO_MAKER"),
    (5, "PAO Checker Approval", "PAO_CHECK"),
    (6, "Payment Release (SBI CMP / RBI e-Kuber)", "BANK_OPS"),
    (7, "Settlement Completed", "TRE_ADMIN"),
]

class RefundService:
    @staticmethod
    async def get_refund_cases(
        db: AsyncSession,
        refund_type: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        query = select(RevRefundCase)

        if refund_type:
            query = query.where(RevRefundCase.refund_type == refund_type)
        if status:
            query = query.where(RevRefundCase.status == status)
        if search:
            query = query.where(
                (RevRefundCase.case_no.ilike(f"%{search}%")) |
                (RevRefundCase.applicant_name.ilike(f"%{search}%")) |
                (RevRefundCase.original_challan_no.ilike(f"%{search}%"))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(RevRefundCase.refund_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        cases = result.scalars().all()

        # Summary counts
        summary_query = select(
            func.count(RevRefundCase.refund_id).label("total_cases"),
            func.coalesce(func.sum(RevRefundCase.claimed_amount), Decimal("0.00")).label("total_claimed"),
            func.coalesce(func.sum(RevRefundCase.refundable_amount), Decimal("0.00")).label("total_refundable"),
        )
        sum_res = (await db.execute(summary_query)).first()

        return {
            "total": total_count,
            "items": cases,
            "summary": {
                "total_cases": sum_res.total_cases if sum_res else 0,
                "total_claimed": sum_res.total_claimed if sum_res else Decimal("0.00"),
                "total_refundable": sum_res.total_refundable if sum_res else Decimal("0.00"),
            }
        }

    @staticmethod
    async def create_refund_case(
        db: AsyncSession,
        req: RefundCaseCreate,
        user_id: int,
    ) -> RevRefundCase:
        # Check if original challan exists in recon or staging
        recon_id = None
        reconciled_amt = Decimal("0.00")

        portal_res = await db.execute(
            select(RevPortalTransactionStaging).where(RevPortalTransactionStaging.challan_no == req.original_challan_no).limit(1)
        )
        portal_row = portal_res.scalar_one_or_none()
        if portal_row:
            reconciled_amt = portal_row.amount
            recon_res = await db.execute(
                select(RevReconResult).where(RevReconResult.challan_no == req.original_challan_no).limit(1)
            )
            recon_row = recon_res.scalar_one_or_none()
            if recon_row:
                recon_id = recon_row.recon_id
        else:
            recon_res = await db.execute(
                select(RevReconResult).where(RevReconResult.challan_no == req.original_challan_no).limit(1)
            )
            recon_row = recon_res.scalar_one_or_none()
            if recon_row:
                recon_id = recon_row.recon_id
                reconciled_amt = recon_row.portal_total or recon_row.bank_total or req.claimed_amount
            else:
                reconciled_amt = req.reconciled_original_amount or req.claimed_amount

        # Generate case number if not provided
        if req.case_no:
            case_no = req.case_no
        else:
            seq_res = await db.execute(
                text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
                {"seq_key": "REFUND_CASE_SEQ", "prefix": "REF", "fy": "2026-27"}
            )
            case_no = seq_res.scalar() or f"REF/2026/{datetime.now().strftime('%H%M%S')}"

        is_override = bool(req.override_reason)
        refundable_amt = req.claimed_amount

        stages = NON_JUDICIAL_STAGES if "NON_JUDICIAL" in req.refund_type.upper() else JUDICIAL_STAGES
        first_stage = stages[0]

        bank_acc = req.applicant_bank_acc or req.bank_account_no or "112233445566"
        ifsc = req.applicant_ifsc or req.ifsc_code or "SBIN0001234"
        e_stamp = req.e_stamp_cert_no or req.shcil_certificate_no

        refund_case = RevRefundCase(
            case_no=case_no,
            refund_type=req.refund_type,
            applicant_name=req.applicant_name,
            applicant_id_proof=req.applicant_id_proof or "AADHAAR",
            applicant_bank_acc=bank_acc,
            applicant_ifsc=ifsc,
            original_challan_no=req.original_challan_no,
            recon_id=recon_id,
            reconciled_original_amount=reconciled_amt,
            claimed_amount=req.claimed_amount,
            refundable_amount=refundable_amt,
            is_amount_override=is_override,
            override_reason=req.override_reason,
            e_stamp_cert_no=e_stamp,
            court_order_no=req.court_order_no,
            current_stage=first_stage[0],
            stage_name=first_stage[1],
            pending_role=first_stage[2],
            status="Submitted",
        )
        db.add(refund_case)
        await db.commit()
        await db.refresh(refund_case)
        return refund_case

    @staticmethod
    async def get_refund_detail(db: AsyncSession, refund_id: int) -> Dict[str, Any]:
        case = await db.get(RevRefundCase, refund_id)
        if not case:
            raise NotFoundException(f"Refund case with ID {refund_id} not found")

        # Verifications
        ver_res = await db.execute(
            select(RevRefundVerification).where(RevRefundVerification.refund_id == refund_id).order_by(desc(RevRefundVerification.verification_id))
        )
        verifications = ver_res.scalars().all()

        # Bills
        bill_res = await db.execute(
            select(RevRefundBill).where(RevRefundBill.refund_id == refund_id).order_by(desc(RevRefundBill.bill_id))
        )
        bills = bill_res.scalars().all()

        stages = NON_JUDICIAL_STAGES if case.refund_type == "NON_JUDICIAL_STAMP" else JUDICIAL_STAGES
        checklist = [
            f"Stage {s[0]}: {s[1]} ({'Completed' if s[0] < case.current_stage else ('In Progress' if s[0] == case.current_stage and case.status != 'Rejected' else 'Pending')})"
            for s in stages
        ]

        timeline = [
            {
                "date": case.created_at.isoformat() if case.created_at else None,
                "title": "Application Submitted",
                "description": f"Filed by {case.applicant_name} for ₹{case.claimed_amount}"
            }
        ]
        for v in verifications:
            timeline.append({
                "date": v.verified_at.isoformat() if v.verified_at else None,
                "title": f"Verification: {v.verification_type} ({v.verification_result})",
                "description": v.verification_remarks
            })
        for b in bills:
            timeline.append({
                "date": b.prepared_at.isoformat() if b.prepared_at else None,
                "title": f"Refund Bill {b.bill_no} Prepared",
                "description": f"Bill Amount: ₹{b.bill_amount}, Status: {b.status}"
            })
        if case.pao_approved_at:
            timeline.append({
                "date": case.pao_approved_at.isoformat(),
                "title": "PAO Sanction Approved",
                "description": case.pao_remarks or "Approved by PAO Checker"
            })
        if case.paid_at:
            timeline.append({
                "date": case.paid_at.isoformat(),
                "title": "Payment Released & Settled",
                "description": f"Ref: {case.epay_ref_no}"
            })

        return {
            "case": case,
            "verifications": verifications,
            "bills": bills,
            "checklist": checklist,
            "timeline": timeline
        }

    @staticmethod
    async def advance_stage(
        db: AsyncSession,
        refund_id: int,
        req: AdvanceStageRequest,
        user_id: int,
    ) -> RevRefundCase:
        case = await db.get(RevRefundCase, refund_id)
        if not case:
            raise NotFoundException(f"Refund case with ID {refund_id} not found")

        stages = NON_JUDICIAL_STAGES if case.refund_type == "NON_JUDICIAL_STAMP" else JUDICIAL_STAGES
        total_stages = len(stages)

        if req.action == "REJECT":
            case.status = "Rejected"
            case.pending_role = "NONE"
            if req.remarks:
                ver = RevRefundVerification(
                    refund_id=case.refund_id,
                    verification_type=req.verification_type or "REJECTION",
                    verification_result="Invalid",
                    authority_name=req.authority_name,
                    verification_remarks=req.remarks,
                    verified_by=user_id,
                )
                db.add(ver)
            await db.commit()
            await db.refresh(case)
            return case

        if req.action == "RAISE_DEFICIENCY":
            case.status = "Deficiency Raised"
            case.pending_role = "APPLICANT"
            if req.remarks:
                ver = RevRefundVerification(
                    refund_id=case.refund_id,
                    verification_type="DEFICIENCY",
                    verification_result="Pending Rectification",
                    authority_name=req.authority_name,
                    verification_remarks=req.remarks,
                    verified_by=user_id,
                )
                db.add(ver)
            await db.commit()
            await db.refresh(case)
            return case

        if req.action == "VERIFY":
            ver = RevRefundVerification(
                refund_id=case.refund_id,
                verification_type=req.verification_type or "VERIFICATION",
                verification_result=req.verification_result or "Valid",
                authority_name=req.authority_name,
                verification_remarks=req.remarks,
                verified_by=user_id,
            )
            db.add(ver)
            # Advance stage
            if case.current_stage < total_stages:
                case.current_stage += 1
                next_stage_meta = stages[case.current_stage - 1]
                case.stage_name = next_stage_meta[1]
                case.pending_role = next_stage_meta[2]
                case.status = "Under Verification"

        elif req.action == "PREPARE_BILL":
            # Generate bill no
            seq_res = await db.execute(
                text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
                {"seq_key": "REFUND_BILL_SEQ", "prefix": "RB", "fy": "2026-27"}
            )
            bill_no = seq_res.scalar()

            bill = RevRefundBill(
                bill_no=bill_no,
                refund_id=case.refund_id,
                department_id=1, # Default department or passed
                ddo_id=req.ddo_id or 1,
                pao_code="PAO-01",
                bill_amount=case.refundable_amount,
                debit_head_id=req.debit_head_id or 1,
                status="PREPARED",
                prepared_by=user_id,
            )
            db.add(bill)
            case.refund_bill_no = bill_no
            case.bill_prepared_by = user_id
            case.bill_prepared_at = datetime.now()
            # Advance to PAO Checker stage
            if case.current_stage < total_stages:
                case.current_stage += 1
                next_stage_meta = stages[case.current_stage - 1]
                case.stage_name = next_stage_meta[1]
                case.pending_role = next_stage_meta[2]
                case.status = "Bill Prepared"

        elif req.action == "APPROVE_PAO":
            # Update bill status
            bill_res = await db.execute(
                select(RevRefundBill).where(RevRefundBill.refund_id == case.refund_id).order_by(desc(RevRefundBill.bill_id)).limit(1)
            )
            bill = bill_res.scalar_one_or_none()
            if bill:
                bill.status = "APPROVED"
                bill.approved_by = user_id
                bill.approved_at = datetime.now()

            case.pao_approved_by = user_id
            case.pao_approved_at = datetime.now()
            case.pao_remarks = req.remarks
            if case.current_stage < total_stages:
                case.current_stage += 1
                next_stage_meta = stages[case.current_stage - 1]
                case.stage_name = next_stage_meta[1]
                case.pending_role = next_stage_meta[2]
                case.status = "Approved"

        elif req.action == "EXECUTE_PAYMENT":
            case.epay_ref_no = f"EPAY-REF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            case.epay_instructed_at = datetime.now()
            case.paid_at = datetime.now()
            case.current_stage = total_stages
            final_stage = stages[-1]
            case.stage_name = final_stage[1]
            case.pending_role = "NONE"
            case.status = "Paid"

        await db.commit()
        await db.refresh(case)
        return case
