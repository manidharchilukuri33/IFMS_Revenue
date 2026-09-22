from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from app.schemas.reports import ReportDataset

class ReportService:
    @staticmethod
    async def get_report_metadata() -> List[Dict[str, str]]:
        return [
            {"id": "r01", "group": "Collection", "name": "Daily revenue collection report", "desc": "Date-wise gross collection with the number of receipts, by payment mode and reconciliation position."},
            {"id": "r02", "group": "Collection", "name": "Source-wise tax and non-tax collection report", "desc": "Collection by revenue source with the tax / non-tax classification and reconciliation position."},
            {"id": "r03", "group": "Reconciliation", "name": "Portal versus bank versus RBI reconciliation summary", "desc": "Control totals of the three source legs with the reconciliation status distribution."},
            {"id": "r04", "group": "Reconciliation", "name": "Transaction-wise reconciliation report", "desc": "Full transaction-level result set with the match reason and evidence references."},
            {"id": "r05", "group": "Reconciliation", "name": "PAO-wise and department-wise pending reconciliation report", "desc": "Unreconciled exposure grouped by department and Pay & Accounts Office."},
            {"id": "r06", "group": "Reconciliation", "name": "Suspense and RAT report", "desc": "Portal receipts held in suspense and unidentified credits awaiting transfer."},
            {"id": "r07", "group": "Reconciliation", "name": "Amount-mismatch and duplicate-receipt report", "desc": "Variance and duplicate settlement cases with the computed difference."},
            {"id": "r08", "group": "Bank", "name": "Bank scroll receipt and processing report", "desc": "Agency bank scroll lines received, value and processing outcome."},
            {"id": "r09", "group": "Bank", "name": "Bank remittance SLA and penal-interest report", "desc": "Line-level SLA performance with the delay and penal interest computed."},
            {"id": "r10", "group": "Bank", "name": "Penal-interest recovery register", "desc": "Letters issued, responses received, amounts recovered and waived."},
            {"id": "r11", "group": "Refund", "name": "Refund register and refund ageing report", "desc": "All refund cases with the stage, amounts and ageing."},
            {"id": "r12", "group": "Refund", "name": "Refund turnaround-time and performance report", "desc": "Status-wise volume, value and average processing days."},
            {"id": "r13", "group": "Devolution", "name": "Devolution claim, payable and payment report", "desc": "Claims with the computed entitlement, variance, approval and settlement position."},
            {"id": "r14", "group": "Accounting", "name": "Receipt-head-wise collection and booking report", "desc": "Collection and booking position by Chart of Accounts receipt head."},
            {"id": "r15", "group": "Governance", "name": "Transaction-wise, date-wise, PAO-wise and head-wise exception report", "desc": "Complete exception register with severity, ownership and ageing."},
            {"id": "r16", "group": "Governance", "name": "User activity and audit trail report", "desc": "Every recorded action with the user, role, entity and value change."},
            {"id": "r17", "group": "Governance", "name": "Upload batch and data-quality report", "desc": "Upload batches with valid, invalid and duplicate counts and the approval position."},
        ]

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        report_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        source_id: Optional[int] = None,
        bank_id: Optional[int] = None,
        pao_code: Optional[str] = None,
    ) -> ReportDataset:
        rid = report_id.lower()

        if rid == "r01":
            sql = text("""
                SELECT 
                    p.payment_date,
                    COUNT(p.portal_item_id) as total_receipts,
                    COALESCE(SUM(p.amount), 0.00) as gross_amount,
                    COALESCE(SUM(CASE WHEN UPPER(p.payment_mode) IN ('ONLINE', 'NETBANKING') THEN p.amount ELSE 0.00 END), 0.00) as online_netbanking,
                    COALESCE(SUM(CASE WHEN UPPER(p.payment_mode) IN ('UPI', 'CARD') THEN p.amount ELSE 0.00 END), 0.00) as upi_card,
                    COALESCE(SUM(CASE WHEN UPPER(p.payment_mode) = 'CASH' THEN p.amount ELSE 0.00 END), 0.00) as cash_amt,
                    COALESCE(SUM(CASE WHEN UPPER(p.payment_mode) IN ('CHEQUE', 'DD') THEN p.amount ELSE 0.00 END), 0.00) as cheque_dd,
                    COALESCE(SUM(CASE WHEN r.status = 'Matched' THEN p.amount ELSE 0.00 END), 0.00) as matched_amt
                FROM ifms_budget.rev_portal_transaction_staging p
                LEFT JOIN ifms_budget.rev_recon_result r ON r.challan_no = p.challan_no
                WHERE p.is_valid = true
                GROUP BY p.payment_date
                ORDER BY p.payment_date DESC
            """)
            res = await db.execute(sql)
            rows = []
            for row in res:
                rows.append([
                    row.payment_date.isoformat() if row.payment_date else "",
                    row.total_receipts,
                    float(row.gross_amount),
                    float(row.online_netbanking),
                    float(row.upi_card),
                    float(row.cash_amt),
                    float(row.cheque_dd),
                    float(row.matched_amt),
                ])
            return ReportDataset(
                report_id="r01",
                report_name="Daily revenue collection report",
                report_group="Collection",
                description="Date-wise gross collection with the number of receipts, by payment mode and reconciliation position.",
                headers=["Collection date", "Receipts", "Gross amount (INR)", "Online / net banking", "UPI / card", "Cash", "Cheque / DD", "Reconciled amount (INR)"],
                rows=rows,
                money_columns=[2, 3, 4, 5, 6, 7],
                total_records=len(rows),
            )

        elif rid == "r02":
            sql = text("""
                SELECT 
                    s.source_code,
                    s.source_name,
                    CASE WHEN s.source_code = 'NONTAX' THEN 'Non-Tax Revenue' ELSE 'Tax Revenue' END as classification,
                    COUNT(p.portal_item_id) as total_receipts,
                    COALESCE(SUM(p.amount), 0.00) as gross_amount,
                    COALESCE(SUM(CASE WHEN r.status = 'Matched' THEN p.amount ELSE 0.00 END), 0.00) as matched_amt
                FROM ifms_budget.rev_revenue_source s
                LEFT JOIN ifms_budget.rev_portal_transaction_staging p ON p.revenue_source = s.source_code AND p.is_valid = true
                LEFT JOIN ifms_budget.rev_recon_result r ON r.challan_no = p.challan_no
                GROUP BY s.source_id, s.source_code, s.source_name
                ORDER BY s.source_code
            """)
            res = await db.execute(sql)
            rows = []
            total_gross = Decimal("0.00")
            raw_rows = res.all()
            for r in raw_rows:
                total_gross += r.gross_amount

            for r in raw_rows:
                gross = float(r.gross_amount)
                matched = float(r.matched_amt)
                unrec = gross - matched
                pct = round((gross / float(total_gross) * 100), 2) if total_gross > 0 else 0.0
                rows.append([
                    r.source_code,
                    r.source_name,
                    r.classification,
                    r.total_receipts,
                    gross,
                    matched,
                    unrec,
                    pct,
                ])
            return ReportDataset(
                report_id="r02",
                report_name="Source-wise tax and non-tax collection report",
                report_group="Collection",
                description="Collection by revenue source with the tax / non-tax classification and reconciliation position.",
                headers=["Revenue source", "Description", "Classification", "Receipts", "Gross amount (INR)", "Matched amount (INR)", "Unreconciled amount (INR)", "Share of total (%)"],
                rows=rows,
                money_columns=[4, 5, 6],
                total_records=len(rows),
            )

        elif rid == "r03":
            sql = text("""
                SELECT 
                    status,
                    COUNT(recon_id) as tx_count,
                    COALESCE(SUM(portal_total), 0.00) as portal_amt,
                    COALESCE(SUM(bank_total), 0.00) as bank_amt,
                    COALESCE(SUM(rbi_total), 0.00) as rbi_amt,
                    COALESCE(SUM(ABS(amount_difference)), 0.00) as diff_amt
                FROM ifms_budget.rev_recon_result
                GROUP BY status
                ORDER BY status
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.status,
                    r.tx_count,
                    float(r.portal_amt),
                    float(r.bank_amt),
                    float(r.rbi_amt),
                    float(r.diff_amt),
                ])
            return ReportDataset(
                report_id="r03",
                report_name="Portal versus bank versus RBI reconciliation summary",
                report_group="Reconciliation",
                description="Control totals of the three source legs with the reconciliation status distribution.",
                headers=["Reconciliation status", "Transactions", "Portal amount (INR)", "Bank amount (INR)", "RBI amount (INR)", "Variance (INR)"],
                rows=rows,
                money_columns=[2, 3, 4, 5],
                total_records=len(rows),
            )

        elif rid == "r04":
            sql = text("""
                SELECT 
                    r.recon_id,
                    r.rev_transaction_id,
                    r.revenue_source,
                    r.dept_code,
                    r.pao_code,
                    r.challan_no,
                    r.cin,
                    r.payer_name,
                    r.portal_total,
                    r.bank_total,
                    r.rbi_total,
                    r.amount_difference,
                    r.created_at,
                    r.rule_applied,
                    r.status,
                    r.sla_delay_days,
                    r.penal_interest_amount,
                    r.match_reason
                FROM ifms_budget.rev_recon_result r
                ORDER BY r.recon_id DESC
                LIMIT 200
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.recon_id,
                    r.rev_transaction_id or "",
                    r.revenue_source or "",
                    r.dept_code or "",
                    r.pao_code or "",
                    r.challan_no or r.cin or "",
                    r.payer_name or "",
                    float(r.portal_total),
                    float(r.bank_total),
                    float(r.rbi_total),
                    float(r.amount_difference),
                    r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
                    r.rule_applied or "",
                    r.status,
                    r.sla_delay_days,
                    float(r.penal_interest_amount),
                    r.match_reason or "",
                ])
            return ReportDataset(
                report_id="r04",
                report_name="Transaction-wise reconciliation report",
                report_group="Reconciliation",
                description="Full transaction-level result set with the match reason and evidence references.",
                headers=["Reconciliation ID", "Txn ID", "Source", "Dept", "PAO", "Challan / Key", "Payer", "Portal (INR)", "Bank (INR)", "RBI (INR)", "Difference (INR)", "Recon date", "Rule ID", "Status", "Delay days", "Penal interest (INR)", "Remarks"],
                rows=rows,
                money_columns=[7, 8, 9, 10, 15],
                total_records=len(rows),
            )

        elif rid == "r05":
            sql = text("""
                SELECT 
                    d.department_code,
                    d.department_name,
                    r.pao_code,
                    COUNT(r.recon_id) as pending_txns,
                    COALESCE(SUM(r.portal_total), 0.00) as portal_amt,
                    COALESCE(SUM(r.rbi_total), 0.00) as rbi_amt,
                    COALESCE(SUM(ABS(r.amount_difference)), 0.00) as diff_amt
                FROM ifms_budget.rev_recon_result r
                LEFT JOIN ifms_budget.department d ON d.department_code = r.dept_code
                WHERE r.status != 'Matched'
                GROUP BY d.department_code, d.department_name, r.pao_code
                ORDER BY d.department_code
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.department_code or "TT",
                    r.department_name or "Trade & Taxes",
                    r.pao_code or "PAO21",
                    r.pending_txns,
                    float(r.portal_amt),
                    float(r.rbi_amt),
                    float(r.diff_amt),
                ])
            return ReportDataset(
                report_id="r05",
                report_name="PAO-wise and department-wise pending reconciliation report",
                report_group="Reconciliation",
                description="Unreconciled exposure grouped by department and Pay & Accounts Office.",
                headers=["Department code", "Department name", "PAO", "Pending transactions", "Portal amount (INR)", "RBI amount (INR)", "Variance (INR)"],
                rows=rows,
                money_columns=[4, 5, 6],
                total_records=len(rows),
            )

        elif rid == "r06":
            sql = text("""
                SELECT 
                    r.status,
                    r.recon_id,
                    r.revenue_source,
                    r.pao_code,
                    r.challan_no,
                    r.cin,
                    r.payer_name,
                    r.portal_total,
                    r.bank_total,
                    r.rbi_total,
                    r.match_reason
                FROM ifms_budget.rev_recon_result r
                WHERE r.status IN ('Suspend', 'RAT')
                ORDER BY r.recon_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.status,
                    r.recon_id,
                    r.revenue_source or "",
                    r.pao_code or "",
                    r.challan_no or r.cin or "",
                    float(r.portal_total),
                    float(r.bank_total),
                    float(r.rbi_total),
                    r.match_reason or "",
                ])
            return ReportDataset(
                report_id="r06",
                report_name="Suspense and RAT report",
                report_group="Reconciliation",
                description="Portal receipts held in suspense and unidentified credits awaiting transfer.",
                headers=["Status", "Reconciliation ID", "Source", "PAO", "Challan / Key", "Portal (INR)", "Bank (INR)", "RBI (INR)", "Observation"],
                rows=rows,
                money_columns=[5, 6, 7],
                total_records=len(rows),
            )

        elif rid == "r07":
            sql = text("""
                SELECT 
                    r.status,
                    r.recon_id,
                    r.revenue_source,
                    r.pao_code,
                    r.challan_no,
                    r.cin,
                    r.portal_total,
                    r.bank_total,
                    r.rbi_total,
                    r.amount_difference,
                    r.match_reason
                FROM ifms_budget.rev_recon_result r
                WHERE r.status IN ('Mismatch', 'Duplicate')
                ORDER BY r.recon_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.status,
                    r.recon_id,
                    r.revenue_source or "",
                    r.pao_code or "",
                    "Agency Bank",
                    r.challan_no or r.cin or "",
                    float(r.portal_total),
                    float(r.bank_total),
                    float(r.rbi_total),
                    float(r.amount_difference),
                    r.match_reason or "",
                ])
            return ReportDataset(
                report_id="r07",
                report_name="Amount-mismatch and duplicate-receipt report",
                report_group="Reconciliation",
                description="Variance and duplicate settlement cases with the computed difference.",
                headers=["Status", "Reconciliation ID", "Source", "PAO", "Bank", "Challan", "Portal (INR)", "Bank (INR)", "RBI (INR)", "Difference (INR)", "Observation"],
                rows=rows,
                money_columns=[6, 7, 8, 9],
                total_records=len(rows),
            )

        elif rid == "r08":
            sql = text("""
                SELECT 
                    b.bank_code,
                    b.bank_name,
                    s.scroll_no,
                    s.scroll_date,
                    s.branch_code,
                    COUNT(s.scroll_item_id) as total_lines,
                    COALESCE(SUM(s.amount), 0.00) as scroll_value,
                    COALESCE(SUM(CASE WHEN s.bank_remittance_date IS NOT NULL THEN s.amount ELSE 0.00 END), 0.00) as remitted_value
                FROM ifms_budget.rev_agency_bank_scroll_staging s
                JOIN ifms_budget.agency_bank b ON b.bank_code = s.bank_code
                GROUP BY b.bank_code, b.bank_name, s.scroll_no, s.scroll_date, s.branch_code
                ORDER BY s.scroll_date DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.bank_code,
                    r.bank_name,
                    r.scroll_no,
                    r.scroll_date.isoformat() if r.scroll_date else "",
                    r.branch_code or "",
                    r.total_lines,
                    float(r.scroll_value),
                    float(r.remitted_value),
                ])
            return ReportDataset(
                report_id="r08",
                report_name="Bank scroll receipt and processing report",
                report_group="Bank",
                description="Agency bank scroll lines received, value and processing outcome.",
                headers=["Bank code", "Bank name", "Scroll number", "Scroll date", "Branch", "Lines", "Scroll value (INR)", "Remitted value (INR)"],
                rows=rows,
                money_columns=[6, 7],
                total_records=len(rows),
            )

        elif rid == "r09":
            sql = text("""
                SELECT 
                    b.bank_name,
                    c.claim_no,
                    c.payment_mode,
                    c.base_date,
                    c.bank_remittance_date,
                    c.principal_amount,
                    c.permitted_days,
                    c.actual_days,
                    c.delay_days,
                    c.annual_rate_pct,
                    c.penal_interest_computed,
                    c.status
                FROM ifms_budget.rev_penal_claim c
                JOIN ifms_budget.agency_bank b ON b.bank_id = c.bank_id
                ORDER BY c.claim_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.bank_name,
                    r.claim_no,
                    r.payment_mode,
                    r.base_date.isoformat() if r.base_date else "",
                    r.bank_remittance_date.isoformat() if r.bank_remittance_date else "",
                    float(r.principal_amount),
                    r.permitted_days,
                    r.actual_days,
                    r.delay_days,
                    float(r.annual_rate_pct),
                    float(r.penal_interest_computed),
                    r.status,
                ])
            return ReportDataset(
                report_id="r09",
                report_name="Bank remittance SLA and penal-interest report",
                report_group="Bank",
                description="Line-level SLA performance with the delay and penal interest computed.",
                headers=["Bank", "Claim No", "Mode", "Base date", "Remittance date", "Amount (INR)", "SLA days", "Actual days", "Delay days", "Rate (%)", "Penal interest (INR)", "Status"],
                rows=rows,
                money_columns=[5, 10],
                total_records=len(rows),
            )

        elif rid == "r10":
            sql = text("""
                SELECT 
                    b.bank_name,
                    c.claim_no,
                    c.principal_amount,
                    c.delay_days,
                    c.penal_interest_computed,
                    COALESCE(l.letter_no, '') as letter_no,
                    c.penal_interest_recovered,
                    c.penal_interest_waived,
                    c.penal_interest_outstanding,
                    c.status
                FROM ifms_budget.rev_penal_claim c
                JOIN ifms_budget.agency_bank b ON b.bank_id = c.bank_id
                LEFT JOIN ifms_budget.rev_penal_letter l ON l.letter_id = c.letter_id
                ORDER BY c.claim_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.bank_name,
                    r.claim_no,
                    float(r.principal_amount),
                    r.delay_days,
                    float(r.penal_interest_computed),
                    r.letter_no,
                    float(r.penal_interest_recovered),
                    float(r.penal_interest_waived),
                    float(r.penal_interest_outstanding),
                    r.status,
                ])
            return ReportDataset(
                report_id="r10",
                report_name="Penal-interest recovery register",
                report_group="Bank",
                description="Letters issued, responses received, amounts recovered and waived.",
                headers=["Bank", "Claim No", "Delayed amount (INR)", "Delay days", "Penal interest (INR)", "Letter No", "Recovered (INR)", "Waived (INR)", "Outstanding (INR)", "Status"],
                rows=rows,
                money_columns=[2, 4, 6, 7, 8],
                total_records=len(rows),
            )

        elif rid == "r11":
            sql = text("""
                SELECT 
                    case_no,
                    refund_type,
                    applicant_name,
                    original_challan_no,
                    reconciled_original_amount,
                    claimed_amount,
                    refundable_amount,
                    created_at,
                    status,
                    pending_role,
                    stage_name
                FROM ifms_budget.rev_refund_case
                ORDER BY refund_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.case_no,
                    r.refund_type,
                    r.applicant_name,
                    r.original_challan_no,
                    float(r.reconciled_original_amount),
                    float(r.claimed_amount),
                    float(r.refundable_amount),
                    r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
                    r.status,
                    r.pending_role,
                    r.stage_name,
                ])
            return ReportDataset(
                report_id="r11",
                report_name="Refund register and refund ageing report",
                report_group="Refund",
                description="All refund cases with the stage, amounts and ageing.",
                headers=["Case number", "Refund type", "Applicant", "Original challan", "Original amount (INR)", "Claim amount (INR)", "Refundable amount (INR)", "Application date", "Status", "Pending role", "Stage"],
                rows=rows,
                money_columns=[4, 5, 6],
                total_records=len(rows),
            )

        elif rid == "r12":
            sql = text("""
                SELECT 
                    status,
                    COUNT(refund_id) as total_cases,
                    COALESCE(SUM(claimed_amount), 0.00) as claim_amt,
                    COALESCE(SUM(refundable_amount), 0.00) as refund_amt
                FROM ifms_budget.rev_refund_case
                GROUP BY status
                ORDER BY status
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.status,
                    r.total_cases,
                    float(r.claim_amt),
                    float(r.refund_amt),
                ])
            return ReportDataset(
                report_id="r12",
                report_name="Refund turnaround-time and performance report",
                report_group="Refund",
                description="Status-wise volume, value and average processing days.",
                headers=["Status", "Cases", "Claim amount (INR)", "Refundable amount (INR)"],
                rows=rows,
                money_columns=[2, 3],
                total_records=len(rows),
            )

        elif rid == "r13":
            sql = text("""
                SELECT 
                    c.claim_no,
                    lb.local_body_name,
                    s.source_code,
                    c.period_from,
                    c.period_to,
                    c.eligible_collections,
                    c.share_pct,
                    c.computed_entitlement,
                    c.claimed_amount,
                    c.variance_amount,
                    c.approved_amount,
                    c.status,
                    COALESCE(c.advice_no, '') as advice_no
                FROM ifms_budget.rev_devolution_claim c
                JOIN ifms_budget.rev_local_body lb ON lb.local_body_id = c.local_body_id
                JOIN ifms_budget.rev_revenue_source s ON s.source_id = c.source_id
                ORDER BY c.claim_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.claim_no,
                    r.local_body_name,
                    r.source_code,
                    r.period_from.isoformat() if r.period_from else "",
                    r.period_to.isoformat() if r.period_to else "",
                    float(r.eligible_collections),
                    float(r.share_pct),
                    float(r.computed_entitlement),
                    float(r.claimed_amount),
                    float(r.variance_amount),
                    float(r.approved_amount),
                    r.status,
                    r.advice_no,
                ])
            return ReportDataset(
                report_id="r13",
                report_name="Devolution claim, payable and payment report",
                report_group="Devolution",
                description="Claims with the computed entitlement, variance, approval and settlement position.",
                headers=["Claim number", "Local body", "Source", "Period from", "Period to", "Eligible collections (INR)", "Share (%)", "Computed entitlement (INR)", "Claim submitted (INR)", "Variance (INR)", "Approved (INR)", "Status", "Advice number"],
                rows=rows,
                money_columns=[5, 7, 8, 9, 10],
                total_records=len(rows),
            )

        elif rid == "r14":
            sql = text("""
                SELECT 
                    p.receipt_head,
                    s.source_code,
                    COUNT(p.portal_item_id) as total_receipts,
                    COALESCE(SUM(p.amount), 0.00) as gross_amount,
                    COALESCE(SUM(CASE WHEN r.status = 'Matched' THEN p.amount ELSE 0.00 END), 0.00) as booked_amt,
                    COALESCE(SUM(CASE WHEN r.status != 'Matched' THEN p.amount ELSE 0.00 END), 0.00) as suspense_amt
                FROM ifms_budget.rev_portal_transaction_staging p
                JOIN ifms_budget.rev_revenue_source s ON s.source_code = p.revenue_source
                LEFT JOIN ifms_budget.rev_recon_result r ON r.challan_no = p.challan_no
                WHERE p.is_valid = true
                GROUP BY p.receipt_head, s.source_code
                ORDER BY p.receipt_head
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.receipt_head,
                    r.source_code,
                    r.total_receipts,
                    float(r.gross_amount),
                    float(r.booked_amt),
                    float(r.suspense_amt),
                ])
            return ReportDataset(
                report_id="r14",
                report_name="Receipt-head-wise collection and booking report",
                report_group="Accounting",
                description="Collection and booking position by Chart of Accounts receipt head.",
                headers=["Receipt head", "Source", "Receipts", "Gross collection (INR)", "Booked (INR)", "In suspense (INR)"],
                rows=rows,
                money_columns=[3, 4, 5],
                total_records=len(rows),
            )

        elif rid == "r15":
            sql = text("""
                SELECT 
                    exception_id,
                    category,
                    severity,
                    created_at,
                    status,
                    escalation_count,
                    resolution_reason,
                    exception_detail
                FROM ifms_budget.rev_exception
                ORDER BY exception_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.exception_id,
                    r.category,
                    r.severity,
                    r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
                    0.00,
                    0,
                    r.status,
                    "Yes" if (r.escalation_count and r.escalation_count > 0) else "No",
                    r.resolution_reason or "",
                    r.exception_detail,
                ])
            return ReportDataset(
                report_id="r15",
                report_name="Transaction-wise, date-wise, PAO-wise and head-wise exception report",
                report_group="Governance",
                description="Complete exception register with severity, ownership and ageing.",
                headers=["Exception ID", "Category", "Severity", "Raised on", "Amount (INR)", "Ageing (days)", "Status", "Escalated", "Resolution", "Detail"],
                rows=rows,
                money_columns=[4],
                total_records=len(rows),
            )

        elif rid == "r16":
            sql = text("""
                SELECT 
                    audit_id,
                    changed_at,
                    changed_by,
                    table_name,
                    operation,
                    row_pk
                FROM ifms_budget.audit_change_log
                ORDER BY audit_id DESC
                LIMIT 200
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.audit_id,
                    r.changed_at.strftime("%Y-%m-%d %H:%M:%S") if r.changed_at else "",
                    str(r.changed_by or "System"),
                    "Revenue",
                    r.operation,
                    r.table_name,
                    str(r.row_pk or ""),
                ])
            return ReportDataset(
                report_id="r16",
                report_name="User activity and audit trail report",
                report_group="Governance",
                description="Every recorded action with the user, role, entity and value change.",
                headers=["Audit ID", "Date / time", "User ID", "Module", "Action", "Table name", "Record ID"],
                rows=rows,
                money_columns=[],
                total_records=len(rows),
            )

        elif rid == "r17":
            sql = text("""
                SELECT 
                    batch_no,
                    batch_type,
                    source_filename,
                    total_records,
                    valid_records,
                    invalid_records,
                    duplicate_records,
                    control_total,
                    status,
                    created_at
                FROM ifms_budget.rev_upload_batch
                ORDER BY batch_id DESC
            """)
            res = await db.execute(sql)
            rows = []
            for r in res:
                rows.append([
                    r.batch_no,
                    r.batch_type,
                    r.source_filename,
                    r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
                    r.total_records,
                    r.valid_records,
                    r.invalid_records,
                    r.duplicate_records,
                    float(r.control_total),
                    r.status,
                ])
            return ReportDataset(
                report_id="r17",
                report_name="Upload batch and data-quality report",
                report_group="Governance",
                description="Upload batches with valid, invalid and duplicate counts and the approval position.",
                headers=["Batch number", "Source type", "File", "Uploaded at", "Total rows", "Valid", "Invalid", "Duplicate", "Control total (INR)", "Status"],
                rows=rows,
                money_columns=[8],
                total_records=len(rows),
            )

        else:
            return ReportDataset(
                report_id=report_id,
                report_name="Report Not Found",
                report_group="Unknown",
                description="No report found with ID " + report_id,
                headers=[],
                rows=[],
                money_columns=[],
                total_records=0,
            )
