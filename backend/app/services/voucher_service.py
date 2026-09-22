from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_, text
from app.models import AccountVoucher, RevSuspenseRegister, RevReconResult, ChartOfAccount, Department, RevSystemConfig
from app.schemas.accounting import (
    BulkVoucherCreateRequest,
    BulkVoucherApproveRequest,
)
from app.core.exceptions import NotFoundException, BusinessValidationException

class VoucherService:
    @staticmethod
    async def get_vouchers(
        db: AsyncSession,
        status: Optional[str] = None,
        financial_year: Optional[str] = None,
        pao_code: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        query = select(AccountVoucher)

        if status:
            query = query.where(AccountVoucher.status == status)
        if financial_year:
            query = query.where(AccountVoucher.financial_year == financial_year)
        if pao_code:
            query = query.where(AccountVoucher.pao_code == pao_code)
        if search:
            query = query.where(
                or_(
                    AccountVoucher.voucher_no.ilike(f"%{search}%"),
                    AccountVoucher.narration.ilike(f"%{search}%"),
                    AccountVoucher.payee_name.ilike(f"%{search}%"),
                    AccountVoucher.bill_no.ilike(f"%{search}%"),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(AccountVoucher.voucher_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        vouchers = result.scalars().all()

        # Load COA lookup cache for formatting
        coa_res = await db.execute(select(ChartOfAccount))
        coa_map = {c.coa_id: c for c in coa_res.scalars().all()}

        dept_res = await db.execute(select(Department))
        dept_map = {d.department_id: d for d in dept_res.scalars().all()}

        items = []
        for v in vouchers:
            dr_coa = coa_map.get(v.debit_coa_id)
            cr_coa = coa_map.get(v.credit_coa_id)
            dept = dept_map.get(v.department_id) if v.department_id else None

            v_dict = {
                "voucher_id": v.voucher_id,
                "sr_no": v.sr_no or v.voucher_id,
                "voucher_no": v.voucher_no,
                "voucher_type": v.voucher_type,
                "voucher_date": v.voucher_date,
                "financial_year": v.financial_year,
                "pao_code": v.pao_code,
                "amount": v.amount,
                "debit_coa_id": v.debit_coa_id,
                "credit_coa_id": v.credit_coa_id,
                "debit_coa_code": dr_coa.coa_code if dr_coa else "8658-00-102-01-00-01",
                "debit_coa_name": dr_coa.coa_name if dr_coa else "Suspense Remittance in Transit",
                "credit_coa_code": cr_coa.coa_code if cr_coa else "0040-00-102-01-00-01",
                "credit_coa_name": cr_coa.coa_name if cr_coa else "Revenue Receipt Head",
                "demand_id": v.demand_id,
                "department_id": v.department_id,
                "department_name": dept.department_name if dept else None,
                "ddo_id": v.ddo_id,
                "office_id": v.office_id,
                "scheme_id": v.scheme_id,
                "project_id": v.project_id,
                "recon_id": v.recon_id,
                "bill_no": v.bill_no,
                "bill_date": v.bill_date,
                "payee_name": v.payee_name,
                "narration": v.narration,
                "status": v.status,
                "prepared_by": v.prepared_by,
                "prepared_at": v.prepared_at,
                "checker_user_id": v.checker_user_id,
                "checker_remarks": v.checker_remarks,
                "approved_at": v.approved_at,
                "created_at": v.created_at,
                "organization_id": v.organization_id,
                "org_branch_id": v.org_branch_id,
                "created_by": v.created_by,
                "updated_by": v.updated_by,
                "workflow_status": v.workflow_status,
            }
            items.append(v_dict)

        # Summary KPIs
        summary_query = select(
            func.count(AccountVoucher.voucher_id).label("total_vouchers"),
            func.coalesce(func.sum(AccountVoucher.amount), Decimal("0.00")).label("total_amount"),
            func.count(AccountVoucher.voucher_id).filter(AccountVoucher.status == "Draft").label("draft_count"),
            func.count(AccountVoucher.voucher_id).filter(AccountVoucher.status == "Approved").label("approved_count"),
        )
        sum_res = (await db.execute(summary_query)).first()

        return {
            "total": total_count,
            "items": items,
            "summary": {
                "total_vouchers": sum_res.total_vouchers if sum_res else 0,
                "total_amount": sum_res.total_amount if sum_res else Decimal("0.00"),
                "draft_count": sum_res.draft_count if sum_res else 0,
                "approved_count": sum_res.approved_count if sum_res else 0,
            }
        }

    @staticmethod
    async def get_voucher_detail(db: AsyncSession, voucher_id: int) -> Dict[str, Any]:
        voucher = await db.get(AccountVoucher, voucher_id)
        if not voucher:
            raise NotFoundException(f"Voucher with ID {voucher_id} not found")

        dr_coa = await db.get(ChartOfAccount, voucher.debit_coa_id)
        cr_coa = await db.get(ChartOfAccount, voucher.credit_coa_id)
        dept = await db.get(Department, voucher.department_id) if voucher.department_id else None

        v_dict = {
            "voucher_id": voucher.voucher_id,
            "sr_no": voucher.sr_no or voucher.voucher_id,
            "voucher_no": voucher.voucher_no,
            "voucher_type": voucher.voucher_type,
            "voucher_date": voucher.voucher_date,
            "financial_year": voucher.financial_year,
            "pao_code": voucher.pao_code,
            "amount": voucher.amount,
            "debit_coa_id": voucher.debit_coa_id,
            "credit_coa_id": voucher.credit_coa_id,
            "debit_coa_code": dr_coa.coa_code if dr_coa else None,
            "debit_coa_name": dr_coa.coa_name if dr_coa else None,
            "credit_coa_code": cr_coa.coa_code if cr_coa else None,
            "credit_coa_name": cr_coa.coa_name if cr_coa else None,
            "demand_id": voucher.demand_id,
            "department_id": voucher.department_id,
            "department_name": dept.department_name if dept else None,
            "ddo_id": voucher.ddo_id,
            "office_id": voucher.office_id,
            "scheme_id": voucher.scheme_id,
            "project_id": voucher.project_id,
            "recon_id": voucher.recon_id,
            "bill_no": voucher.bill_no,
            "bill_date": voucher.bill_date,
            "payee_name": voucher.payee_name,
            "narration": voucher.narration,
            "status": voucher.status,
            "prepared_by": voucher.prepared_by,
            "prepared_at": voucher.prepared_at,
            "checker_user_id": voucher.checker_user_id,
            "checker_remarks": voucher.checker_remarks,
            "approved_at": voucher.approved_at,
            "created_at": voucher.created_at,
            "organization_id": voucher.organization_id,
            "org_branch_id": voucher.org_branch_id,
            "created_by": voucher.created_by,
            "updated_by": voucher.updated_by,
            "workflow_status": voucher.workflow_status,
        }

        # Recon context
        recon = await db.get(RevReconResult, voucher.recon_id) if voucher.recon_id else None
        recon_context = {
            "group_key": recon.group_key if recon else "",
            "challan_no": recon.challan_no if recon else "",
            "payer_name": recon.payer_name if recon else "",
            "match_status": recon.status if recon else "",
            "portal_total": float(recon.portal_total) if recon and recon.portal_total else None,
        } if recon else None

        debit_head = {
            "coa_id": dr_coa.coa_id if dr_coa else voucher.debit_coa_id,
            "head_code": dr_coa.coa_code if dr_coa else "8658-00-102-01-00-01",
            "head_name": dr_coa.coa_name if dr_coa else "Suspense Remittance in Transit",
            "amount": voucher.amount,
            "entry_type": "DEBIT",
        }

        credit_head = {
            "coa_id": cr_coa.coa_id if cr_coa else voucher.credit_coa_id,
            "head_code": cr_coa.coa_code if cr_coa else "0040-00-102-01-00-01",
            "head_name": cr_coa.coa_name if cr_coa else "Revenue Receipt Head",
            "amount": voucher.amount,
            "entry_type": "CREDIT",
        }

        return {
            "voucher": v_dict,
            "debit_head": debit_head,
            "credit_head": credit_head,
            "recon_context": recon_context,
        }

    @staticmethod
    async def create_vouchers_bulk(
        db: AsyncSession,
        req: BulkVoucherCreateRequest,
        user_id: int,
    ) -> Dict[str, Any]:
        """Invokes the PostgreSQL stored procedure sp_rev_create_booking_vouchers"""
        try:
            await db.execute(
                text("CALL ifms_budget.sp_rev_create_booking_vouchers(:user_id, :pao_code)"),
                {"user_id": user_id, "pao_code": req.pao_code}
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise BusinessValidationException(f"Error executing voucher generation: {str(e)}")

        # Fetch count of draft vouchers
        drafts_res = await db.execute(
            select(func.count(AccountVoucher.voucher_id)).where(AccountVoucher.status == "Draft")
        )
        draft_count = drafts_res.scalar() or 0

        return {
            "message": "Booking vouchers generated successfully for all matched recon records.",
            "draft_vouchers_count": draft_count,
            "pao_code": req.pao_code
        }

    @staticmethod
    async def create_single_voucher(
        db: AsyncSession,
        recon_id: int,
        narration: Optional[str],
        user_id: int,
    ) -> AccountVoucher:
        recon = await db.get(RevReconResult, recon_id)
        if not recon:
            raise NotFoundException(f"Recon record with ID {recon_id} not found")

        # Resolve COA from config
        cfg_res = await db.execute(select(RevSystemConfig).where(RevSystemConfig.config_id == 1))
        config = cfg_res.scalar_one_or_none()
        susp_head_id = config.suspense_head_id if config and config.suspense_head_id else 1
        
        dr_head_id = susp_head_id
        cr_head_id = getattr(recon, 'receipt_head_id', 1) or 1

        # Resolve department_id
        dept_id = None
        if recon.dept_code:
            dept_res = await db.execute(select(Department.department_id).where(Department.department_code.ilike(f"%{recon.dept_code}%")).limit(1))
            dept_id = dept_res.scalar_one_or_none()

        seq_res = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "VOUCHER_SEQ", "prefix": "VCH", "fy": "2026-27"}
        )
        voucher_no = seq_res.scalar() or f"VCH-2026-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        amt = recon.rbi_total or recon.portal_total or Decimal("0.00")
        narr = narration or f"Receipt voucher booked on 3-way reconciliation completion for challan {recon.challan_no}"

        vch = AccountVoucher(
            voucher_no=voucher_no,
            voucher_type="REVENUE_RECEIPT",
            voucher_date=date.today(),
            financial_year="2026-27",
            pao_code=recon.pao_code or "PAO21",
            amount=amt,
            debit_coa_id=dr_head_id,
            credit_coa_id=cr_head_id,
            department_id=dept_id or 1,
            recon_id=recon.recon_id,
            bill_no=recon.challan_no,
            bill_date=date.today(),
            payee_name=recon.payer_name,
            narration=narr,
            status="Draft",
            prepared_by=user_id,
            prepared_at=datetime.now(),
            organization_id=1,
            org_branch_id=1,
            created_by=user_id,
        )
        db.add(vch)
        recon.booking_status = "DRAFT_VOUCHER"
        await db.commit()
        await db.refresh(vch)
        return vch

    @staticmethod
    async def approve_vouchers_bulk(
        db: AsyncSession,
        req: BulkVoucherApproveRequest,
        checker_id: int,
    ) -> Dict[str, Any]:
        """Invokes the PostgreSQL stored procedure sp_rev_approve_booking_vouchers"""
        try:
            await db.execute(
                text("CALL ifms_budget.sp_rev_approve_booking_vouchers(:checker_id, :remarks)"),
                {"checker_id": checker_id, "remarks": req.remarks or "Bulk approved by PAO Checker"}
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise BusinessValidationException(f"Error executing voucher approval: {str(e)}")

        approved_res = await db.execute(
            select(func.count(AccountVoucher.voucher_id)).where(AccountVoucher.status == "Approved")
        )
        approved_count = approved_res.scalar() or 0

        return {
            "message": "All draft booking vouchers approved and posted to General Ledger successfully.",
            "approved_vouchers_count": approved_count
        }

    @staticmethod
    async def approve_single_voucher(
        db: AsyncSession,
        voucher_id: int,
        remarks: str,
        checker_id: int,
    ) -> AccountVoucher:
        voucher = await db.get(AccountVoucher, voucher_id)
        if not voucher:
            raise NotFoundException(f"Voucher with ID {voucher_id} not found")

        voucher.status = "Approved"
        voucher.checker_user_id = checker_id
        voucher.checker_remarks = remarks
        voucher.approved_at = datetime.now()

        if voucher.recon_id:
            recon = await db.get(RevReconResult, voucher.recon_id)
            if recon:
                recon.booking_status = "BOOKED"

        await db.commit()
        await db.refresh(voucher)
        return voucher

    @staticmethod
    async def get_suspense_entries(
        db: AsyncSession,
        suspense_type: Optional[str] = None,
        status: Optional[str] = None,
        min_ageing_days: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        query = select(RevSuspenseRegister)

        if suspense_type:
            query = query.where(RevSuspenseRegister.suspense_type == suspense_type)
        if status:
            query = query.where(RevSuspenseRegister.status == status)
        if min_ageing_days is not None:
            query = query.where(RevSuspenseRegister.ageing_days >= min_ageing_days)

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(RevSuspenseRegister.suspense_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        entries = result.scalars().all()

        # KPIs
        summary_query = select(
            func.count(RevSuspenseRegister.suspense_id).label("total_entries"),
            func.coalesce(func.sum(RevSuspenseRegister.amount), Decimal("0.00")).label("total_amount"),
            func.count(RevSuspenseRegister.suspense_id).filter(RevSuspenseRegister.status == "OPEN").label("open_count"),
            func.count(RevSuspenseRegister.suspense_id).filter(RevSuspenseRegister.status == "CLEARED").label("cleared_count"),
        )
        sum_res = (await db.execute(summary_query)).first()

        # Build response items with head info
        items = []
        for e in entries:
            coa = await db.get(ChartOfAccount, e.suspense_head_id)
            items.append({
                "suspense_id": e.suspense_id,
                "recon_id": e.recon_id,
                "suspense_type": e.suspense_type,
                "suspense_head_id": e.suspense_head_id,
                "amount": e.amount,
                "ageing_days": e.ageing_days,
                "status": e.status,
                "cleared_at": e.cleared_at,
                "clearing_remarks": e.clearing_remarks,
                "created_at": e.created_at,
                "updated_at": e.updated_at,
                "suspense_head_code": coa.coa_code if coa else "8658-00-101-01-00-01",
                "suspense_head_name": coa.coa_name if coa else "Suspense Clearing Account",
            })

        return {
            "total": total_count,
            "items": items,
            "summary": {
                "total_entries": sum_res.total_entries if sum_res else 0,
                "total_amount": sum_res.total_amount if sum_res else Decimal("0.00"),
                "open_count": sum_res.open_count if sum_res else 0,
                "cleared_count": sum_res.cleared_count if sum_res else 0,
            }
        }

    @staticmethod
    async def clear_suspense_entry(
        db: AsyncSession,
        suspense_id: int,
        remarks: str,
        user_id: int,
    ) -> RevSuspenseRegister:
        entry = await db.get(RevSuspenseRegister, suspense_id)
        if not entry:
            raise NotFoundException(f"Suspense entry with ID {suspense_id} not found")

        entry.status = "CLEARED"
        entry.cleared_at = datetime.now()
        entry.clearing_remarks = remarks

        await db.commit()
        await db.refresh(entry)
        return entry
