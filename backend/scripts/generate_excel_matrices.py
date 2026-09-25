import os
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Common Styling Constants
FONT_TITLE = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_BOLD = Font(name="Calibri", size=10, bold=True)
FONT_NORMAL = Font(name="Calibri", size=10)
FONT_MONO = Font(name="Consolas", size=9)

FILL_NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
FILL_STEEL = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
FILL_TEAL = PatternFill(start_color="008080", end_color="008080", fill_type="solid")
FILL_ACCENT = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
FILL_ALT = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
FILL_WARN = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
FILL_SUCCESS = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

THIN_BORDER = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)
HEADER_BORDER = Border(
    left=Side(style='thin', color='1F4E78'),
    right=Side(style='thin', color='1F4E78'),
    top=Side(style='medium', color='1F4E78'),
    bottom=Side(style='medium', color='1F4E78')
)

def style_header_row(ws, row_idx, headers, fill=FILL_NAVY):
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = HEADER_BORDER

def auto_fit_columns(ws, min_width=12, max_width=50):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        longest = 0
        for cell in col:
            val_str = str(cell.value or '')
            if '\n' in val_str:
                val_str = max(val_str.split('\n'), key=len)
            longest = max(longest, len(val_str))
        ws.column_dimensions[col_letter].width = min(max_width, max(min_width, longest + 3))

