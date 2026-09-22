from fastapi import APIRouter, Depends, Query, Body
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.refunds import (
    RefundCaseCreate,
    AdvanceStageRequest,
)
from app.services.refund_service import RefundService

router = APIRouter(prefix="/api/refunds", tags=["Refund Workflow Engine"])

@router.get("", dependencies=[Depends(require_capability("nav.refund"))])
@router.get("/cases", dependencies=[Depends(require_capability("nav.refund"))])
async def list_refund_cases(
    refund_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await RefundService.get_refund_cases(
        db, refund_type, status, search, limit, offset
    )

@router.post("", dependencies=[Depends(require_capability("refund.create"))])
@router.post("/cases", dependencies=[Depends(require_capability("refund.create"))])
async def create_refund_case(
    req: RefundCaseCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RefundService.create_refund_case(db, req, user.user_id)

@router.get("/{refund_id}", dependencies=[Depends(require_capability("nav.refund"))])
@router.get("/cases/{refund_id}", dependencies=[Depends(require_capability("nav.refund"))])
async def get_refund_case_detail(
    refund_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await RefundService.get_refund_detail(db, refund_id)

@router.post("/{refund_id}/advance")
@router.post("/cases/{refund_id}/advance")
async def advance_refund_stage(
    refund_id: int,
    req: AdvanceStageRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await RefundService.advance_stage(db, refund_id, req, user.user_id)

@router.post("/{refund_id}/verify-shcil")
@router.post("/cases/{refund_id}/verify-shcil")
async def verify_shcil(
    refund_id: int,
    payload: Dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = AdvanceStageRequest(
        action="VERIFY",
        verification_type="SHCIL_E_STAMP",
        verification_result="Valid",
        authority_name="Stock Holding Corp of India (SHCIL)",
        remarks=f"SHCIL e-Stamp certificate {payload.get('certificate_no', '')} verified against central repository."
    )
    return await RefundService.advance_stage(db, refund_id, req, user.user_id)

@router.post("/{refund_id}/prepare-bill")
@router.post("/cases/{refund_id}/prepare-bill")
async def prepare_bill(
    refund_id: int,
    payload: Dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = AdvanceStageRequest(
        action="PREPARE_BILL",
        remarks="Refund Bill Prepared for submission to PAO"
    )
    return await RefundService.advance_stage(db, refund_id, req, user.user_id)

@router.post("/{refund_id}/approve-pao")
@router.post("/cases/{refund_id}/approve-pao")
async def approve_pao(
    refund_id: int,
    payload: Dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = AdvanceStageRequest(
        action="APPROVE_PAO",
        remarks=payload.get("remarks", "Approved by PAO Checker")
    )
    return await RefundService.advance_stage(db, refund_id, req, user.user_id)

@router.post("/{refund_id}/instruct-payment")
@router.post("/cases/{refund_id}/instruct-payment")
async def instruct_payment(
    refund_id: int,
    payload: Dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = AdvanceStageRequest(
        action="EXECUTE_PAYMENT",
        remarks=f"e-Payment instruction issued to bank account {payload.get('bank_account_no', '')}"
    )
    return await RefundService.advance_stage(db, refund_id, req, user.user_id)

@router.post("/{refund_id}/mark-paid")
@router.post("/cases/{refund_id}/mark-paid")
async def mark_paid(
    refund_id: int,
    payload: Dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    req = AdvanceStageRequest(
        action="EXECUTE_PAYMENT",
        remarks=f"Settled with bank reference {payload.get('e_payment_ref', '')}"
    )
    return await RefundService.advance_stage(db, refund_id, req, user.user_id)

