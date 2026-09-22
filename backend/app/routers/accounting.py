from fastapi import APIRouter, Depends, Query, Body
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.accounting import (
    BulkVoucherCreateRequest,
    BulkVoucherApproveRequest,
)
from app.services.voucher_service import VoucherService

router = APIRouter(prefix="/api/accounting", tags=["Accounting & Booking Vouchers"])

@router.get("/vouchers", dependencies=[Depends(require_capability("nav.accounting"))])
async def list_vouchers(
    status: Optional[str] = Query(None),
    financial_year: Optional[str] = Query(None),
    pao_code: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await VoucherService.get_vouchers(
        db, status, financial_year, pao_code, search, limit, offset
    )

@router.get("/vouchers/{voucher_id}", dependencies=[Depends(require_capability("nav.accounting"))])
async def get_voucher_detail(
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await VoucherService.get_voucher_detail(db, voucher_id)

@router.post("/vouchers/create", dependencies=[Depends(require_capability("voucher.create"))])
async def create_single_voucher(
    payload: Dict[str, Any] = Body(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recon_id = payload.get("recon_id") or payload.get("id") or 1
    narration = payload.get("narration")
    return await VoucherService.create_single_voucher(db, recon_id, narration, user.user_id)

@router.post("/vouchers/generate-bulk", dependencies=[Depends(require_capability("voucher.create"))])
async def generate_vouchers_bulk(
    req: BulkVoucherCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VoucherService.create_vouchers_bulk(db, req, user.user_id)

@router.post("/vouchers/approve-bulk", dependencies=[Depends(require_capability("voucher.approve"))])
async def approve_vouchers_bulk(
    req: BulkVoucherApproveRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await VoucherService.approve_vouchers_bulk(db, req, user.user_id)

@router.post("/vouchers/{voucher_id}/approve", dependencies=[Depends(require_capability("voucher.approve"))])
async def approve_single_voucher(
    voucher_id: int,
    payload: Optional[Dict[str, Any]] = Body(None),
    remarks: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rem = (payload.get("remarks") if payload else None) or remarks or "Approved by PAO Checker"
    return await VoucherService.approve_single_voucher(db, voucher_id, rem, user.user_id)

@router.get("/suspense", dependencies=[Depends(require_capability("nav.accounting"))])
async def list_suspense_entries(
    suspense_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_ageing_days: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await VoucherService.get_suspense_entries(db, suspense_type, status, min_ageing_days, limit, offset)

@router.post("/suspense/{suspense_id}/clear", dependencies=[Depends(require_capability("voucher.approve"))])
async def clear_suspense_entry(
    suspense_id: int,
    payload: Optional[Dict[str, Any]] = Body(None),
    remarks: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rem = (payload.get("remarks") if payload else None) or remarks or "Cleared after manual verification"
    return await VoucherService.clear_suspense_entry(db, suspense_id, rem, user.user_id)

