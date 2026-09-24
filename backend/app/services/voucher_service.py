from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc, or_, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    AccountVoucher,
    RevSuspenseRegister,
    RevReconResult,
    ChartOfAccount,
    Department,
    RevSystemConfig,
    AuditChangeLog,
    AppUser,
)
from app.schemas.accounting import (
    BulkVoucherCreateRequest,
    BulkVoucherApproveRequest,
)
from app.core.exceptions import NotFoundException, BusinessValidationException

def calculate_financial_year(d: date) -> str:
    """Calculates Indian Financial Year string dynamically (e.g., '2026-27')"""
    year = d.year
    month = d.month
    if month >= 4:
        return f"{year}-{str(year + 1)[-2:]}"
    else:
        return f"{year - 1}-{str(year)[-2:]}"

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

        if status and status != "ALL":
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

        # Load System Config default suspense head
        cfg_res = await db.execute(select(RevSystemConfig).where(RevSystemConfig.config_id == 1))
        config = cfg_res.scalar_one_or_none()
        default_suspense_coa = coa_map.get(config.suspense_head_id) if config and config.suspense_head_id else None

        dept_res = await db.execute(select(Department))
        dept_map = {d.department_id: d for d in dept_res.scalars().all()}

        # Load Recon mapping if linked
        recon_ids = [v.recon_id for v in vouchers if v.recon_id]
        recon_map = {}
        if recon_ids:
            r_res = await db.execute(select(RevReconResult).where(RevReconResult.recon_id.in_(recon_ids)))
            recon_map = {r.recon_id: r for r in r_res.scalars().all()}

        # Load AppUser lookup cache dynamically
        user_ids = set()
        for v in vouchers:
            if v.created_by:
                user_ids.add(v.created_by)
            if v.prepared_by:
                user_ids.add(v.prepared_by)
            if v.checker_user_id:
                user_ids.add(v.checker_user_id)
        user_map = {}
        if user_ids:
            u_res = await db.execute(select(AppUser).where(AppUser.user_id.in_(list(user_ids))))
            user_map = {u.user_id: u for u in u_res.scalars().all()}

        items = []
        for v in vouchers:
            dr_coa = coa_map.get(v.debit_coa_id) or default_suspense_coa
            cr_coa = coa_map.get(v.credit_coa_id)
            dept = dept_map.get(v.department_id) if v.department_id else None
            rec = recon_map.get(v.recon_id) if v.recon_id else None
            penal_amt = float(rec.penal_interest_amount) if rec and rec.penal_interest_amount else 0.0
            sla_days = rec.sla_delay_days if rec and rec.sla_delay_days else 0
            challan = rec.challan_no if rec and rec.challan_no else v.bill_no

            prep_u = user_map.get(v.prepared_by) or user_map.get(v.created_by)
            check_u = user_map.get(v.checker_user_id)

            maker_name = prep_u.full_name or prep_u.login_name if prep_u else (f"User #{v.prepared_by}" if v.prepared_by else "System")
            checker_name = check_u.full_name or check_u.login_name if check_u else (f"User #{v.checker_user_id}" if v.checker_user_id else None)

            v_dict = {
                "voucher_id": v.voucher_id,
                "sr_no": v.sr_no or v.voucher_id,
                "voucher_no": v.voucher_no,
                "voucher_type": v.voucher_type or "REVENUE_RECEIPT",
                "voucher_date": v.voucher_date,
                "financial_year": v.financial_year,
                "pao_code": v.pao_code,
                "amount": v.amount,
                "penal_interest_amount": penal_amt,
                "sla_delay_days": sla_days,
                "challan_no": challan,
                "debit_coa_id": v.debit_coa_id,
                "credit_coa_id": v.credit_coa_id,
                "debit_coa_code": dr_coa.coa_code if dr_coa else None,
                "debit_coa_name": dr_coa.coa_name if dr_coa else None,
                "credit_coa_code": cr_coa.coa_code if cr_coa else None,
                "credit_coa_name": cr_coa.coa_name if cr_coa else None,
                "demand_id": v.demand_id,
                "department_id": v.department_id,
                "department_name": dept.department_name if dept else None,
                "department_code": dept.department_code if dept else None,
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
                "created_by_name": maker_name,
                "checker_user_id": v.checker_user_id,
                "checker_remarks": v.checker_remarks,
                "approved_by_name": checker_name,
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

        prep_u = await db.get(AppUser, voucher.prepared_by) if voucher.prepared_by else (await db.get(AppUser, voucher.created_by) if voucher.created_by else None)
        check_u = await db.get(AppUser, voucher.checker_user_id) if voucher.checker_user_id else None

        # Recon context
        recon = await db.get(RevReconResult, voucher.recon_id) if voucher.recon_id else None
        penal_amt = float(recon.penal_interest_amount) if recon and recon.penal_interest_amount else 0.0
        sla_days = recon.sla_delay_days if recon and recon.sla_delay_days else 0

        v_dict = {
            "voucher_id": voucher.voucher_id,
            "sr_no": voucher.sr_no or voucher.voucher_id,
            "voucher_no": voucher.voucher_no,
            "voucher_type": voucher.voucher_type or "REVENUE_RECEIPT",
            "voucher_date": voucher.voucher_date,
            "financial_year": voucher.financial_year,
            "pao_code": voucher.pao_code,
            "amount": voucher.amount,
            "penal_interest_amount": penal_amt,
            "sla_delay_days": sla_days,
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
            "created_by_name": prep_u.full_name or prep_u.login_name if prep_u else None,
            "checker_user_id": voucher.checker_user_id,
            "checker_remarks": voucher.checker_remarks,
            "approved_by_name": check_u.full_name or check_u.login_name if check_u else None,
            "approved_at": voucher.approved_at,
            "created_at": voucher.created_at,
            "organization_id": voucher.organization_id,
            "org_branch_id": voucher.org_branch_id,
            "created_by": voucher.created_by,
            "updated_by": voucher.updated_by,
            "workflow_status": voucher.workflow_status,
        }

        recon_context = {
            "group_key": recon.group_key if recon else "",
            "challan_no": recon.challan_no if recon else "",
            "payer_name": recon.payer_name if recon else "",
            "match_status": recon.status if recon else "",
            "portal_total": float(recon.portal_total) if recon and recon.portal_total else None,
            "penal_interest_amount": penal_amt,
            "sla_delay_days": sla_days,
        } if recon else None

        gross_amt = float(voucher.amount or 0)
        net_settled = gross_amt + float(penal_amt)

        debit_head = {
            "coa_id": dr_coa.coa_id if dr_coa else voucher.debit_coa_id,
            "head_code": dr_coa.coa_code if dr_coa else "8658-00-102-01-00-01",
            "head_name": dr_coa.coa_name if dr_coa else "Suspense Remittance in Transit",
            "amount": gross_amt,
            "entry_type": "DEBIT",
        }

        credit_head = {
            "coa_id": cr_coa.coa_id if cr_coa else voucher.credit_coa_id,
            "head_code": cr_coa.coa_code if cr_coa else "0040-00-102-01-00-01",
            "head_name": cr_coa.coa_name if cr_coa else "Revenue Receipt Head",
            "amount": net_settled,
            "entry_type": "CREDIT",
        }

        # Load System Config default heads & COA map
        coa_res = await db.execute(select(ChartOfAccount))
        coa_map = {c.coa_id: c for c in coa_res.scalars().all()}

        cfg_res = await db.execute(select(RevSystemConfig).where(RevSystemConfig.config_id == 1))
        config = cfg_res.scalar_one_or_none()

        # Query all rows for this voucher (both sr_no 1 and sr_no 2 if present)
        vch_rows_res = await db.execute(
            select(AccountVoucher)
            .where(or_(AccountVoucher.voucher_no == voucher.voucher_no, AccountVoucher.voucher_id == voucher_id))
            .order_by(AccountVoucher.sr_no)
        )
        all_vch_rows = vch_rows_res.scalars().all()
        
        penal_row = next((r for r in all_vch_rows if r.sr_no == 2), None)
        penal_head_id = penal_row.debit_coa_id if penal_row else (config.penal_interest_head_id if config else None)
        penal_coa = coa_map.get(penal_head_id) if penal_head_id else None
        penal_account_name = f"{penal_coa.coa_code} — {penal_coa.coa_name}" if penal_coa else "8658-00-102-01-00-02 — Accrued Penal Interest (Bank SLA Delay)"

        # Build dynamic 3-row Accounting Journal Entry (Image 2 style)
        journal_entries = [
            {
                "account": f"{dr_coa.coa_code} — {dr_coa.coa_name}" if dr_coa else "8658-00-102-01-00-01 — Suspense Account (Civil)",
                "debit": gross_amt,
                "credit": None,
                "type": "PRINCIPAL_DEBIT",
            },
            {
                "account": f"{cr_coa.coa_code} — {cr_coa.coa_name}" if cr_coa else "0040-00-102-01-00-01 — Revenue Receipt Head",
                "debit": None,
                "credit": net_settled,
                "type": "REVENUE_CREDIT",
            },
        ]
        if penal_amt > 0:
            journal_entries.append({
                "account": penal_account_name,
                "debit": float(penal_amt),
                "credit": None,
                "type": "PENAL_INTEREST_DEBIT",
            })

        return {
            "voucher": v_dict,
            "debit_head": debit_head,
            "credit_head": credit_head,
            "recon_context": recon_context,
            "journal_entries": journal_entries,
            "total_debit": net_settled,
            "total_credit": net_settled,
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
        voucher_date_str: Optional[str] = None,
        voucher_no_custom: Optional[str] = None,
    ) -> AccountVoucher:
        recon = await db.get(RevReconResult, recon_id)
        if not recon:
            raise NotFoundException(f"Recon record with ID {recon_id} not found")

        # Resolve COA from config
        cfg_res = await db.execute(select(RevSystemConfig).where(RevSystemConfig.config_id == 1))
        config = cfg_res.scalar_one_or_none()
        susp_head_id = config.suspense_head_id if config and config.suspense_head_id else 1
        
        dr_head_id = susp_head_id

        # Resolve Credit Head dynamically from receipt_head string or fallback to first COA matching 0040
        cr_head_id = None
        if recon.receipt_head:
            coa_res = await db.execute(select(ChartOfAccount.coa_id).where(ChartOfAccount.coa_code == recon.receipt_head).limit(1))
            cr_head_id = coa_res.scalar_one_or_none()
        if not cr_head_id:
            coa_res = await db.execute(select(ChartOfAccount.coa_id).where(ChartOfAccount.coa_code.like("0040%")).limit(1))
            cr_head_id = coa_res.scalar_one_or_none() or 1

        # Resolve department_id
        dept_id = None
        if recon.dept_code:
            dept_res = await db.execute(select(Department.department_id).where(Department.department_code.ilike(f"%{recon.dept_code}%")).limit(1))
            dept_id = dept_res.scalar_one_or_none()

        if voucher_date_str:
            try:
                v_date = datetime.strptime(voucher_date_str[:10], "%Y-%m-%d").date()
            except Exception:
                v_date = recon.created_at.date() if recon.created_at else date.today()
        else:
            v_date = recon.created_at.date() if recon.created_at else date.today()

        fy = calculate_financial_year(v_date)
        date_token = v_date.strftime("%Y%m%d")

        if voucher_no_custom and voucher_no_custom.strip():
            voucher_no = voucher_no_custom.strip()
        else:
            seq_res = await db.execute(
                text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
                {"seq_key": "VOUCHER_SEQ", "prefix": "VR", "fy": fy}
            )
            voucher_no = seq_res.scalar() or f"VR-{date_token}-{str(recon.recon_id).zfill(4)}"

        # Next sr_no
        sr_res = await db.execute(select(func.coalesce(func.max(AccountVoucher.sr_no), 0) + 1))
        next_sr = sr_res.scalar() or 1

        amt = recon.rbi_total or recon.portal_total or recon.bank_total or Decimal("0.00")
        penal_amt = recon.penal_interest_amount or Decimal("0.00")
        
        penal_info = ""
        if penal_amt > 0:
            penal_info = f" [Penal Interest: ₹{penal_amt} for {recon.sla_delay_days or 0} days delay]"

        narr = narration or f"Receipt voucher booked on 3-way reconciliation completion for challan {recon.challan_no or 'N/A'}{penal_info}"

        # 1. Main Principal Row (sr_no = 1)
        vch1 = AccountVoucher(
            sr_no=1,
            voucher_no=voucher_no,
            voucher_type="REVENUE_RECEIPT",
            voucher_date=v_date,
            financial_year=fy,
            pao_code=recon.pao_code or "PAO21",
            amount=amt,
            debit_coa_id=dr_head_id,
            credit_coa_id=cr_head_id,
            department_id=dept_id or 1,
            recon_id=recon.recon_id,
            bill_no=recon.challan_no,
            bill_date=v_date,
            payee_name=recon.payer_name,
            narration=narr,
            status="Draft",
            prepared_by=user_id,
            prepared_at=datetime.now(),
            organization_id=1,
            org_branch_id=1,
            created_by=user_id,
            updated_by=user_id,
            workflow_status="ACTIVE",
        )
        db.add(vch1)

        # 2. Penal Interest Row (sr_no = 2) if penal interest is accrued
        if penal_amt > 0:
            penal_dr_head = config.penal_interest_head_id if config and config.penal_interest_head_id else dr_head_id
            vch2 = AccountVoucher(
                sr_no=2,
                voucher_no=voucher_no,
                voucher_type="REVENUE_RECEIPT",
                voucher_date=v_date,
                financial_year=fy,
                pao_code=recon.pao_code or "PAO21",
                amount=penal_amt,
                debit_coa_id=penal_dr_head,
                credit_coa_id=cr_head_id,
                department_id=dept_id or 1,
                recon_id=recon.recon_id,
                bill_no=recon.challan_no,
                bill_date=v_date,
                payee_name=recon.payer_name,
                narration=f"{narr} [Penal Interest Remittance]",
                status="Draft",
                prepared_by=user_id,
                prepared_at=datetime.now(),
                organization_id=1,
                org_branch_id=1,
                created_by=user_id,
                updated_by=user_id,
                workflow_status="ACTIVE",
            )
            db.add(vch2)

        recon.booking_status = "DRAFT_VOUCHER"
        recon.updated_at = datetime.now()
        recon.updated_by = user_id

        # Insert audit change log
        audit = AuditChangeLog(
            schema_name="ifms_budget",
            table_name="account_voucher",
            row_pk=str(recon.recon_id),
            operation="INSERT",
            new_data={
                "voucher_no": voucher_no,
                "amount": float(amt),
                "penal_interest_amount": float(penal_amt),
                "recon_id": recon.recon_id,
                "status": "Draft",
                "rows_created": 2 if penal_amt > 0 else 1,
                "sla_delay_days": recon.sla_delay_days or 0,
            },
            changed_by=user_id,
            changed_at=datetime.now(),
        )
        db.add(audit)

        await db.commit()
        await db.refresh(vch1)
        return vch1

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
            # Sync corresponding rev_recon_result booking status to BOOKED
            await db.execute(
                text("""
                    UPDATE ifms_budget.rev_recon_result
                    SET booking_status = 'BOOKED', updated_at = clock_timestamp(), updated_by = :checker_id
                    WHERE recon_id IN (
                        SELECT recon_id FROM ifms_budget.account_voucher WHERE status = 'Approved' AND recon_id IS NOT NULL
                    ) AND booking_status != 'BOOKED'
                """),
                {"checker_id": checker_id}
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

        vch_no = voucher.voucher_no

        # Update ALL rows matching this voucher_no
        await db.execute(
            update(AccountVoucher)
            .where(or_(AccountVoucher.voucher_no == vch_no, AccountVoucher.voucher_id == voucher_id))
            .values(
                status="Approved",
                checker_user_id=checker_id,
                checker_remarks=remarks,
                approved_at=func.clock_timestamp(),
                updated_by=checker_id
            )
            .execution_options(synchronize_session="fetch")
        )

        if voucher.recon_id:
            recon = await db.get(RevReconResult, voucher.recon_id)
            if recon:
                recon.booking_status = "BOOKED"
                recon.updated_at = datetime.now()
                recon.updated_by = checker_id

        # Insert audit change log
        audit = AuditChangeLog(
            schema_name="ifms_budget",
            table_name="account_voucher",
            row_pk=str(voucher.voucher_id),
            operation="UPDATE",
            new_data={
                "voucher_no": vch_no,
                "status": "Approved",
                "checker_user_id": checker_id,
                "checker_remarks": remarks,
                "booking_status": "BOOKED",
            },
            changed_by=checker_id,
            changed_at=datetime.now(),
        )
        db.add(audit)

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

        if suspense_type and suspense_type != "ALL":
            query = query.where(RevSuspenseRegister.suspense_type == suspense_type)
        if status and status != "ALL":
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
                "suspense_head_code": coa.coa_code if coa else None,
                "suspense_head_name": coa.coa_name if coa else None,
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
        entry.updated_by = user_id

        await db.commit()
        await db.refresh(entry)
        return entry
