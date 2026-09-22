from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.refunds import RevRefundCase, RevRefundVerification
from app.core.exceptions import NotFoundException

class CitizenService:
    @staticmethod
    async def track_refund_case(db: AsyncSession, case_no: str) -> Dict[str, Any]:
        query = select(RevRefundCase).where(RevRefundCase.case_no.ilike(case_no.strip()))
        result = await db.execute(query)
        case = result.scalar_one_or_none()

        if not case:
            raise NotFoundException(f"No refund application found with case reference '{case_no}'")

        # Mask applicant name
        name_parts = case.applicant_name.split()
        masked_name = name_parts[0] + " " + ("*" * (len(name_parts[-1]) if len(name_parts) > 1 else 3))

        # Get public verification timeline
        ver_res = await db.execute(
            select(RevRefundVerification).where(RevRefundVerification.refund_id == case.refund_id).order_by(RevRefundVerification.verification_id)
        )
        verifications = ver_res.scalars().all()

        timeline = [
            {
                "stage": 1,
                "title": "Application Submitted",
                "date": case.created_at.strftime("%d-%b-%Y") if case.created_at else "",
                "status": "Completed"
            }
        ]

        for v in verifications:
            timeline.append({
                "stage": 2,
                "title": f"Verification: {v.verification_type}",
                "date": v.verified_at.strftime("%d-%b-%Y") if v.verified_at else "",
                "status": v.verification_result
            })

        if case.pao_approved_at:
            timeline.append({
                "stage": 3,
                "title": "Treasury / PAO Sanction Approved",
                "date": case.pao_approved_at.strftime("%d-%b-%Y"),
                "status": "Approved"
            })

        if case.paid_at:
            timeline.append({
                "stage": 4,
                "title": "e-Payment Disbursed to Bank Account",
                "date": case.paid_at.strftime("%d-%b-%Y"),
                "status": "Paid"
            })

        return {
            "case_no": case.case_no,
            "refund_type": "Non-Judicial Stamp Duty" if case.refund_type == "NON_JUDICIAL_STAMP" else "Judicial Court Fee",
            "applicant_name_masked": masked_name,
            "original_challan_no": case.original_challan_no,
            "claimed_amount": float(case.claimed_amount),
            "refundable_amount": float(case.refundable_amount),
            "current_stage": case.current_stage,
            "stage_name": case.stage_name,
            "pending_at": case.pending_role,
            "status": case.status,
            "epay_ref_no": case.epay_ref_no or "Pending sanction",
            "submitted_at": case.created_at.strftime("%d-%b-%Y") if case.created_at else "",
            "timeline": timeline
        }