# ==============================================================================
# 1. GENERATE IFMS_BUDGET_DATABASE_TRACEABILITY.xlsx
# ==============================================================================
def generate_db_traceability():
    wb = openpyxl.Workbook()
    # Sheet 1: Master Traceability
    ws1 = wb.active
    ws1.title = "Master Traceability Matrix"
    ws1.views.sheetView[0].showGridLines = True
    
    headers1 = [
        "Module", "Screen Name", "Role", "Functional Action", "UI Trigger / Button",
        "API Endpoint", "HTTP Method", "Backend Service & Function", "Stored Procedure / DB Routine",
        "Target Database Table(s)", "Operation Type", "Columns Affected", "WHERE / Matching Condition",
        "Audit Table Affected", "Next Workflow Status"
    ]
    style_header_row(ws1, 1, headers1, FILL_NAVY)
    
    trace_data = [
        # Dashboard
        ("Dashboard", "Executive Dashboard", "ALL ROLES", "View real-time revenue collection KPIs", "Page Mount / Refresh",
         "/api/dashboard/summary", "GET", "DashboardService.get_dashboard_summary", "None (Direct Aggregation Query)",
         "rev_portal_transaction_staging, rev_recon_result, rev_revenue_source", "SELECT",
         "portal_total, bank_total, rbi_total, match_status, amount", "is_valid = true AND payment_date BETWEEN :from AND :to",
         "None (Read-Only)", "None (Real-Time Display)"),

        # Collection
        ("Revenue Collection", "Revenue Collection Register", "DDO, PAO_MAKER, TRE_ADMIN, SYSADMIN", "List portal transactions & status", "Page Mount / Filter",
         "/api/collection/transactions", "GET", "CollectionService.list_transactions", "None",
         "rev_portal_transaction_staging", "SELECT", "portal_item_id, challan_no, cin, cpin, amount, portal_status",
         "is_valid = true [AND source/dept/date filters]", "None (Read-Only)", "Display Register"),

        ("Revenue Collection", "Manual Collection Form", "DDO, PAO_MAKER, SYSADMIN", "Enter and post manual collection", "Save Manual Collection",
         "/api/collection/manual-receipt", "POST", "CollectionService.create_manual_receipt", "fn_rev_next_seq",
         "rev_upload_batch, rev_portal_transaction_staging", "INSERT",
         "batch_id, batch_no, portal_transaction_id, challan_no, amount, payment_mode, dept_validated, is_valid",
         "Batch sequence generated via fn_rev_next_seq('BATCH_SEQ')", "audit_change_log (via CDC Trigger)", "Batch status = APPROVED, Txn dept_validated = True"),

        ("Revenue Collection", "Revenue Collection Register", "DDO, PAO_MAKER, TRE_ADMIN, SYSADMIN", "Validate departmental receipt", "Validate Single / Validate All",
         "/api/collection/transactions/validate-departmental", "POST", "CollectionService.validate_departmental", "None",
         "rev_portal_transaction_staging", "UPDATE", "dept_validated, dept_validated_by, dept_validated_at",
         "portal_item_id IN (:item_ids)", "audit_change_log (via CDC Trigger)", "dept_validated = True"),

        # Upload
        ("Data Upload Centre", "Data Upload Centre", "PAO_MAKER, DDO, SYSADMIN", "Upload departmental portal CSV file", "Upload Portal File",
         "/api/upload/portal", "POST", "UploadService.process_csv_upload", "None",
         "rev_upload_batch, rev_portal_transaction_staging, rev_upload_rejected_row", "INSERT",
         "batch_no, source_filename, total_records, valid_records, control_total, status",
         "CSV header validation against PORTAL format", "audit_change_log", "batch status = PENDING_APPROVAL"),

        ("Data Upload Centre", "Data Upload Centre", "PAO_MAKER, BANK_OPS, SYSADMIN", "Upload agency bank scroll CSV file", "Upload Bank Scroll",
         "/api/upload/bank-scroll", "POST", "UploadService.process_csv_upload", "None",
         "rev_upload_batch, rev_agency_bank_scroll_staging, rev_upload_rejected_row", "INSERT",
         "batch_no, bank_code, total_records, valid_records, control_total, status",
         "CSV header validation against BANK_SCROLL format", "audit_change_log", "batch status = PENDING_APPROVAL"),

        ("Data Upload Centre", "Data Upload Centre", "PAO_MAKER, SYSADMIN", "Upload RBI luggage settlement CSV", "Upload RBI Luggage",
         "/api/upload/rbi-luggage", "POST", "UploadService.process_csv_upload", "None",
         "rev_upload_batch, rev_rbi_luggage_staging, rev_upload_rejected_row", "INSERT",
         "batch_no, rbi_reference_no, total_records, valid_records, control_total, status",
         "CSV header validation against RBI_LUGGAGE format", "audit_change_log", "batch status = PENDING_APPROVAL"),

        ("Data Upload Centre", "Data Upload Centre", "PAO_CHECK, TRE_ADMIN, SYSADMIN", "Approve staging upload batch", "Approve Batch (Checker)",
         "/api/upload/batches/{batch_id}/approve", "POST", "UploadService.approve_batch", "sp_rev_approve_upload_batch",
         "rev_upload_batch", "UPDATE", "status, checker_user_id, checker_remarks, approved_at",
         "batch_id = :id AND status = 'PENDING_APPROVAL'", "audit_change_log", "batch status = APPROVED"),

        # Reconciliation
        ("Reconciliation Workbench", "3-Way Reconciliation", "PAO_MAKER, TRE_ADMIN, SYSADMIN", "Execute 3-way matching engine", "Run Auto-Reconciliation",
         "/api/recon/run", "POST", "ReconEngine.run_three_way_reconciliation", "None (Rules Engine R01-R08)",
         "rev_recon_run, rev_recon_result, rev_recon_leg_linkage, rev_exception, rev_suspense_register", "INSERT/UPDATE",
         "run_id, status, match_rule, portal_total, bank_total, rbi_total, amount_diff, booking_status",
         "Multi-pass joins on Challan, CIN, CPIN, Amount tolerance, Date tolerance", "audit_change_log (trg_rev_recon_audit)", "Status = Matched / Mismatch / Suspend / RAT"),

        ("Reconciliation Workbench", "3-Way Reconciliation", "PAO_MAKER, SYSADMIN", "Propose manual match override", "Propose Manual Match",
         "/api/recon/results/{recon_id}/propose-override", "POST", "ReconEngine.propose_override", "None",
         "rev_recon_override, rev_recon_result", "INSERT/UPDATE",
         "override_id, recon_id, proposed_status, justification, status",
         "recon_id = :id", "audit_change_log", "override status = PENDING_CHECKER"),

        ("Reconciliation Workbench", "3-Way Reconciliation", "PAO_CHECK, TRE_ADMIN, SYSADMIN", "Approve manual match override", "Approve Override (Checker)",
         "/api/recon/results/{recon_id}/approve-override", "POST", "ReconEngine.approve_override", "None",
         "rev_recon_override, rev_recon_result", "UPDATE",
         "status='APPROVED', checker_id, approved_at; recon_result.status='Matched', is_manual_override=True",
         "override_id = :id AND status = 'PENDING_CHECKER'", "audit_change_log", "Recon status = Matched (Manual Override)"),

        # Exceptions
        ("Exceptions Management", "Exception Queue", "PAO_MAKER, TRE_ADMIN, SYSADMIN", "Issue formal discrepancy letter", "Generate Demand Letter",
         "/api/recon/results/{recon_id}/send-letter", "POST", "ExceptionService.issue_exception_letter", "None",
         "rev_exception_letter, rev_exception", "INSERT/UPDATE",
         "letter_no, bank_code, issue_date, demand_amount, status",
         "recon_id = :id", "audit_change_log", "Letter status = ISSUED, Exception = AWAITING_BANK_RESPONSE"),

        ("Exceptions Management", "Exception Queue", "PAO_MAKER, TRE_ADMIN, SYSADMIN", "Solve discrepancy with adjustment", "Resolve Discrepancy",
         "/api/recon/results/{recon_id}/solve", "POST", "ExceptionService.resolve_exception", "None",
         "rev_exception, rev_exception_note", "UPDATE/INSERT",
         "status='RESOLVED', resolution_type, resolved_by, resolved_at",
         "recon_id = :id", "audit_change_log", "Exception status = RESOLVED"),

        # Accounting
        ("Accounting & Vouchers", "Receipt Voucher Posting", "PAO_MAKER, SYSADMIN", "Create bulk draft vouchers for matched receipts", "Bulk Generate Vouchers",
         "/api/accounting/vouchers/create-bulk", "POST", "VoucherService.create_booking_vouchers", "sp_rev_create_booking_vouchers",
         "account_voucher, rev_recon_result", "INSERT/UPDATE",
         "voucher_no, recon_id, debit_coa_id, credit_coa_id, amount, status='Draft'; recon.booking_status='DRAFT_VOUCHER'",
         "rev_recon_result.status = 'Matched' AND booking_status IN ('UNBOOKED', 'READY_FOR_BOOKING')", "audit_change_log", "Vouchers = Draft, Recon = DRAFT_VOUCHER"),

        ("Accounting & Vouchers", "Receipt Voucher Posting", "PAO_CHECK, TRE_ADMIN, SYSADMIN", "Approve draft vouchers in bulk", "Approve Vouchers (Checker)",
         "/api/accounting/vouchers/approve-bulk", "POST", "VoucherService.approve_booking_vouchers", "sp_rev_approve_booking_vouchers",
         "account_voucher, rev_recon_result", "UPDATE",
         "account_voucher.status='Approved', checker_user_id, approved_at; rev_recon_result.booking_status='BOOKED'",
         "account_voucher.status = 'Draft'", "audit_change_log", "Vouchers = Approved, Recon = BOOKED"),

        ("Accounting & Vouchers", "Receipt Voucher Posting", "PAO_CHECK, FINANCE, SYSADMIN", "Post approved voucher to budget ledger", "Post to Ledger",
         "/api/accounting/vouchers/{voucher_id}/post-ledger", "POST", "VoucherService.post_to_budget_ledger", "fn_post_budget_ledger",
         "budget_ledger_entry, account_voucher", "INSERT/UPDATE",
         "ledger_entry_id, batch_id, coa_id, amount, entry_date, voucher_id; account_voucher.workflow_status='POSTED'",
         "account_voucher.voucher_id = :id AND status = 'Approved'", "audit_change_log", "Ledger posted, Voucher = POSTED"),

        # SLA & Penal Interest
        ("Bank SLA & Penal", "Penal Interest Claims", "PAO_MAKER, TRE_ADMIN, SYSADMIN", "Compute penal interest and issue claim", "Issue Demand Letter",
         "/api/sla/claims/{claim_id}/demand-letter", "POST", "SlaService.issue_demand_letter", "fn_rev_compute_penal_interest",
         "rev_penal_letter, rev_penal_claim", "INSERT/UPDATE",
         "letter_no, claim_id, bank_code, delay_days, interest_amount, status='ISSUED'",
         "claim_id = :id", "audit_change_log", "Claim status = DEMAND_ISSUED"),

        ("Bank SLA & Penal", "Penal Interest Claims", "BANK_OPS, PAO_MAKER, SYSADMIN", "Record agency bank response / settlement", "Record Bank Response",
         "/api/sla/claims/{claim_id}/bank-response", "POST", "SlaService.record_bank_response", "None",
         "rev_penal_bank_response, rev_penal_claim", "INSERT/UPDATE",
         "response_id, response_type, agreed_amount, payment_ref, status='SETTLED'",
         "claim_id = :id", "audit_change_log", "Claim status = SETTLED / DISPUTED"),

        ("Bank SLA & Penal", "Penal Interest Claims", "FINANCE, TRE_ADMIN, SYSADMIN", "Grant penal interest waiver", "Approve Waiver",
         "/api/sla/claims/{claim_id}/waiver", "POST", "SlaService.approve_waiver", "None",
         "rev_penal_waiver, rev_penal_claim", "INSERT/UPDATE",
         "waiver_id, waived_amount, reason_code, sanction_order_no, status='WAIVED'",
         "claim_id = :id", "audit_change_log", "Claim status = WAIVED"),

        # Refunds
        ("Refund Management", "Refund Cases", "DDO, PAO_MAKER, SYSADMIN", "Create new refund case", "Submit Refund Application",
         "/api/refunds/cases", "POST", "RefundService.create_refund_case", "fn_rev_next_seq",
         "rev_refund_case", "INSERT",
         "case_no, refund_type, challan_no, payer_name, refund_amount, status='DRAFT'",
         "Sequence generated via fn_rev_next_seq('REFUND_SEQ')", "audit_change_log (trg_rev_refund_audit)", "Refund status = DRAFT / DDO_SUBMITTED"),

        ("Refund Management", "Refund Cases", "DDO, REVENUE_OFFICER, SYSADMIN", "Verify stamp certificate with SHCIL / Dept", "Verify with SHCIL",
         "/api/refunds/cases/{refund_id}/verify-shcil", "POST", "RefundService.verify_shcil", "None",
         "rev_refund_verification, rev_refund_case", "INSERT/UPDATE",
         "verification_id, verification_type='SHCIL', verification_result='GENUINE', is_locked=True; case status='SHCIL_VERIFIED'",
         "refund_id = :id AND status IN ('DRAFT', 'DDO_SUBMITTED')", "audit_change_log", "Refund status = SHCIL_VERIFIED"),

        ("Refund Management", "Refund Cases", "PAO_MAKER, PAO_CHECK, SYSADMIN", "Advance refund stage / Scrutiny", "Approve Scrutiny / Issue Sanction",
         "/api/refunds/cases/{refund_id}/advance", "POST", "RefundService.advance_refund_stage", "None",
         "rev_refund_case", "UPDATE",
         "status, current_stage, scrutiny_remarks, approved_at",
         "refund_id = :id", "audit_change_log", "Refund status = PAO_APPROVED"),

        ("Refund Management", "Refund Cases", "PAO_MAKER, SYSADMIN", "Prepare treasury refund bill", "Generate Refund Bill",
         "/api/refunds/cases/{refund_id}/prepare-bill", "POST", "RefundService.prepare_refund_bill", "fn_rev_next_seq",
         "rev_refund_bill, rev_refund_case", "INSERT/UPDATE",
         "bill_no, bill_date, gross_amount, net_payable, debit_head_id; case status='BILL_PREPARED'",
         "refund_id = :id AND status = 'PAO_APPROVED'", "audit_change_log", "Refund status = BILL_PREPARED"),

        ("Refund Management", "Refund Cases", "PAO_CHECK, TRE_ADMIN, SYSADMIN", "Instruct e-payment / ECS", "Authorize Payment",
         "/api/refunds/cases/{refund_id}/instruct-payment", "POST", "RefundService.instruct_payment", "None",
         "rev_refund_case, rev_refund_bill", "UPDATE",
         "case status='PAYMENT_INSTRUCTED', payment_mode='ECS', bank_advice_no",
         "refund_id = :id AND status = 'BILL_PREPARED'", "audit_change_log", "Refund status = PAYMENT_INSTRUCTED"),

        ("Refund Management", "Refund Cases", "BANK_OPS, PAO_CHECK, SYSADMIN", "Confirm credit to claimant account", "Mark Paid",
         "/api/refunds/cases/{refund_id}/mark-paid", "POST", "RefundService.mark_paid", "None",
         "rev_refund_case, rev_refund_bill", "UPDATE",
         "case status='PAID', payment_date, utr_no",
         "refund_id = :id AND status = 'PAYMENT_INSTRUCTED'", "audit_change_log", "Refund status = PAID"),

        # Devolution
        ("Local Body Devolution", "Devolution Claims", "DDO, FINANCE, SYSADMIN", "Compute net revenue share for local body", "Compute Devolution",
         "/api/devolution/compute", "POST", "DevolutionService.compute_devolution", "None",
         "rev_devolution_computation, rev_devolution_rule, rev_recon_result", "SELECT/INSERT",
         "computation_id, local_body_id, gross_collection, deduction_pct, net_entitlement",
         "Rule match on local_body_type and revenue_source for period", "audit_change_log", "Computed Devolution Record"),

        ("Local Body Devolution", "Devolution Claims", "FINANCE, TRE_ADMIN, SYSADMIN", "Approve devolution and issue advice", "Issue Devolution Advice",
         "/api/devolution/claims/{claim_id}/issue-advice", "POST", "DevolutionService.issue_advice", "fn_rev_next_seq",
         "rev_devolution_advice, rev_devolution_claim", "INSERT/UPDATE",
         "advice_no, claim_id, approved_amount, treasury_code, status='ADVICE_ISSUED'",
         "claim_id = :id AND status = 'APPROVED'", "audit_change_log", "Claim status = ADVICE_ISSUED"),

        # Masters
        ("Masters & Configuration", "Master Management", "TRE_ADMIN, SYSADMIN", "Create or update master record", "Save Master Record",
         "/api/masters/{entity}", "POST/PUT", "MasterService.create/update", "None",
         "department, ddo, rev_pao, agency_bank, bank_branch, rev_revenue_portal, rev_revenue_source, chart_of_account, rev_recon_rule, rev_sla_rule, rev_devolution_rule, rev_system_config", "INSERT/UPDATE",
         "All entity columns + updated_at, updated_by, is_active",
         "Primary Key match for UPDATE", "audit_change_log", "Master Record Active"),

        # Audit Trail
        ("Audit Trail", "Audit Trail Register", "AUDITOR, ALL ROLES", "Inquire immutable change log & diff", "Search / View Diff",
         "/api/audit", "GET", "AuditService.get_audit_logs", "None",
         "audit_change_log", "SELECT",
         "audit_id, table_name, operation, row_pk, old_data, new_data, changed_by, changed_at",
         "table_name = :t AND changed_at BETWEEN :from AND :to", "None (Audit Viewing)", "Display Audit Logs & JSON Diff")
    ]
    
    for r_idx, row in enumerate(trace_data, 2):
        for c_idx, val in enumerate(row, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_MONO if c_idx in [6, 8, 9, 10, 12, 14] else FONT_NORMAL
            cell.border = THIN_BORDER
            if r_idx % 2 == 1:
                cell.fill = FILL_ALT
            if c_idx == 11:
                cell.alignment = Alignment(horizontal="center")
    auto_fit_columns(ws1)

    # Sheet 2: Tables & Columns Catalog
    ws2 = wb.create_sheet(title="Database Tables & Columns")
    ws2.views.sheetView[0].showGridLines = True
    headers2 = ["Schema", "Table Name", "Column Name", "Data Type", "Nullable", "Default Value", "Key Type", "Business Description / Purpose"]
    style_header_row(ws2, 1, headers2, FILL_STEEL)
    
    with open('backend/scripts/db_tables_columns.json', 'r', encoding='utf-8') as f:
        tables_meta = json.load(f)
        
    row_count = 2
    for t_name, cols in sorted(tables_meta.items()):
        for col in cols:
            c_name = col['column_name']
            c_type = col['data_type']
            c_null = col['is_nullable']
            c_def = str(col['column_default'] or '—')
            is_pk = 'PK' if c_name.endswith('_id') and ('id' in c_name and t_name in c_name or c_name == 'id' or c_name == f"{t_name}_id") else ''
            is_fk = 'FK' if c_name.endswith('_id') and not is_pk else ''
            key_type = is_pk or is_fk or '—'
            
            desc = f"Stores {c_name.replace('_', ' ')} for {t_name.replace('_', ' ')}."
            if 'status' in c_name: desc = "Workflow lifecycle status state."
            elif 'created_at' in c_name: desc = "Timestamp when record was initially created."
            elif 'updated_at' in c_name: desc = "Timestamp when record was last updated."
            elif 'created_by' in c_name: desc = "User ID who created the record."
            elif 'amount' in c_name: desc = "Financial transaction amount in INR (numeric 17,2)."
            
            row_vals = ["ifms_budget", t_name, c_name, c_type, c_null, c_def, key_type, desc]
            for c_idx, val in enumerate(row_vals, 1):
                cell = ws2.cell(row=row_count, column=c_idx, value=val)
                cell.font = FONT_MONO if c_idx in [2, 3, 4] else FONT_NORMAL
                cell.border = THIN_BORDER
                if row_count % 2 == 1:
                    cell.fill = FILL_ALT
            row_count += 1
    auto_fit_columns(ws2)

    # Sheet 3: Stored Procedures & Functions
    ws3 = wb.create_sheet(title="Stored Procedures & Routines")
    ws3.views.sheetView[0].showGridLines = True
    headers3 = ["Schema", "Routine Name", "Type", "Parameters & Signature", "Tables Read", "Tables Written", "Audit Logging", "Operational Purpose"]
    style_header_row(ws3, 1, headers3, FILL_TEAL)
    
    with open('backend/scripts/db_routines.json', 'r', encoding='utf-8') as f:
        routines_meta = json.load(f)
        
    r_idx = 2
    for r_name, r_info in sorted(routines_meta.items()):
        defn = r_info['definition']
        prokind = r_info['kind']
        p_type = "PROCEDURE" if prokind == 'p' else "FUNCTION"
        
        # Determine tables read / written
        t_read = []
        t_write = []
        for tbl in tables_meta.keys():
            if f"FROM ifms_budget.{tbl}" in defn or f"JOIN ifms_budget.{tbl}" in defn:
                t_read.append(tbl)
            if f"INSERT INTO ifms_budget.{tbl}" in defn or f"UPDATE ifms_budget.{tbl}" in defn or f"DELETE FROM ifms_budget.{tbl}" in defn:
                t_write.append(tbl)
                
        purpose = "Core database routine."
        if r_name == 'sp_rev_approve_upload_batch':
            purpose = "Validates and transitions upload batch from PENDING_APPROVAL to APPROVED by PAO Checker."
        elif r_name == 'sp_rev_create_booking_vouchers':
            purpose = "Generates dual-COA Draft receipt vouchers and penal interest rows for Matched reconciliation items."
        elif r_name == 'sp_rev_approve_booking_vouchers':
            purpose = "Bulk approves Draft vouchers by PAO Checker and marks reconciliation booking_status as BOOKED."
        elif r_name == 'fn_rev_calculate_delay_days':
            purpose = "Computes remittance delay beyond statutory SLA turnaround threshold (T+1 or Realisation+2)."
        elif r_name == 'fn_rev_compute_penal_interest':
            purpose = "Calculates statutory penal interest on delayed remittances at Bank Repo Rate + 200 bps (8.5% p.a.)."
        elif r_name == 'fn_rev_next_seq':
            purpose = "Generates atomic, zero-padded document sequence numbers from document_number_sequence."
            
        r_vals = [
            "ifms_budget", r_name, p_type,
            defn.split('\n')[0] if defn else "—",
            ", ".join(t_read) if t_read else "None",
            ", ".join(t_write) if t_write else "None",
            "audit_change_log (via CDC Triggers)",
            purpose
        ]
        for c_idx, val in enumerate(r_vals, 1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_MONO if c_idx in [2, 4, 5, 6] else FONT_NORMAL
            cell.border = THIN_BORDER
            if r_idx % 2 == 1:
                cell.fill = FILL_ALT
        r_idx += 1
    auto_fit_columns(ws3)

    # Save
    out_path = "IFMS_BUDGET_DATABASE_TRACEABILITY.xlsx"
    wb.save(out_path)
    print(f"Generated {out_path} successfully!")


# ==============================================================================
# 2. GENERATE IFMS_BUDGET_ROLE_ACCESS_MATRIX.xlsx
# ==============================================================================
def generate_role_access_matrix():
    wb = openpyxl.Workbook()
    # Sheet 1: Role Directory
    ws1 = wb.active
    ws1.title = "Role Directory & Capabilities"
    ws1.views.sheetView[0].showGridLines = True
    
    headers1 = [
        "Role Code", "Role Title", "Statutory Responsibility", "Core Daily Workflow",
        "Entry Route", "Allowed Modules", "Restricted Modules",
        "Create", "Read", "Update", "Delete", "Approve", "Reject", "Submit"
    ]
    style_header_row(ws1, 1, headers1, FILL_NAVY)
    
    role_rows = [
        ("SYSADMIN", "System Administrator", "Complete technical management, configuration, master maintenance, and system health oversight.",
         "Monitors system logs, executes data ingestion pipelines, manages user credentials, and maintains system config.",
         "dashboard", "ALL (14 Screens)", "None", "YES", "YES", "YES", "YES", "YES", "YES", "YES"),

        ("TRE_ADMIN", "Treasury Administration", "Administrative control over treasuries, PAO jurisdiction, bank onboarding, and master schedules.",
         "Configures receipt heads, reconciles treasury scrolls, monitors SLA defaults, and manages bank branch accounts.",
         "dashboard", "12 Screens (Except Citizen)", "Citizen Public Portal", "YES", "YES", "YES", "YES", "YES", "YES", "YES"),

        ("PAO_MAKER", "Pay & Accounts Office Maker", "Operational ingestion of collection data, 3-way reconciliation execution, and exception triage.",
         "Uploads departmental/bank/RBI files, executes reconciliation engine, initiates vouchers, drafts demand letters.",
         "dashboard", "11 Screens", "Citizen Portal, System Config", "YES", "YES", "YES", "NO", "NO", "NO", "YES"),

        ("PAO_CHECK", "Pay & Accounts Office Checker", "Statutory verification, upload batch authorization, override approval, and voucher authorization.",
         "Scrutinizes upload batches, approves reconciliation overrides, authorizes booking vouchers, verifies refunds.",
         "dashboard", "11 Screens", "Citizen Portal, Manual Collection Create", "NO", "YES", "YES", "NO", "YES", "YES", "YES"),

        ("DDO", "Drawing & Disbursing Officer / Dept", "Departmental revenue monitoring, manual receipt capture, refund origination, and devolution claims.",
         "Validates departmental collections, enters counter receipts, originates citizen refunds, files devolution claims.",
         "dashboard", "9 Screens (Collection, Upload, Recon, Exceptions, Refunds, Devolution, Reports, Masters, Audit)",
         "Bank SLA & Penal Interest, Accounting Vouchers", "YES", "YES", "YES", "NO", "NO", "NO", "YES"),

        ("FINANCE", "Finance Department User", "Macro revenue governance, devolution sanctioning, penalty waiver approval, and budgetary monitoring.",
         "Analyzes monthly revenue yields, reviews tax vs non-tax devolution claims, grants penal waivers, posts ledger.",
         "dashboard", "10 Screens", "Upload Ingestion, Manual Receipt Capture", "NO", "YES", "YES", "NO", "YES", "YES", "YES"),

        ("BANK_OPS", "Agency Bank Operations User", "Bank scroll submission, penal interest claim reconciliation, and settlement confirmation.",
         "Uploads daily agency bank scrolls, reviews penalty demand notices, submits bank response explanations, confirms refunds.",
         "upload", "6 Screens (Dashboard, Upload, Exceptions, SLA, Reports, Help)", "Recon Workbench, Refunds, Devolution, Accounting",
         "YES", "YES", "YES", "NO", "NO", "NO", "YES"),

        ("AUDITOR", "Auditor / Read-Only Oversight", "Independent statutory audit, compliance verification, and inspection of change data logs.",
         "Inspects reconciliation results, reviews penal interest assessments, tracks refund TAT, audits change logs.",
         "dashboard", "ALL (14 Screens - Read Only)", "None (Read-Only across all modules)",
         "NO", "YES", "NO", "NO", "NO", "NO", "NO"),

        ("CITIZEN", "Citizen / Payer Public View", "Public transparency, online challan tracking, and self-service refund status monitoring.",
         "Enters case number to track revenue refund application timeline, verification status, and ECS payment reference.",
         "citizen", "2 Screens (Citizen Refund Tracker, Help Guide)", "All Administrative & Accounting Modules",
         "NO", "YES", "NO", "NO", "NO", "NO", "NO")
    ]
    
    for r_idx, r in enumerate(role_rows, 2):
        for c_idx, val in enumerate(r, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_NORMAL
            cell.border = THIN_BORDER
            if r_idx % 2 == 1: cell.fill = FILL_ALT
            if c_idx >= 8:
                cell.alignment = Alignment(horizontal="center")
                if val == "YES": cell.fill = FILL_SUCCESS
                elif val == "NO": cell.fill = FILL_WARN
    auto_fit_columns(ws1)

    # Sheet 2: Screen Access Matrix
    ws2 = wb.create_sheet(title="Screen Access Matrix")
    ws2.views.sheetView[0].showGridLines = True
    
    headers2 = ["Module / Screen Name", "Route Hash", "Capability Key", "SYSADMIN", "TRE_ADMIN", "PAO_MAKER", "PAO_CHECK", "DDO", "FINANCE", "BANK_OPS", "AUDITOR", "CITIZEN"]
    style_header_row(ws2, 1, headers2, FILL_STEEL)
    
    screens = [
        ("Executive Dashboard", "#dashboard", "nav.dashboard", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Revenue Collection Register", "#collection", "nav.collection", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Data Upload Centre", "#upload", "nav.upload", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "DENIED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Reconciliation Workbench", "#recon", "nav.recon", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "DENIED", "READ-ONLY", "DENIED"),
        ("Exceptions Management", "#exceptions", "nav.exceptions", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Bank SLA & Penal Interest", "#sla", "nav.sla", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "DENIED", "ALLOWED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Revenue Refund Management", "#refunds", "nav.refund", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "DENIED", "READ-ONLY", "DENIED"),
        ("Citizen Refund Tracker", "#citizen", "nav.refund", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "DENIED", "READ-ONLY", "ALLOWED"),
        ("Local Body Devolution", "#devolution", "nav.devolution", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "DENIED", "READ-ONLY", "DENIED"),
        ("Accounting & Vouchers", "#accounting", "nav.accounting", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "DENIED", "ALLOWED", "DENIED", "READ-ONLY", "DENIED"),
        ("Reports & MIS Catalogue", "#reports", "nav.reports", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Masters & Configuration", "#masters", "nav.masters", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Security Audit Trail", "#audit", "nav.audit", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "READ-ONLY", "DENIED"),
        ("Help, Formats & Test Guide", "#help", "nav.help", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "ALLOWED", "READ-ONLY", "ALLOWED"),
    ]
    
    for r_idx, s in enumerate(screens, 2):
        for c_idx, val in enumerate(s, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_NORMAL
            cell.border = THIN_BORDER
            if c_idx >= 4:
                cell.alignment = Alignment(horizontal="center")
                if val == "ALLOWED": cell.fill = FILL_SUCCESS
                elif val == "DENIED": cell.fill = FILL_WARN
                elif val == "READ-ONLY": cell.fill = FILL_ACCENT
    auto_fit_columns(ws2)

    # Sheet 3: Action & Button Permissions
    ws3 = wb.create_sheet(title="Action Permission Matrix")
    ws3.views.sheetView[0].showGridLines = True
    
    headers3 = ["Module", "Action / Operation", "SYSADMIN", "TRE_ADMIN", "PAO_MAKER", "PAO_CHECK", "DDO", "FINANCE", "BANK_OPS", "AUDITOR", "CITIZEN"]
    style_header_row(ws3, 1, headers3, FILL_TEAL)
    
    actions = [
        ("Collection", "Capture Manual Receipt", "YES", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO"),
        ("Collection", "Validate Departmental Receipt", "YES", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO"),
        ("Collection", "Export Collection Register CSV", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "NO"),
        ("Upload", "Upload Departmental Portal File", "YES", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO"),
        ("Upload", "Upload Agency Bank Scroll File", "YES", "YES", "YES", "NO", "NO", "NO", "YES", "NO", "NO"),
        ("Upload", "Upload RBI Luggage Settlement", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Upload", "1-Click Load Sample Datasets", "YES", "YES", "YES", "NO", "YES", "NO", "YES", "NO", "NO"),
        ("Upload", "Approve Upload Batch (Checker)", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO", "NO"),
        ("Upload", "Delete Upload Batch", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Recon", "Execute 3-Way Auto-Reconciliation", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Recon", "Propose Manual Match Override", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Recon", "Approve Manual Match Override", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO", "NO"),
        ("Recon", "Reset Reconciliation State", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Exceptions", "Issue Bank Discrepancy Letter", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Exceptions", "Add Investigation / Scrutiny Note", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "NO", "NO"),
        ("Exceptions", "Mark Discrepancy Resolved", "YES", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO"),
        ("Accounting", "Bulk Generate Draft Vouchers", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Accounting", "Bulk Approve Vouchers (Checker)", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO", "NO"),
        ("Accounting", "Post Voucher to Budget Ledger", "YES", "YES", "NO", "YES", "NO", "YES", "NO", "NO", "NO"),
        ("SLA & Penal", "Issue Penal Interest Demand Notice", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("SLA & Penal", "Record Agency Bank Response", "YES", "YES", "YES", "NO", "NO", "NO", "YES", "NO", "NO"),
        ("SLA & Penal", "Approve Penalty Waiver", "YES", "YES", "NO", "NO", "NO", "YES", "NO", "NO", "NO"),
        ("Refunds", "Originate / Draft Refund Case", "YES", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO"),
        ("Refunds", "Verify SHCIL / Dept Certificate", "YES", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO"),
        ("Refunds", "Scrutinize & Approve Refund (PAO)", "YES", "YES", "NO", "YES", "NO", "NO", "NO", "NO", "NO"),
        ("Refunds", "Prepare Refund Treasury Bill", "YES", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Refunds", "Instruct Payment / Authorization", "YES", "YES", "NO", "YES", "NO", "YES", "NO", "NO", "NO"),
        ("Refunds", "Confirm Payment / Mark Paid", "YES", "YES", "NO", "NO", "NO", "NO", "YES", "NO", "NO"),
        ("Devolution", "Compute Local Body Devolution", "YES", "YES", "YES", "NO", "YES", "YES", "NO", "NO", "NO"),
        ("Devolution", "Approve & Issue Devolution Advice", "YES", "YES", "NO", "NO", "NO", "YES", "NO", "NO", "NO"),
        ("Reports", "Generate & View Statutory MIS", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "NO"),
        ("Reports", "Print Official Report (PDF / Hardcopy)", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "NO"),
        ("Reports", "Export Report to CSV File", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "NO"),
        ("Masters", "Add / Edit Master Record", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Masters", "Update System Configuration", "YES", "YES", "NO", "NO", "NO", "NO", "NO", "NO", "NO"),
        ("Audit", "View Change Data Log & Field Diff", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "NO"),
        ("Citizen", "Track Refund Application Status", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "YES", "YES")
    ]
    
    for r_idx, a in enumerate(actions, 2):
        for c_idx, val in enumerate(a, 1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_NORMAL
            cell.border = THIN_BORDER
            if c_idx >= 3:
                cell.alignment = Alignment(horizontal="center")
                if val == "YES": cell.fill = FILL_SUCCESS
                elif val == "NO": cell.fill = FILL_WARN
    auto_fit_columns(ws3)

    out_path = "IFMS_BUDGET_ROLE_ACCESS_MATRIX.xlsx"
    wb.save(out_path)
    print(f"Generated {out_path} successfully!")


# ==============================================================================
# 3. GENERATE IFMS_BUDGET_BUTTON_FUNCTIONAL_MAPPING.xlsx
# ==============================================================================
def generate_button_mapping():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Button Functional Mapping"
    ws.views.sheetView[0].showGridLines = True
    
    headers = [
        "Button Label / Text", "Screen / Page", "Module", "Permitted Roles", "Business Purpose",
        "Preconditions for Click", "Frontend Validation", "API Endpoint Called", "HTTP Method",
        "Backend Function & Service", "Stored Procedure / Trigger", "Target Database Tables",
        "Operation Type", "Lifecycle Status Change", "Audit Log Generated",
        "Success Result / Feedback", "Error Result / Rollback"
    ]
    style_header_row(ws, 1, headers, FILL_NAVY)
    
    buttons_data = [
        ("+ Capture Manual Receipt", "Revenue Collection", "Collection", "DDO, PAO_MAKER, TRE_ADMIN, SYSADMIN",
         "Opens modal to record counter/manual receipt directly into the system.",
         "User authenticated with authorized role.", "Payer name required, amount > 0, receipt head valid.",
         "/api/collection/manual-receipt", "POST", "CollectionService.create_manual_receipt", "fn_rev_next_seq",
         "rev_upload_batch, rev_portal_transaction_staging", "INSERT",
         "Batch = APPROVED, Txn dept_validated = True", "audit_change_log (via CDC Trigger)",
         "Toast: Manual collection posted to new batch.", "Form Error modal displayed, no DB write."),

        ("Validate Single (Checkmark)", "Revenue Collection", "Collection", "DDO, PAO_MAKER, TRE_ADMIN, SYSADMIN",
         "Records departmental endorsement on a single collection transaction.",
         "Transaction has dept_validated = False.", "None (Row-level action).",
         "/api/collection/transactions/validate-departmental", "POST", "CollectionService.validate_departmental", "None",
         "rev_portal_transaction_staging", "UPDATE",
         "dept_validated changes from False to True", "audit_change_log (via CDC Trigger)",
         "Toast: Departmental validation recorded for REV-TXN.", "Error toast, rollback."),

        ("Validate All Filtered", "Revenue Collection", "Collection", "DDO, PAO_MAKER, TRE_ADMIN, SYSADMIN",
         "Bulk records departmental validation for all currently filtered records.",
         "At least one filtered record has dept_validated = False.", "Confirmation modal accepted.",
         "/api/collection/transactions/validate-departmental", "POST", "CollectionService.validate_departmental", "None",
         "rev_portal_transaction_staging", "UPDATE",
         "All matching rows have dept_validated set to True", "audit_change_log (via CDC Trigger)",
         "Toast: N transaction(s) validated by the department.", "Error toast displayed."),

        ("Export CSV", "Revenue Collection", "Collection", "ALL ROLES",
         "Exports filtered collection register rows to local CSV file.",
         "Filtered records count > 0.", "None.",
         "Client-side CSV generator", "CLIENT", "exportCSV utility", "None",
         "None (Client memory export)", "SELECT",
         "None", "None",
         "Browser downloads ifms_revenue_collection_register.csv.", "Toast: No records to export."),

        ("Upload Departmental Portal File", "Data Upload Centre", "Upload", "PAO_MAKER, DDO, SYSADMIN",
         "Uploads CSV of portal receipts into staging table.",
         "Valid CSV file selected or sample loaded.", "File extension .csv, mandatory headers present.",
         "/api/upload/portal", "POST", "UploadService.process_csv_upload", "None",
         "rev_upload_batch, rev_portal_transaction_staging, rev_upload_rejected_row", "INSERT",
         "Batch status = PENDING_APPROVAL", "audit_change_log",
         "Batch created, valid rows staged, toast shown.", "HTTP 400 Bad Request, rejection rows saved."),

        ("Upload Agency Bank Scroll", "Data Upload Centre", "Upload", "PAO_MAKER, BANK_OPS, SYSADMIN",
         "Uploads CSV of bank scroll transactions into staging table.",
         "Valid CSV selected.", "Headers: bank_code, scroll_no, remittance_date, amount...",
         "/api/upload/bank-scroll", "POST", "UploadService.process_csv_upload", "None",
         "rev_upload_batch, rev_agency_bank_scroll_staging, rev_upload_rejected_row", "INSERT",
         "Batch status = PENDING_APPROVAL", "audit_change_log",
         "Batch created, valid bank rows staged.", "Validation error modal with invalid rows."),

        ("Upload RBI Luggage Settlement", "Data Upload Centre", "Upload", "PAO_MAKER, SYSADMIN",
         "Uploads CSV of RBI clearance lines into staging table.",
         "Valid CSV selected.", "Headers: rbi_reference_no, settlement_date, credit_date...",
         "/api/upload/rbi-luggage", "POST", "UploadService.process_csv_upload", "None",
         "rev_upload_batch, rev_rbi_luggage_staging, rev_upload_rejected_row", "INSERT",
         "Batch status = PENDING_APPROVAL", "audit_change_log",
         "Batch created, RBI credit rows staged.", "Error toast, invalid row counter."),

        ("Approve Batch (Checker)", "Data Upload Centre", "Upload", "PAO_CHECK, TRE_ADMIN, SYSADMIN",
         "Statutory approval of uploaded batch by authorized PAO Checker.",
         "Batch status = 'PENDING_APPROVAL', Checker != Uploader.", "Remarks required.",
         "/api/upload/batches/{batch_id}/approve", "POST", "UploadService.approve_batch", "sp_rev_approve_upload_batch",
         "rev_upload_batch", "UPDATE",
         "status changes from PENDING_APPROVAL to APPROVED", "audit_change_log",
         "Toast: Batch approved, ready for reconciliation.", "Exception raised if status != PENDING_APPROVAL."),

        ("Delete Batch", "Data Upload Centre", "Upload", "PAO_MAKER, SYSADMIN",
         "Removes erroneous unapproved staging batch.",
         "Batch status != 'APPROVED'.", "User confirms prompt.",
         "/api/upload/batches/{batch_id}", "DELETE", "UploadService.delete_batch", "None",
         "rev_upload_batch, rev_portal_transaction_staging, rev_agency_bank_scroll_staging, rev_rbi_luggage_staging", "DELETE",
         "Batch and staging rows deleted", "audit_change_log",
         "Toast: Batch deleted from staging.", "Error toast if batch already approved."),

        ("Run Auto-Reconciliation", "Reconciliation Workbench", "Recon", "PAO_MAKER, TRE_ADMIN, SYSADMIN",
         "Executes 3-way matching rules (R01-R08) across staged records.",
         "Approved batches exist for Portal, Bank, and RBI.", "None.",
         "/api/recon/run", "POST", "ReconEngine.run_three_way_reconciliation", "None (Rules Engine)",
         "rev_recon_run, rev_recon_result, rev_recon_leg_linkage, rev_exception, rev_suspense_register", "INSERT/UPDATE",
         "Result status = Matched / Mismatch / Suspend / RAT", "audit_change_log (trg_rev_recon_audit)",
         "Toast: Reconciliation completed (N matched, M exceptions).", "Error toast, failure details logged."),

        ("Propose Override", "Reconciliation Workbench", "Recon", "PAO_MAKER, SYSADMIN",
         "Initiates maker-checker override request for unreconciled item.",
         "Record status IN ('Mismatch', 'Suspend', 'RAT').", "Target linkage selected, justification mandatory.",
         "/api/recon/results/{recon_id}/propose-override", "POST", "ReconEngine.propose_override", "None",
         "rev_recon_override, rev_recon_result", "INSERT/UPDATE",
         "Override status = PENDING_CHECKER", "audit_change_log",
         "Toast: Override proposed, awaiting checker approval.", "Validation toast if justification empty."),

        ("Approve Override (Checker)", "Reconciliation Workbench", "Recon", "PAO_CHECK, TRE_ADMIN, SYSADMIN",
         "Authorizes manual linkage override.",
         "Override status = 'PENDING_CHECKER'.", "Remarks entered.",
         "/api/recon/results/{recon_id}/approve-override", "POST", "ReconEngine.approve_override", "None",
         "rev_recon_override, rev_recon_result", "UPDATE",
         "Override = APPROVED, Recon status = Matched, is_manual_override = True", "audit_change_log",
         "Toast: Override approved, transaction marked Matched.", "Rejection resets to original status."),

        ("Bulk Generate Draft Vouchers", "Accounting & Vouchers", "Accounting", "PAO_MAKER, SYSADMIN",
         "Generates dual-COA accounting vouchers for all Matched receipts.",
         "Matched receipts with booking_status = 'UNBOOKED'.", "None.",
         "/api/accounting/vouchers/create-bulk", "POST", "VoucherService.create_booking_vouchers", "sp_rev_create_booking_vouchers",
         "account_voucher, rev_recon_result", "INSERT/UPDATE",
         "Vouchers = Draft, Recon booking_status = DRAFT_VOUCHER", "audit_change_log",
         "Toast: N draft vouchers generated.", "Error toast if sequence generation fails."),

        ("Bulk Approve Vouchers (Checker)", "Accounting & Vouchers", "Accounting", "PAO_CHECK, TRE_ADMIN, SYSADMIN",
         "Authorizes draft accounting vouchers into live treasury books.",
         "Vouchers exist in status = 'Draft'.", "None.",
         "/api/accounting/vouchers/approve-bulk", "POST", "VoucherService.approve_booking_vouchers", "sp_rev_approve_booking_vouchers",
         "account_voucher, rev_recon_result", "UPDATE",
         "account_voucher.status = 'Approved', recon.booking_status = 'BOOKED'", "audit_change_log",
         "Toast: N vouchers approved.", "Rollback on database error."),

        ("Post to Budget Ledger", "Accounting & Vouchers", "Accounting", "PAO_CHECK, FINANCE, SYSADMIN",
         "Posts approved voucher directly to general budget ledger.",
         "Voucher status = 'Approved', workflow_status != 'POSTED'.", "None.",
         "/api/accounting/vouchers/{voucher_id}/post-ledger", "POST", "VoucherService.post_to_budget_ledger", "fn_post_budget_ledger",
         "budget_ledger_entry, account_voucher", "INSERT/UPDATE",
         "Voucher workflow_status = 'POSTED', ledger entry created", "audit_change_log",
         "Toast: Voucher posted to budget ledger.", "Error toast, balance check failure."),

        ("Issue Demand Notice", "Bank SLA & Penal", "SLA", "PAO_MAKER, TRE_ADMIN, SYSADMIN",
         "Generates formal legal penal interest demand notice to agency bank.",
         "Delay days > SLA grace period, interest > 0.", "Demand letter template validated.",
         "/api/sla/claims/{claim_id}/demand-letter", "POST", "SlaService.issue_demand_letter", "fn_rev_compute_penal_interest",
         "rev_penal_letter, rev_penal_claim", "INSERT/UPDATE",
         "Claim status = DEMAND_ISSUED", "audit_change_log",
         "Toast: Demand letter issued.", "Error toast if claim already settled."),

        ("Record Bank Settlement", "Bank SLA & Penal", "SLA", "BANK_OPS, PAO_MAKER, SYSADMIN",
         "Records bank payment reference and recovery.",
         "Claim status = 'DEMAND_ISSUED'.", "Payment ref and amount mandatory.",
         "/api/sla/claims/{claim_id}/bank-response", "POST", "SlaService.record_bank_response", "None",
         "rev_penal_bank_response, rev_penal_claim", "INSERT/UPDATE",
         "Claim status = SETTLED", "audit_change_log",
         "Toast: Bank response recorded.", "Error toast on invalid amount."),

        ("Approve Penalty Waiver", "Bank SLA & Penal", "SLA", "FINANCE, TRE_ADMIN, SYSADMIN",
         "Statutory waiver of penal interest under competent financial power.",
         "Claim status IN ('DEMAND_ISSUED', 'DISPUTED').", "Sanction order number & justification required.",
         "/api/sla/claims/{claim_id}/waiver", "POST", "SlaService.approve_waiver", "None",
         "rev_penal_waiver, rev_penal_claim", "INSERT/UPDATE",
         "Claim status = WAIVED", "audit_change_log",
         "Toast: Penal interest waiver approved.", "Error toast if unauthorized."),

        ("Submit Refund Application", "Refund Management", "Refunds", "DDO, PAO_MAKER, SYSADMIN",
         "Registers new revenue refund application into system.",
         "Original challan exists in collection register.", "Claimant PAN/Aadhaar, amount, reason mandatory.",
         "/api/refunds/cases", "POST", "RefundService.create_refund_case", "fn_rev_next_seq",
         "rev_refund_case", "INSERT",
         "Refund status = DRAFT / DDO_SUBMITTED", "audit_change_log (trg_rev_refund_audit)",
         "Toast: Refund case REF-XXXX created.", "Validation toast on duplicate challan."),

        ("Verify with SHCIL / Dept", "Refund Management", "Refunds", "DDO, REVENUE_OFFICER, SYSADMIN",
         "Verifies authenticity of e-stamp / court fee receipt with issuing portal.",
         "Refund case status = 'DDO_SUBMITTED'.", "Certificate number and lock token.",
         "/api/refunds/cases/{refund_id}/verify-shcil", "POST", "RefundService.verify_shcil", "None",
         "rev_refund_verification, rev_refund_case", "INSERT/UPDATE",
         "Case status = SHCIL_VERIFIED", "audit_change_log",
         "Toast: Certificate verified and locked.", "Deficiency raised if certificate invalid."),

        ("Prepare Refund Bill", "Refund Management", "Refunds", "PAO_MAKER, SYSADMIN",
         "Generates formal refund payment bill.",
         "Case status = 'PAO_APPROVED'.", "Debit head of account verified.",
         "/api/refunds/cases/{refund_id}/prepare-bill", "POST", "RefundService.prepare_refund_bill", "fn_rev_next_seq",
         "rev_refund_bill, rev_refund_case", "INSERT/UPDATE",
         "Case status = BILL_PREPARED", "audit_change_log",
         "Toast: Refund bill generated.", "Error toast on budget head failure."),

        ("Authorize Payment / ECS", "Refund Management", "Refunds", "PAO_CHECK, TRE_ADMIN, SYSADMIN",
         "Issues electronic payment instruction to agency bank.",
         "Case status = 'BILL_PREPARED'.", "Bank IFSC and account number validated.",
         "/api/refunds/cases/{refund_id}/instruct-payment", "POST", "RefundService.instruct_payment", "None",
         "rev_refund_case, rev_refund_bill", "UPDATE",
         "Case status = PAYMENT_INSTRUCTED", "audit_change_log",
         "Toast: Payment instructed.", "Error toast on bank IFSC failure."),

        ("Confirm Credit / Mark Paid", "Refund Management", "Refunds", "BANK_OPS, PAO_CHECK, SYSADMIN",
         "Confirms electronic disbursement to claimant bank account.",
         "Case status = 'PAYMENT_INSTRUCTED'.", "UTR number and date mandatory.",
         "/api/refunds/cases/{refund_id}/mark-paid", "POST", "RefundService.mark_paid", "None",
         "rev_refund_case, rev_refund_bill", "UPDATE",
         "Case status = PAID", "audit_change_log",
         "Toast: Refund payment confirmed.", "Error toast on missing UTR."),

        ("Compute Devolution", "Local Body Devolution", "Devolution", "DDO, FINANCE, SYSADMIN",
         "Calculates statutory net revenue share payable to local bodies.",
         "Devolution rules configured for active FY.", "Local body and period selected.",
         "/api/devolution/compute", "POST", "DevolutionService.compute_devolution", "None",
         "rev_devolution_computation, rev_devolution_claim", "SELECT/INSERT",
         "Computation record generated", "audit_change_log",
         "Toast: Devolution computed successfully.", "Error toast on zero collection balance."),

        ("Issue Devolution Advice", "Local Body Devolution", "Devolution", "FINANCE, TRE_ADMIN, SYSADMIN",
         "Issues formal treasury devolution settlement payment advice.",
         "Claim status = 'APPROVED'.", "Treasury code assigned.",
         "/api/devolution/claims/{claim_id}/issue-advice", "POST", "DevolutionService.issue_advice", "fn_rev_next_seq",
         "rev_devolution_advice, rev_devolution_claim", "INSERT/UPDATE",
         "Claim status = ADVICE_ISSUED", "audit_change_log",
         "Toast: Devolution advice issued.", "Error toast if unapproved."),

        ("Save Master Record", "Masters & Configuration", "Masters", "TRE_ADMIN, SYSADMIN",
         "Creates or updates master table row in PostgreSQL.",
         "Mandatory fields populated, unique code.", "Code and Name required.",
         "/api/masters/{entity}", "POST/PUT", "MasterService.create/update", "None",
         "department, ddo, rev_pao, agency_bank, chart_of_account, rev_recon_rule...", "INSERT/UPDATE",
         "Master record active in database", "audit_change_log",
         "Toast: Master record saved.", "HTTP 400 on duplicate key constraint."),

        ("Print Report", "Reports & MIS", "Reports", "ALL ROLES",
         "Renders print-ready formatted layout and triggers browser print dialog.",
         "Report generated and rendered in view.", "None.",
         "window.print()", "CLIENT", "Native Print Handler", "None",
         "None (Direct Print)", "SELECT",
         "None", "None",
         "System print dialog opened.", "None.")
    ]
    
    for r_idx, row in enumerate(buttons_data, 2):
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_MONO if c_idx in [8, 9, 10, 11, 12] else FONT_NORMAL
            cell.border = THIN_BORDER
            if r_idx % 2 == 1: cell.fill = FILL_ALT
            if c_idx == 13: cell.alignment = Alignment(horizontal="center")
    auto_fit_columns(ws)

    out_path = "IFMS_BUDGET_BUTTON_FUNCTIONAL_MAPPING.xlsx"
    wb.save(out_path)
    print(f"Generated {out_path} successfully!")


# ==============================================================================
# 4. GENERATE IFMS_BUDGET_LOOKUP_DICTIONARY.xlsx
# ==============================================================================
def generate_lookup_dictionary():
    wb = openpyxl.Workbook()
    # Sheet 1: Lookup Dictionary
    ws1 = wb.active
    ws1.title = "Lookup Data Dictionary"
    ws1.views.sheetView[0].showGridLines = True
    
    headers1 = [
        "Lookup Field Name", "Screen / Form", "Field UI Label", "API Endpoint", "Backend Service",
        "Source Database Table", "Value Column", "Display Column", "Join Condition", "WHERE Condition",
        "Active Status Condition", "Role Filter Condition", "Department Filter Condition", "FY Condition",
        "Why Value May Not Appear / Troubleshooting Rule"
    ]
    style_header_row(ws1, 1, headers1, FILL_NAVY)
    
    lookups_data = [
        ("Department Lookup", "Revenue Collection, Masters, Reports, Refunds", "Department",
         "/api/masters/departments", "MasterService.list_departments",
         "ifms_budget.department", "department_code", "department_name", "None",
         "is_active = true", "is_active = true", "None (All roles see active depts)", "None", "None",
         "Record excluded if is_active is false in department table."),

        ("PAO Lookup", "Revenue Collection, Upload, Recon, Masters, Reports", "Pay & Accounts Office (PAO)",
         "/api/masters/paos", "MasterService.list_paos",
         "ifms_budget.rev_pao", "pao_code", "pao_name (e.g. PAO21 - Treasury)", "department d ON d.department_id = p.department_id",
         "p.is_active = true", "p.is_active = true", "DDO restricted to mapped PAO", "dept_code must match if dept filter active", "None",
         "PAO not shown if marked inactive or if mismatched with selected department."),

        ("DDO Lookup", "Revenue Collection, Manual Collection, Masters", "Drawing & Disbursing Officer",
         "/api/masters/ddos", "MasterService.list_ddos",
         "ifms_budget.ddo", "ddo_code", "ddo_name", "department d ON d.department_id = ddo.department_id",
         "ddo.is_active = true", "is_active = true", "DDO sees own DDO code", "ddo.department_id = selected dept", "None",
         "Excluded if DDO is inactive, or belongs to a different department."),

        ("Revenue Source Lookup", "Collection, Upload, Recon, SLA, Reports", "Revenue Source",
         "/api/masters/sources", "MasterService.list_sources",
         "ifms_budget.rev_revenue_source", "source_code", "source_name (e.g. GST, Excise, Stamp)", "department d ON d.department_id = s.department_id",
         "s.is_active = true", "is_active = true", "None", "source.department_id = selected dept", "None",
         "Excluded if source is deactivated in rev_revenue_source."),

        ("Revenue Portal Lookup", "Upload Centre, Masters", "Revenue Portal",
         "/api/masters/portals", "MasterService.list_portals",
         "ifms_budget.rev_revenue_portal", "portal_code", "portal_name (e.g. GSTN, ESCIMS)", "rev_revenue_source s ON s.source_id = p.source_id",
         "p.is_active = true", "is_active = true", "None", "None", "None",
         "Excluded if portal is inactive or API integration disabled."),

        ("Agency Bank Lookup", "Upload, SLA, Masters, Reports, Refunds", "Agency Bank",
         "/api/masters/banks", "MasterService.list_agency_banks",
         "ifms_budget.agency_bank", "bank_code", "bank_name (e.g. SBI, HDFC)", "None",
         "is_active = true", "is_active = true", "Bank Ops sees assigned bank only", "None", "None",
         "Excluded if bank is marked inactive or not designated as agency bank."),

        ("Bank Branch Lookup", "Masters, SLA, Refunds", "Bank Branch",
         "/api/masters/branches", "MasterService.list_bank_branches",
         "ifms_budget.bank_branch", "branch_code", "branch_name (IFSC Code)", "agency_bank b ON b.bank_id = bb.bank_id",
         "bb.is_active = true", "is_active = true", "None", "None", "None",
         "Excluded if branch is inactive or bank_id does not match selected bank."),

        ("Treasury / Branch Lookup", "Collection, Accounting, Devolution, Masters", "Treasury Branch",
         "/api/masters/treasuries", "MasterService.list_treasuries",
         "ifms_budget.branch", "branch_code", "branch_name", "organization o ON o.organization_id = b.organization_id",
         "b.is_active = true", "is_active = true", "Treasury user locked to assigned branch", "None", "None",
         "Excluded if treasury branch is deactivated."),

        ("Receipt Head (COA) Lookup", "Collection, Accounting, Masters, Reports", "Head of Account (Major / Minor / Detail)",
         "/api/masters/heads", "MasterService.list_chart_of_accounts",
         "ifms_budget.chart_of_account", "coa_code", "coa_name (e.g. 0040-00-102-01-00-01 Taxes on Sales)", "None",
         "is_active = true AND coa_code LIKE '00%' (Revenue Heads)", "is_active = true", "None", "None", "Valid in active FY",
         "Excluded if head is inactive, expired, or non-revenue head (expenditure heads start with 2xxx/4xxx)."),

        ("Reconciliation Rule Lookup", "Masters, Recon Engine", "Reconciliation Rule",
         "/api/masters/rules", "MasterService.list_recon_rules",
         "ifms_budget.rev_recon_rule", "rule_code", "rule_name (e.g. R01 Exact 3-Way)", "None",
         "is_active = true", "is_active = true", "None", "None", "None",
         "Excluded if rule is deactivated by administrator."),

        ("SLA Rule Lookup", "Bank SLA & Penal, Masters", "Remittance SLA Rule",
         "/api/masters/sla-rules", "MasterService.list_sla_rules",
         "ifms_budget.rev_sla_rule", "rule_code", "rule_name (e.g. Cash T+1, Netbanking T+1)", "agency_bank b ON b.bank_id = r.bank_id",
         "r.is_active = true", "r.is_active = true", "None", "None", "None",
         "Excluded if rule is disabled or not applicable to payment mode."),

        ("Local Body Lookup", "Devolution, Masters", "Local Body / Municipal Corp",
         "/api/masters/local-bodies", "MasterService.list_local_bodies",
         "ifms_budget.rev_local_body", "local_body_id", "local_body_name (e.g. Municipal Corp A)", "None",
         "is_active = true", "is_active = true", "None", "None", "None",
         "Excluded if local body is inactive or jurisdiction suspended."),

        ("Devolution Rule Lookup", "Devolution, Masters", "Devolution Rule",
         "/api/masters/devolution-rules", "MasterService.list_devolution_rules",
         "ifms_budget.rev_devolution_rule", "rule_code", "rule_name (e.g. Stamp Devolution 10%)", "rev_local_body lb ON lb.local_body_type = r.local_body_type",
         "r.is_active = true", "r.is_active = true", "None", "None", "Effective date within FY",
         "Excluded if rule is expired or inactive in rev_devolution_rule."),

        ("Payment Mode Lookup", "Collection, Upload, Reports", "Payment Mode",
         "Static Code Master / rev_system_config", "Enums",
         "Enums (ONLINE, NETBANKING, UPI, CARD, CASH, CHEQUE, DD)", "code", "display_name", "None",
         "code IN ('NETBANKING', 'UPI', 'CARD', 'CASH', 'CHEQUE', 'DD')", "None", "None", "None", "None",
         "Excluded if payment mode not supported by portal.")
    ]
    
    for r_idx, row in enumerate(lookups_data, 2):
        for c_idx, val in enumerate(row, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_MONO if c_idx in [4, 6, 7, 8, 10, 11] else FONT_NORMAL
            cell.border = THIN_BORDER
            if r_idx % 2 == 1: cell.fill = FILL_ALT
    auto_fit_columns(ws1)

    # Sheet 2: Troubleshooting Guide
    ws2 = wb.create_sheet(title="Lookup Troubleshooting Guide")
    ws2.views.sheetView[0].showGridLines = True
    headers2 = ["Dropdown / Lookup", "Scenario: Value Not Showing", "Check 1: Database Existence", "Check 2: Status Flag", "Check 3: Role Permission", "Check 4: Parent Mapping / Foreign Key", "Resolution Command / Action"]
    style_header_row(ws2, 1, headers2, FILL_STEEL)
    
    troubleshoot = [
        ("Department Dropdown", "Department name missing in filter or form.",
         "SELECT * FROM ifms_budget.department WHERE department_code = 'XYZ';",
         "Verify is_active = true. If false, record is hidden.",
         "All authenticated roles have access to active departments.",
         "Verify organization_id matches current tenant.",
         "UPDATE ifms_budget.department SET is_active = true WHERE department_code = 'XYZ';"),

        ("PAO Dropdown", "PAO office not visible in dropdown list.",
         "SELECT * FROM ifms_budget.rev_pao WHERE pao_code = 'PAO21';",
         "Verify is_active = true in rev_pao table.",
         "DDO role will only see PAO mapped to their department/treasury.",
         "Verify department_id matches selected department.",
         "Check department mapping in rev_pao or clear department filter."),

        ("DDO Dropdown", "DDO code not listed during manual receipt entry.",
         "SELECT * FROM ifms_budget.ddo WHERE ddo_code = 'DDO-TT-001';",
         "Verify is_active = true in ddo table.",
         "DDO role is locked to their assigned DDO code.",
         "Ensure ddo.department_id matches selected Department.",
         "Verify DDO master mapping and active status in Masters > DDOs."),

        ("Receipt Head (COA)", "Major/Minor Head not appearing in Accounting or Collection.",
         "SELECT * FROM ifms_budget.chart_of_account WHERE coa_code = '0040-...';",
         "Verify is_active = true. Ensure coa_code starts with '00' (Revenue).",
         "Expenditure heads (starting with 2000-4000) are filtered out.",
         "Ensure coa_level = 6 (detail head level for direct posting).",
         "Activate head in Chart of Accounts master and verify 6-tier classification."),

        ("Agency Bank Dropdown", "Bank name not available for scroll upload or SLA.",
         "SELECT * FROM ifms_budget.agency_bank WHERE bank_code = 'SBI';",
         "Verify is_active = true in agency_bank table.",
         "Bank Ops user only sees their own assigned bank code.",
         "Check clearing_account_no and nodal_officer details in agency_bank.",
         "Activate bank in Masters > Agency Banks."),

        ("Revenue Source Dropdown", "Source code (e.g. GST, Stamp) missing in selector.",
         "SELECT * FROM ifms_budget.rev_revenue_source WHERE source_code = 'GST';",
         "Verify is_active = true in rev_revenue_source table.",
         "Role must have operational jurisdiction for department.",
         "Verify department_id matches active department.",
         "Activate source in Masters > Revenue Sources.")
    ]
    
    for r_idx, t in enumerate(troubleshoot, 2):
        for c_idx, val in enumerate(t, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_MONO if c_idx in [3, 7] else FONT_NORMAL
            cell.border = THIN_BORDER
            if r_idx % 2 == 1: cell.fill = FILL_ALT
    auto_fit_columns(ws2)

    out_path = "IFMS_BUDGET_LOOKUP_DICTIONARY.xlsx"
    wb.save(out_path)
    print(f"Generated {out_path} successfully!")

if __name__ == '__main__':
    generate_db_traceability()
    generate_role_access_matrix()
    generate_button_mapping()
    generate_lookup_dictionary()
