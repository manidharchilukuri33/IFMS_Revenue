import os
import json
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_shading(cell, hex_color):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="D9D9D9"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(f'<w:tblBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="{color}"/><w:left w:val="single" w:sz="4" w:space="0" w:color="{color}"/><w:right w:val="single" w:sz="4" w:space="0" w:color="{color}"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color}"/></w:tblBorders>')
    tblPr.append(borders)

def add_callout(doc, title, text, level='info'):
    bg_color = "F2F4F8" if level == 'info' else ("FFF9E6" if level == 'warn' else "EBF5EE")
    border_color = "1F4E78" if level == 'info' else ("D97706" if level == 'warn' else "16A34A")
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, bg_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    cell._tc.get_or_add_tcPr().append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    run_t = p.add_run(f"[{title.upper()}] ")
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(10)
    run_t.font.bold = True
    if level == 'info': run_t.font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)
    elif level == 'warn': run_t.font.color.rgb = RGBColor(0xB4, 0x53, 0x09)
    else: run_t.font.color.rgb = RGBColor(0x15, 0x80, 0x3D)
    
    run_txt = p.add_run(text)
    run_txt.font.name = "Calibri"
    run_txt.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_heading_1(doc, text):
    h = doc.add_heading(text, level=1)
    h.paragraph_format.space_before = Pt(20)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    for r in h.runs:
        r.font.name = "Calibri"
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)
    return h

def add_heading_2(doc, text):
    h = doc.add_heading(text, level=2)
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    for r in h.runs:
        r.font.name = "Calibri"
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x2F, 0x55, 0x97)
    return h

def add_heading_3(doc, text):
    h = doc.add_heading(text, level=3)
    h.paragraph_format.space_before = Pt(10)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    for r in h.runs:
        r.font.name = "Calibri"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x80, 0x80)
    return h

def add_body_p(doc, text, bold_prefix=None, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
    return p

def add_bullet_p(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(9.5)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
    return p

def add_table_data(doc, headers, rows_data, col_widths=None):
    table = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)
    
    # Header row
    hdr_cells = table.rows[0].cells
    for idx, h in enumerate(headers):
        hdr_cells[idx].text = h
        set_cell_shading(hdr_cells[idx], "1F4E78")
        set_cell_margins(hdr_cells[idx], top=80, bottom=80, left=100, right=100)
        p = hdr_cells[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            
    # Body rows
    for r_idx, r_data in enumerate(rows_data):
        row_cells = table.rows[r_idx + 1].cells
        bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            row_cells[c_idx].text = str(val if val is not None else "—")
            set_cell_shading(row_cells[c_idx], bg)
            set_cell_margins(row_cells[c_idx], top=60, bottom=60, left=100, right=100)
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.line_spacing = 1.1
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    if col_widths and len(col_widths) == len(headers):
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table

def build_sop_document():
    doc = docx.Document()
    
    # Page Setup: Margins 0.75" top/bottom, 1.0" left/right
    for s in doc.sections:
        s.top_margin = Inches(0.75)
        s.bottom_margin = Inches(0.75)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # =========================================================================
    # 1. COVER PAGE & DOCUMENT CONTROL
    # =========================================================================
    p_gov = doc.add_paragraph()
    p_gov.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_gov = p_gov.add_run("GOVERNMENT OF THE NATIONAL CAPITAL TERRITORY\nDIRECTORATE OF INFORMATION TECHNOLOGY & FINANCE DEPARTMENT")
    r_gov.font.name = "Calibri"
    r_gov.font.size = Pt(11)
    r_gov.font.bold = True
    r_gov.font.color.rgb = RGBColor(0x5F, 0x6B, 0x7A)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(36)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("INTEGRATED FINANCIAL MANAGEMENT SYSTEM (IFMS)\nREVENUE COLLECTION & RECONCILIATION MODULE")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(36)
    r_sub = p_sub.add_run("COMPREHENSIVE PRODUCTION SYSTEM OPERATING PROCEDURE (SOP)\nEnd-to-End Implementation, Role-Wise Workflows, Database Traceability, and Technical Field Mappings")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = RGBColor(0x2F, 0x55, 0x97)

    # Document Control Metadata Table
    ctrl_headers = ["Document Attribute", "Production Specification Details"]
    ctrl_data = [
        ["System Name", "IFMS Revenue Collection & Reconciliation Module (Production Release)"],
        ["Document ID", "IFMS-REV-SOP-2026-V2.0 (Official Government Release)"],
        ["Implementation Architecture", "3-Tier: React 18 Single Page App + FastAPI Python 3.13 + PostgreSQL 16 Enterprise"],
        ["Target Database", "PostgreSQL Database: ifms_budget (Schema: ifms_budget, 109 Tables & Views)"],
        ["Effective Date", "25-September-2026 (Operational Baseline for FY 2026-27 onwards)"],
        ["Target Stakeholders", "DDOs, PAO Makers, PAO Checkers, Treasury Officers, Finance Dept, Auditors, Developers, UAT Testers"],
        ["Classification", "Official Public Finance Operating Manual — Government Treasury Operations"],
        ["Source Code Repositories", "Frontend: /frontend (React 18/TS), Backend: /backend (FastAPI/SQLAlchemy)"]
    ]
    add_table_data(doc, ctrl_headers, ctrl_data, [2.2, 4.3])

    doc.add_page_break()

    # =========================================================================
    # 2. REVISION HISTORY
    # =========================================================================
    add_heading_1(doc, "Document Revision History")
    add_body_p(doc, "This Standard Operating Procedure is maintained under strict version control. Every modification, schema enhancement, and workflow upgrade must be recorded in this formal register.")
    
    rev_headers = ["Version", "Release Date", "Primary Author", "Reviewer / Approver", "Key Operational & Architectural Changes"]
    rev_data = [
        ["1.0", "15-Aug-2026", "Systems Architecture Team", "Treasury Steering Committee", "Initial functional prototype draft based on simulated in-memory prototype (ifms_revenue_reconciliation_prototype.html)."],
        ["1.5", "10-Sep-2026", "Lead Database Engineer", "Director (Budget & Accounts)", "Connected backend services to PostgreSQL ifms_budget. Added staging tables, 3-way matching engine, and stored procedures."],
        ["2.0", "25-Sep-2026", "Enterprise Systems Architect", "Principal Secretary (Finance)", "Full production-grade end-to-end release. Dedicated DDO operating workflow, 17 live SQL statutory reports, full CRUD masters, Change Data Capture (CDC) audit trail, and zero-mock traceability."]
    ]
    add_table_data(doc, rev_headers, rev_data, [0.7, 1.0, 1.3, 1.4, 2.1])

    # =========================================================================
    # 3. PURPOSE & STATUTORY SCOPE
    # =========================================================================
    add_heading_1(doc, "1. Purpose & Statutory Scope")
    add_body_p(doc, "This Standard Operating Procedure (SOP) governs the day-to-day operations, accounting procedures, automated reconciliation, and security administration of the IFMS Revenue Collection & Reconciliation Module.")
    
    add_heading_2(doc, "1.1 Statutory Mandate")
    add_body_p(doc, "The system operates under the authority of the State Financial Rules, the Central Treasury Rules, and the Reserve Bank of India (RBI) Memorandum of Procedure for Agency Bank Operations. It enforces the following non-negotiable statutory controls:")
    add_bullet_p(doc, "Three-Legged Evidence Rule: A government receipt is never treated as reconciled merely because an agency bank claims to have received money. Full reconciliation requires three independent legs of proof: (1) Departmental portal transaction, (2) Agency bank scroll remittance, and (3) RBI E-Kuber government account credit confirmation.", "The Three-Legged Evidence Rule — ")
    add_bullet_p(doc, "Dual-COA Booking Requirement: All reconciled receipts must be booked with double-entry classification in the live treasury books: Dr Suspense/Remittance-in-Transit (Head 8658) and Cr Specific Revenue Head of Account.", "Statutory Accounting — ")
    add_bullet_p(doc, "Agency Bank Remittance SLA: Commercial agency banks must remit collections to the government account within T+1 working days (for electronic/cash receipts) or Realisation+2 working days (for cheques). Delays automatically trigger statutory penal interest at RBI Repo Rate + 200 bps (8.5% p.a.).", "SLA & Penal Interest — ")
    add_bullet_p(doc, "Immutable Maker-Checker Segregation: Under the Four-Eyes Principle, no individual user may unilaterally ingest data, approve staging batches, override unmatched items, and book accounting vouchers.", "Maker-Checker Controls — ")

    add_heading_2(doc, "1.2 Revenue Scope")
    add_body_p(doc, "The module currently governs all major tax and non-tax revenue heads of the Government:", bold_prefix="Revenue Domains Covered: ")
    add_bullet_p(doc, "State Goods & Services Tax (SGST), IGST Settlement, and GST Cess via the GSTN portal integration.", "Commercial Taxes: ")
    add_bullet_p(doc, "Country liquor, Indian-made foreign liquor (IMFL), license fees, and wholesale permits via the ESCIMS excise portal.", "State Excise: ")
    add_bullet_p(doc, "Motor vehicle road taxes, fitness certificate fees, driving license fees, and national permits via the PARIVAHAN portal.", "Transport Department: ")
    add_bullet_p(doc, "Non-judicial e-stamp duty, judicial court fees, registration fees, and search fees via the Stock Holding Corporation of India (SHCIL) portal.", "Stamps & Registration: ")
    add_bullet_p(doc, "Trade licenses, property tax surcharges, professional taxes, and conversion charges collected by the Department for municipal bodies.", "Local Body Collections: ")

    # =========================================================================
    # 4. SYSTEM OVERVIEW & ARCHITECTURE
    # =========================================================================
    add_heading_1(doc, "2. System Architecture & Technical Specifications")
    add_body_p(doc, "The application is built on an enterprise 3-tier architecture ensuring complete separation of presentation, business logic, and transactional persistence.")
    
    arch_headers = ["Architecture Tier", "Component / Technology", "Technical Specifications & Role"]
    arch_data = [
        ["Presentation Tier", "React 18 Single Page Application (SPA)", "TypeScript, Vite, Modern Responsive UI, CSS Custom Properties, Role Switcher, Session Context, Fast Dynamic Rendering."],
        ["API Gateway Tier", "FastAPI Asynchronous Micro-Framework", "Python 3.13, Uvicorn ASGI Server, Pydantic V2 Schemas, Strict Capability-Based RBAC Middleware, CORS Protection."],
        ["ORM / Data Access", "SQLAlchemy 2.0 Async + Asyncpg", "Connection Pooling, Greenlet Asynchronous Execution, Parameterized Prepared Queries (SQL Injection Immunity)."],
        ["Database Tier", "PostgreSQL 16 Enterprise Database", "Dedicated schema ifms_budget, 93 Base Tables, 16 Views, Foreign Keys, Triggers, Functions, Stored Procedures, and Sequences."],
        ["Security & Audit", "Change Data Capture (CDC) Triggers", "Immutable audit_change_log capturing full BEFORE and AFTER row JSON states with timestamp, user ID, and operation type."]
    ]
    add_table_data(doc, arch_headers, arch_data, [1.4, 2.1, 3.0])

    add_callout(doc, "Architecture Rule", "Direct database manipulation from the frontend is strictly prohibited. Every user action routes through validated FastAPI REST endpoints enforcing require_capability dependencies before executing parameterized SQL transactions in PostgreSQL.", "info")

    # =========================================================================
    # 5. USER ROLES & PERSONAS
    # =========================================================================
    add_heading_1(doc, "3. Authoritative Role Directory & Personas")
    add_body_p(doc, "The system defines 9 formal operational personas. Every role is mapped to specific statutory duties, default screens, and action permissions.")

    role_headers = ["Role Code", "Role Title", "Statutory Responsibility", "Start Screen", "Allowed Screens", "Prohibited Modules"]
    role_data = [
        ["SYSADMIN", "System Administrator", "Full administrative control, technical parameters, database schema maintenance, and system health oversight.", "#dashboard", "ALL (14 Screens)", "None"],
        ["TRE_ADMIN", "Treasury Administration", "Jurisdiction over treasuries, PAO offices, agency bank branch mappings, receipt heads, and system config.", "#dashboard", "13 Screens", "Citizen Portal"],
        ["PAO_MAKER", "Pay & Accounts Office Maker", "Operational data ingestion, executing 3-way matching rules engine, exception investigation, voucher drafting.", "#dashboard", "11 Screens", "Citizen Portal, System Config"],
        ["PAO_CHECK", "Pay & Accounts Office Checker", "Statutory verification, batch approval, override approval, bulk voucher authorization, refund sanction.", "#dashboard", "11 Screens", "Citizen Portal, Manual Receipt Capture"],
        ["DDO", "Drawing & Disbursing Officer", "Departmental collection monitoring, manual receipt entry, collection validation, refund origination, devolution.", "#dashboard", "9 Screens", "Bank SLA & Penal, Accounting Vouchers"],
        ["FINANCE", "Finance Department User", "Macro revenue analytics, devolution sanctioning, penal interest waiver approval, and budget ledger posting.", "#dashboard", "10 Screens", "Upload Ingestion, Manual Receipt Capture"],
        ["BANK_OPS", "Agency Bank Operations User", "Uploading daily bank scroll files, reviewing penalty demand notices, recording settlement payments, refund credits.", "#upload", "6 Screens", "Recon Workbench, Refunds, Devolution, Accounting"],
        ["AUDITOR", "Statutory Auditor / Read-Only", "Independent verification, compliance checking, change data capture review, and audit trail inspection.", "#dashboard", "ALL (Read-Only)", "All Modify / Write / Approve Actions"],
        ["CITIZEN", "Citizen / Public Payer", "Self-service online tracking of revenue refund cases using unique Case Number without logging in.", "#citizen", "2 Screens (Citizen, Help)", "All Administrative & Accounting Modules"]
    ]
    add_table_data(doc, role_headers, role_data, [1.0, 1.2, 1.8, 0.8, 0.9, 0.8])

    # =========================================================================
    # 6. DDO / DEPARTMENT USER OPERATING PROCEDURE (MANDATORY SPECIAL FOCUS)
    # =========================================================================
    add_heading_1(doc, "4. DDO / Department User — System Operating Procedure")
    add_callout(doc, "Special Operational Focus", "This chapter specifically addresses the operational mandate: 'When a DDO logs in, what is his work?' It provides Drawing & Disbursing Officers and departmental revenue officers with a complete, prescriptive guide to their daily duties.", "info")

    add_heading_2(doc, "4.1 Purpose of the DDO Role")
    add_body_p(doc, "The Drawing & Disbursing Officer (DDO) represents the revenue-collecting department (e.g. Transport, Excise, Trade & Taxes, Revenue/Stamps). The DDO is legally responsible for ensuring that all fees, taxes, and duties collected at field counters, online portals, or departmental cash offices are accurately recorded, validated, and remitted into the Government Treasury Account without delay.")

    add_heading_2(doc, "4.2 Daily Step-by-Step DDO Workflow")
    add_body_p(doc, "When a DDO logs into the IFMS application, the DDO must perform the following standard operations in order:")
    
    add_bullet_p(doc, "Step 1: Dashboard Review — The DDO reviews the Executive Dashboard (#dashboard) to inspect the daily gross collection total for their department, the volume of matched receipts, and any pending exceptions.", "1. Morning Dashboard Inspection: ")
    add_bullet_p(doc, "Step 2: Scrutinize Collection Register — The DDO navigates to the Revenue Collection Register (#collection). The register displays all transactions ingested from departmental portals (GSTN, ESCIMS, PARIVAHAN, SHCIL). The DDO filters by their Department Code (e.g. 'TT' for Trade & Taxes, 'TRANSPORT', 'EXCISE') and DDO Code (e.g. 'DDO-TT-001').", "2. Departmental Register Scrutiny: ")
    add_bullet_p(doc, "Step 3: Departmental Endorsement / Validation — For every verified transaction, the DDO clicks the 'Validate' checkmark (or 'Validate All Filtered'). This executes POST /api/collection/transactions/validate-departmental, setting dept_validated = True in ifms_budget.rev_portal_transaction_staging. This statutory endorsement certifies that the department has rendered the service and confirms the receipt legitimacy.", "3. Departmental Receipt Endorsement: ")
    add_bullet_p(doc, "Step 4: Manual Counter Receipt Entry — If revenue was collected offline (cash at counter, bank draft, physical challan), the DDO clicks '+ Capture Manual Receipt'. The DDO enters Payer Name, Amount, Challan Number, Payment Mode, and Selects the Major/Minor Receipt Head. Clicking 'Save' executes POST /api/collection/manual-receipt, creating a pre-approved batch in rev_upload_batch and inserting a staging row in rev_portal_transaction_staging with dept_validated = True.", "4. Capturing Offline / Counter Collections: ")
    add_bullet_p(doc, "Step 5: Originating Citizen Refunds — When a citizen or taxpayer applies for a refund of excess court fees, unused stamp duty, or motor vehicle tax, the DDO navigates to Revenue Refund Management (#refunds) and clicks '+ New Refund Case'. The DDO enters the original Challan No, Claimant PAN/Aadhaar, Bank IFSC, Account Number, and Refund Amount. Clicking 'Submit' creates a case in ifms_budget.rev_refund_case with status DDO_SUBMITTED.", "5. Revenue Refund Origination: ")
    add_bullet_p(doc, "Step 6: Verifying E-Stamp Certificates with SHCIL — For stamp refunds, the DDO clicks 'Verify SHCIL'. The system queries SHCIL integration, verifies authenticity, and locks the e-stamp certificate in rev_refund_verification to prevent double-refunding. The case advances to SHCIL_VERIFIED.", "6. Certificate Verification: ")
    add_bullet_p(doc, "Step 7: Filing Local Body Devolution Claims — If the department collects taxes subject to municipal revenue sharing (e.g. motor vehicle tax or stamp duty surcharges), the DDO navigates to Local Body Devolution (#devolution) and reviews computed devolution claims before routing them to Finance.", "7. Devolution Claim Review: ")
    add_bullet_p(doc, "Step 8: Exporting Daily Accounts — At the close of business, the DDO clicks 'Export CSV' on the Collection Register to download a statutory audit copy of daily collections for departmental cashbook reconciliation.", "8. Cashbook Export: ")

    add_heading_2(doc, "4.3 Complete DDO Screen, Form, and Database Traceability Matrix")
    add_body_p(doc, "Every action performed by a DDO is mapped below to the exact form field, validation check, API endpoint, database table, and resulting status:")

    ddo_headers = ["Step", "Screen Name", "Form / Field / Button", "DDO Action", "Client Validation", "Lookup Source & Condition", "Backend API & Function", "Target Database Table", "Operation", "Resulting Status / State"]
    ddo_data = [
        ["1", "Collection Register", "Filter Bar: Dept & DDO", "Select Department and DDO Code", "Valid Code", "department, ddo (WHERE is_active=true)", "/api/collection/transactions", "rev_portal_transaction_staging", "SELECT", "Filtered transactions displayed"],
        ["2", "Collection Register", "Button: Validate Single", "Click checkmark on transaction row", "dept_validated = false", "None", "/api/collection/transactions/validate-departmental", "rev_portal_transaction_staging", "UPDATE", "dept_validated = True, dept_validated_by = DDO_ID"],
        ["3", "Collection Register", "Button: Validate All", "Click Validate All Filtered", "Confirmation prompt", "None", "/api/collection/transactions/validate-departmental", "rev_portal_transaction_staging", "UPDATE", "dept_validated = True on all filtered rows"],
        ["4", "Manual Entry Form", "Field: Payer Name", "Enters taxpayer / firm name", "Required, non-empty", "None", "None (Form State)", "None", "None", "Form validation passed"],
        ["5", "Manual Entry Form", "Field: Amount (INR)", "Enters collected amount", "Numeric, > 0.00", "None", "None (Form State)", "None", "None", "Form validation passed"],
        ["6", "Manual Entry Form", "Field: Receipt Head", "Selects Major/Minor Head", "Head must be active", "chart_of_account (WHERE coa_code LIKE '00%')", "None (Form State)", "None", "None", "Head selected from master"],
        ["7", "Manual Entry Form", "Button: Save Manual Collection", "Clicks Save & Submit", "All mandatory fields valid", "fn_rev_next_seq for batch & txn", "/api/collection/manual-receipt (CollectionService.create_manual_receipt)", "rev_upload_batch, rev_portal_transaction_staging", "INSERT", "Batch APPROVED, Staging row inserted, audit_change_log updated"],
        ["8", "Refund Management", "Button: + New Refund Case", "Opens refund creation modal", "Original challan exists", "rev_portal_transaction_staging (Challan match)", "/api/refunds/cases (RefundService.create_refund_case)", "rev_refund_case", "INSERT", "Case created, status = DRAFT / DDO_SUBMITTED"],
        ["9", "Refund Management", "Button: Verify with SHCIL", "Executes certificate lock", "Certificate valid token", "External SHCIL portal API", "/api/refunds/cases/{id}/verify-shcil (RefundService.verify_shcil)", "rev_refund_verification, rev_refund_case", "INSERT/UPDATE", "Certificate locked, status = SHCIL_VERIFIED"],
        ["10", "Devolution", "Button: Compute Devolution", "Initiates entitlement calculation", "Period selected", "rev_devolution_rule, rev_recon_result", "/api/devolution/compute (DevolutionService.compute_devolution)", "rev_devolution_computation, rev_devolution_claim", "SELECT/INSERT", "Entitlement computed for local body"]
    ]
    add_table_data(doc, ddo_headers, ddo_data, [0.4, 0.9, 1.0, 0.9, 0.8, 0.9, 1.0, 1.0, 0.6, 0.9])

    add_heading_2(doc, "4.4 What a DDO CANNOT Access (Restricted Modules)")
    add_body_p(doc, "To maintain strict statutory segregation of duties, the DDO role is explicitly denied access to:")
    add_bullet_p(doc, "The DDO cannot view bank delay records or issue penal demand notices. This is exclusively a PAO / Treasury / Bank Operations function.", "Bank SLA & Penal Interest (#sla): ")
    add_bullet_p(doc, "The DDO cannot generate accounting vouchers or post to the budget ledger. Only PAO Maker and PAO Checker may book revenue into treasury accounts.", "Accounting & Vouchers (#accounting): ")
    add_bullet_p(doc, "The DDO cannot approve upload batches or authorize reconciliation overrides. Checker approval is reserved for PAO Checker.", "Checker Approval Actions: ")

    # =========================================================================
    # 7. COMPLETE BUSINESS WORKFLOW (LIFECYCLE STAGES A THROUGH I)
    # =========================================================================
    add_heading_1(doc, "5. The Complete Revenue Reconciliation Lifecycle")
    add_body_p(doc, "The end-to-end operational cycle progresses through nine disciplined stages (Stages A through I):")

    stages = [
        ("Stage A: Baseline Master Verification", "Treasury Administration and System Administrator verify active Chart of Accounts receipt heads, agency bank clearing accounts, SLA rules, and revenue portals in Masters (#masters)."),
        ("Stage B: Departmental Portal Ingestion", "Departmental receipts are ingested via CSV upload or API into rev_portal_transaction_staging. Batch status is set to PENDING_APPROVAL in rev_upload_batch."),
        ("Stage C: Agency Bank Scroll Ingestion", "Agency banks transmit daily electronic scrolls detailing collections remitted. Ingested into rev_agency_bank_scroll_staging with batch status PENDING_APPROVAL."),
        ("Stage D: RBI E-Kuber Settlement Ingestion", "Daily clearance files from the RBI Central Accounts Section (CAS) Nagpur are ingested into rev_rbi_luggage_staging with batch status PENDING_APPROVAL."),
        ("Stage E: Data Validation & Rejection Auditing", "The ingestion pipeline validates schema integrity, required fields, date formats, and duplicate records. Rejected rows are isolated into rev_upload_rejected_row."),
        ("Stage F: PAO Checker Batch Authorization", "The PAO Checker scrutinizes batch control totals. Upon verification, the Checker executes sp_rev_approve_upload_batch, advancing batch status to APPROVED."),
        ("Stage G: 3-Way Auto-Reconciliation Engine", "The PAO Maker triggers POST /api/recon/run. The engine executes Rules R01 to R08, linking evidence in rev_recon_leg_linkage and populating rev_recon_result."),
        ("Stage H: Outcomes Review & Exception Triage", "Reconciliation results are triaged into Matched, Suspend (portal only), RAT (bank credit without challan), Mismatch, and Duplicate. Exceptions are routed to rev_exception."),
        ("Stage I: Dual-COA Accounting & Ledger Booking", "PAO Maker generates draft vouchers via sp_rev_create_booking_vouchers. PAO Checker bulk approves vouchers via sp_rev_approve_booking_vouchers, and posts to budget_ledger_entry.")
    ]
    for s_title, s_desc in stages:
        add_bullet_p(doc, s_desc, bold_prefix=f"{s_title} — ")

    # =========================================================================
    # 8. 3-WAY RECONCILIATION MATCHING ENGINE & RULES (R01 TO R08)
    # =========================================================================
    add_heading_1(doc, "6. Reconciliation Rules Engine & Matching Hierarchy")
    add_body_p(doc, "The automated matching engine (ReconEngine) applies an 8-tier hierarchical waterfall to pair staged records. Once a record matches under a higher-priority rule, it is locked and excluded from subsequent passes.")

    rules_headers = ["Rule ID", "Rule Name", "Matching Logic & Evidence Columns", "Tolerance Window", "Outcome Status", "Target Database Table"]
    rules_data = [
        ["R01", "Exact 3-Way Primary Match", "Exact equality on Challan No + CIN + CPIN + Amount across Portal, Bank, and RBI legs.", "Zero tolerance (Exact)", "Matched", "rev_recon_result, rev_recon_leg_linkage"],
        ["R02", "CIN + Amount Match", "Matches on CIN (Challan Identification Number) + exact Amount across Portal and Bank scroll.", "Amount = 0.00 diff", "Matched", "rev_recon_result, rev_recon_leg_linkage"],
        ["R03", "Challan + Amount Match", "Matches on Departmental Challan Number + exact Amount across Portal and Bank scroll.", "Amount = 0.00 diff", "Matched", "rev_recon_result, rev_recon_leg_linkage"],
        ["R04", "Date Tolerance Match", "Matches on Challan No + Amount where remittance date is within +/- 2 calendar days.", "Date variance <= 2 days", "Matched", "rev_recon_result, rev_recon_leg_linkage"],
        ["R05", "Amount Tolerance Match", "Matches on Challan No + Date where amount variance is within +/- Rs. 5.00 (bank rounding).", "Amount diff <= 5.00", "Matched", "rev_recon_result, rev_recon_leg_linkage"],
        ["R06", "One-to-Many Part Settlement", "One bulk portal payment settled across multiple bank scroll lines (sum of scroll amounts = portal amount).", "Sum equality exact", "Matched", "rev_recon_result, rev_recon_leg_linkage"],
        ["R07", "Two-Way Provisional Match", "Matches Portal and Bank scroll legs when RBI settlement file is still awaited.", "Zero tolerance", "Pending (2-Way)", "rev_recon_result, rev_recon_leg_linkage"],
        ["R08", "Manual Override Linkage", "Manual pairing approved by PAO Checker upon formal verification of bank proof.", "Checker Authorization", "Matched (Override)", "rev_recon_override, rev_recon_result"]
    ]
    add_table_data(doc, rules_headers, rules_data, [0.6, 1.4, 2.0, 1.0, 0.9, 1.2])

    # =========================================================================
    # 9. BANK SLA PERFORMANCE & PENAL INTEREST ENGINE
    # =========================================================================
    add_heading_1(doc, "7. Bank Remittance SLA & Penal Interest Calculations")
    add_body_p(doc, "Under statutory guidelines, commercial agency banks acting as accredited government agents must remit collected revenue into the Government Account at the Reserve Bank of India within strict cutoff windows.")
    
    add_heading_2(doc, "7.1 Statutory Turnaround Time (TAT) Thresholds")
    add_bullet_p(doc, "Funds must be remitted by the next banking day (T+1). Delay begins on T+2.", "Electronic Modes (Netbanking, Debit/Credit Card, UPI, RTGS/NEFT): ")
    add_bullet_p(doc, "Funds must be remitted by the next banking day (T+1). Delay begins on T+2.", "Physical Cash Collections at Bank Counters: ")
    add_bullet_p(doc, "Funds must be remitted within 2 working days after cheque realisation (Realisation+2). Delay begins on Realisation+3.", "Cheque and Demand Draft Collections: ")

    add_heading_2(doc, "7.2 Penal Interest Formula")
    add_body_p(doc, "When a bank breaches the statutory turnaround window, penal interest is automatically computed by the database function fn_rev_compute_penal_interest:")
    
    add_callout(doc, "Statutory Formula", "Penal Interest (INR) = [Remittance Amount × (Bank Repo Rate + 200 bps) × Days of Delay] ÷ [365 × 100]\nWhere: Repo Rate = 6.50% p.a., Penalty Spread = 2.00% p.a. -> Effective Penal Rate = 8.50% p.a.", "warn")

    add_heading_2(doc, "7.3 Demand & Recovery Lifecycle")
    add_bullet_p(doc, "The PAO Maker reviews computed delays and clicks 'Issue Demand Notice'. This creates a record in rev_penal_letter and transitions the claim to DEMAND_ISSUED.", "1. Demand Issuance: ")
    add_bullet_p(doc, "The Agency Bank submits payment reference and settlement advice. Handled via POST /api/sla/claims/{id}/bank-response, updating rev_penal_bank_response and setting status to SETTLED.", "2. Bank Response / Recovery: ")
    add_bullet_p(doc, "Under exceptional circumstances (system outages, declared bank strikes), the Finance Department may grant a waiver via POST /api/sla/claims/{id}/waiver, recording justification in rev_penal_waiver and setting status to WAIVED.", "3. Statutory Waiver: ")

    # =========================================================================
    # 10. DUAL-COA ACCOUNTING & VOUCHER BOOKING
    # =========================================================================
    add_heading_1(doc, "8. Dual-COA Accounting & Budget Ledger Posting")
    add_body_p(doc, "The module implements automated double-entry classification ensuring that all matched receipts are booked into live treasury accounting books.")

    add_heading_2(doc, "8.1 Accounting Voucher Structure")
    add_body_p(doc, "Every matched receipt generates an accounting voucher in ifms_budget.account_voucher with two distinct debit-credit legs:")
    add_bullet_p(doc, "Debit Head: 8658-00-102-01-00-01 (Remittance in Transit / Agency Bank Clearing). Credit Head: Departmental Revenue Major/Minor Head (e.g. 0040-00-102-01-00-01 Taxes on Sales/SGST). Amount: Full Gross Collection.", "Leg 1 (Principal Revenue Receipt): ")
    add_bullet_p(doc, "Debit Head: 8658-00-102-01-00-02 (Agency Bank Clearing - Penal Interest). Credit Head: 0049-04-800-01-00-01 (Interest Receipts from Commercial Banks). Amount: Computed Penal Interest.", "Leg 2 (Penal Interest Component, if applicable): ")

    add_heading_2(doc, "8.2 Stored Procedure Execution Trace")
    add_body_p(doc, "1. Bulk Voucher Generation: PAO Maker clicks 'Bulk Generate Vouchers' -> Backend calls sp_rev_create_booking_vouchers(p_user_id, p_pao_code) -> Database inserts rows into account_voucher with status 'Draft' and updates rev_recon_result.booking_status to 'DRAFT_VOUCHER'.")
    add_body_p(doc, "2. Bulk Voucher Approval: PAO Checker clicks 'Approve Vouchers' -> Backend calls sp_rev_approve_booking_vouchers(p_checker_id, p_remarks) -> Database updates account_voucher.status to 'Approved' and sets rev_recon_result.booking_status to 'BOOKED'.")
    add_body_p(doc, "3. General Ledger Posting: User clicks 'Post to Ledger' -> Backend executes fn_post_budget_ledger, creating official balanced debits and credits in budget_ledger_entry and setting account_voucher.workflow_status to 'POSTED'.")

    # =========================================================================
    # 11. REPORTS & MIS CATALOGUE (ALL 17 REPORTS)
    # =========================================================================
    add_heading_1(doc, "9. Statutory Reports & Executive MIS Catalogue")
    add_body_p(doc, "The system incorporates 17 statutory and operational reports querying live PostgreSQL tables with parameter filtering (Date, Source, Bank, PAO, Department) and CSV export.")

    rpt_headers = ["ID", "Report Title", "Statutory Category", "Data Source Tables & Views", "Core Filter Parameters", "Reporting Purpose"]
    rpt_data = [
        ["R01", "Daily Revenue Collection Report", "Collection", "rev_portal_transaction_staging, rev_recon_result", "from_date, to_date, source_id, pao_code", "Daily gross revenue yields by payment mode and reconciliation position."],
        ["R02", "Source-wise Tax vs Non-Tax Report", "Collection", "rev_portal_transaction_staging, rev_revenue_source", "from_date, to_date, dept_code", "Breakdown by tax vs non-tax sources with budget target variance."],
        ["R03", "3-Way Reconciliation Summary", "Reconciliation", "rev_recon_result, rev_recon_leg_linkage", "from_date, to_date, source_id", "Control totals comparing Portal vs Bank Scroll vs RBI Luggage."],
        ["R04", "Transaction-wise Reconciliation Report", "Reconciliation", "rev_recon_result, rev_portal_transaction_staging", "challan_no, cin, status, date range", "Line-level audit register with rule applied and evidence linkages."],
        ["R05", "Pending Reconciliation Report", "Reconciliation", "rev_recon_result, rev_pao, department", "pao_code, dept_code, ageing", "Grouped unreconciled exposure by department and Pay & Accounts Office."],
        ["R06", "Suspense and RAT Report", "Reconciliation", "rev_recon_result, rev_suspense_register", "status IN ('Suspend', 'RAT'), date range", "Portal receipts held in suspense and unclassified bank credits."],
        ["R07", "Amount Mismatch & Duplicate Report", "Reconciliation", "rev_recon_result", "status IN ('Mismatch', 'Duplicate')", "Variance analysis between claimed portal amount and credited bank amount."],
        ["R08", "Bank Scroll Receipt & Processing Report", "Agency Bank", "rev_agency_bank_scroll_staging, agency_bank", "bank_id, from_date, to_date", "Bank scroll transmission audit, processed volume, and rejected counts."],
        ["R09", "Bank Remittance SLA Performance", "Agency Bank", "rev_recon_result, rev_sla_rule, agency_bank", "bank_id, delay_days > 0", "Line-level remittance delay analysis with computed penal interest."],
        ["R10", "Penal Interest Recovery Register", "Agency Bank", "rev_penal_claim, rev_penal_letter, rev_penal_waiver", "bank_id, status (ISSUED/SETTLED/WAIVED)", "Recovery progress, demand notices, bank settlements, and waivers."],
        ["R11", "Refund Register & Ageing Analysis", "Revenue Refund", "rev_refund_case, rev_refund_bill", "refund_type, status, ageing_days", "Refund cases with stage progression, sanction dates, and TAT ageing."],
        ["R12", "Refund Turnaround Time (TAT) Report", "Revenue Refund", "rev_refund_case, rev_refund_verification", "from_date, to_date, department", "Stage-wise average turnaround time from submission to disbursement."],
        ["R13", "Local Body Devolution Register", "Devolution", "rev_devolution_claim, rev_devolution_advice", "local_body_id, financial_year", "Net revenue sharing entitlements, deductions, and payment advice status."],
        ["R14", "Receipt-Head Collection & Booking", "Accounting", "account_voucher, chart_of_account", "coa_code, financial_year", "Receipt Head collection against Budget Estimates and booking status."],
        ["R15", "Complete Exception Register", "Governance", "rev_exception, rev_recon_result", "severity, exception_type, owner_role", "Master exception queue with resolution status, notes, and ownership."],
        ["R16", "User Activity & Audit Trail Report", "Governance", "audit_change_log, app_user", "table_name, user_id, action, date range", "Forensic audit log of all system insertions, updates, and deletes."],
        ["R17", "Upload Batch & Data Quality Report", "Governance", "rev_upload_batch, rev_upload_rejected_row", "batch_type, status, from_date", "Data quality metrics, rejected row analysis, and checker approvals."]
    ]
    add_table_data(doc, rpt_headers, rpt_data, [0.4, 1.4, 0.9, 1.3, 1.1, 1.4])

    # =========================================================================
    # 12. "WHY IS DATA NOT SHOWING?" TROUBLESHOOTING GUIDE (MANDATORY)
    # =========================================================================
    add_heading_1(doc, "10. 'Why Is Data Not Showing?' — Operational Troubleshooting Guide")
    add_callout(doc, "Crucial Operational Guide", "When a user reports: 'A department/PAO/challan/record is not appearing in the dropdown or list', the support team and operational users must follow these exact diagnostic rules.", "warn")

    why_headers = ["Component / Control", "User Symptom", "Exact Code / Database Condition", "Direct Diagnostic SQL Query", "Remediation Procedure"]
    why_data = [
        ["Department Dropdown", "Department name missing in filter or manual entry form.",
         "is_active = true flag in ifms_budget.department.",
         "SELECT department_id, department_code, is_active FROM ifms_budget.department WHERE department_code = 'XYZ';",
         "If is_active is false, update via Masters > Departments or SQL: UPDATE ifms_budget.department SET is_active=true WHERE department_code='XYZ'."],

        ["PAO Dropdown", "PAO office missing from selection list.",
         "rev_pao.is_active = true AND (department_id = selected_dept OR DDO mapped).",
         "SELECT pao_id, pao_code, department_id, is_active FROM ifms_budget.rev_pao WHERE pao_code = 'PAO21';",
         "Verify PAO is active and check if a department filter is active in the UI restricting PAO choices."],

        ["DDO Dropdown", "DDO code not visible during manual receipt capture.",
         "ddo.is_active = true AND ddo.department_id = selected_department_id.",
         "SELECT ddo_id, ddo_code, department_id, is_active FROM ifms_budget.ddo WHERE ddo_code = 'DDO-TT-001';",
         "Ensure selected department matches DDO's parent department. DDO cannot select an unmapped department."],

        ["Receipt Head (COA)", "Head of account missing in Collection or Accounting.",
         "chart_of_account.is_active = true AND coa_code LIKE '00%' (Only Revenue Heads).",
         "SELECT coa_id, coa_code, coa_name, is_active FROM ifms_budget.chart_of_account WHERE coa_code = '0040-00-102-01-00-01';",
         "Expenditure heads (starting with 2xxx or 4xxx) are excluded by design. Ensure head is marked is_active=true."],

        ["Agency Bank Dropdown", "Bank not listed in upload or SLA dropdown.",
         "agency_bank.is_active = true (AND for Bank Ops: bank_code = user's assigned bank).",
         "SELECT bank_id, bank_code, bank_name, is_active FROM ifms_budget.agency_bank WHERE bank_code = 'SBI';",
         "Activate bank in Masters > Agency Banks. For Bank Ops user, ensure user is assigned to correct bank."],

        ["Upload Batches", "Batch not visible for 3-way reconciliation.",
         "rev_upload_batch.status must be 'APPROVED'. PENDING_APPROVAL batches are excluded.",
         "SELECT batch_id, batch_no, batch_type, status FROM ifms_budget.rev_upload_batch WHERE batch_no = 'BAT-XXX';",
         "PAO Checker must approve batch via Data Upload Centre (#upload) before it enters reconciliation."],

        ["Reconciliation Result", "Challan shows as Unmatched / Mismatch instead of Matched.",
         "Amount difference > tolerance window (+/- Rs. 5) OR date variance > 2 days.",
         "SELECT recon_id, challan_no, portal_total, bank_total, rbi_total, amount_difference, status FROM ifms_budget.rev_recon_result WHERE challan_no = 'CH-XXX';",
         "Review Exception Details. If justified, PAO Maker initiates Propose Override and PAO Checker authorizes."],

        ["Refund Case", "Bill cannot be prepared for refund case.",
         "rev_refund_case.status must be 'PAO_APPROVED'.",
         "SELECT refund_id, case_no, status, current_stage FROM ifms_budget.rev_refund_case WHERE case_no = 'REF-XXX';",
         "Case must complete SHCIL verification and PAO Scrutiny before bill preparation is unlocked."]
    ]
    add_table_data(doc, why_headers, why_data, [1.0, 1.2, 1.3, 1.6, 1.4])

    # =========================================================================
    # 13. AUDIT TRAIL & CHANGE DATA CAPTURE (CDC)
    # =========================================================================
    add_heading_1(doc, "11. Security Audit Trail & Change Data Capture (CDC)")
    add_body_p(doc, "The IFMS Revenue module implements an immutable, tamper-evident audit logging architecture backed by PostgreSQL triggers and the audit_change_log table.")

    add_heading_2(doc, "11.1 Audit Table Schema (ifms_budget.audit_change_log)")
    add_body_p(doc, "Every critical transaction table has an AFTER INSERT OR UPDATE OR DELETE trigger executing fn_rev_audit_handler or fn_log_change:")
    add_bullet_p(doc, "Unique monotonically increasing integer primary key.", "audit_id: ")
    add_bullet_p(doc, "Name of the target table modified (e.g. rev_recon_result, rev_refund_case, account_voucher).", "table_name: ")
    add_bullet_p(doc, "Primary key of the specific modified row.", "row_pk: ")
    add_bullet_p(doc, "Type of SQL manipulation: INSERT, UPDATE, or DELETE.", "operation: ")
    add_bullet_p(doc, "Complete JSONB serialized snapshot of the row BEFORE modification (null for INSERT).", "old_data: ")
    add_bullet_p(doc, "Complete JSONB serialized snapshot of the row AFTER modification (null for DELETE).", "new_data: ")
    add_bullet_p(doc, "Authenticated User ID who executed the action.", "changed_by: ")
    add_bullet_p(doc, "Microsecond-accurate timestamp generated via clock_timestamp().", "changed_at: ")

    add_heading_2(doc, "11.2 Frontend Audit Trail & Field Diff Inspector")
    add_body_p(doc, "Authorized users and statutory auditors inspect the audit trail via Security Audit Trail (#audit). The screen provides:")
    add_bullet_p(doc, "Filters by Table Name, Module, Action Type (INSERT/UPDATE/DELETE), User ID, and Date Range.", "Multi-Dimensional Filtering: ")
    add_bullet_p(doc, "Clicking 'View Diff' opens a side-by-side comparison modal highlighting exact field-level changes between old_data and new_data, with green indicators for new values and red for modified previous values.", "Interactive Side-by-Side Diff Modal: ")
    add_bullet_p(doc, "Collapsible JSON viewer displaying the exact JSON payloads stored in PostgreSQL for forensic verification.", "Raw JSON Inspection: ")

    # =========================================================================
    # 14. ANNEXURES
    # =========================================================================
    doc.add_page_break()
    add_heading_1(doc, "Annexure A: Database Tables Catalog (ifms_budget)")
    add_body_p(doc, "The ifms_budget schema contains 93 base tables and 16 views. Below is the complete catalog of primary revenue and core treasury tables:")

    ann_headers = ["Table Name", "Table Category", "Primary Key", "Core Columns & Types", "Operational Purpose"]
    ann_data = [
        ["rev_portal_transaction_staging", "Staging / Ingestion", "portal_item_id (bigint)", "challan_no, cin, cpin, amount (num 17,2), payment_date, dept_validated", "Ingestion staging table for all departmental portal collections."],
        ["rev_agency_bank_scroll_staging", "Staging / Ingestion", "scroll_item_id (bigint)", "bank_code, scroll_no, remittance_date, amount, utr_no", "Ingestion staging table for commercial agency bank scrolls."],
        ["rev_rbi_luggage_staging", "Staging / Ingestion", "rbi_item_id (bigint)", "rbi_reference_no, settlement_date, credit_date, amount, rbi_status", "Ingestion staging table for RBI E-Kuber daily luggage settlement."],
        ["rev_upload_batch", "Staging Control", "batch_id (bigint)", "batch_no, batch_type, total_records, valid_records, control_total, status", "Batch control header governing ingestion lifecycle and checker approval."],
        ["rev_upload_rejected_row", "Audit & Quality", "rejection_id (bigint)", "batch_id, row_number, raw_data, rejection_reason", "Stores rejected lines failing CSV schema or mandatory business rules."],
        ["rev_recon_result", "Reconciliation", "recon_id (bigint)", "status, match_rule, portal_total, bank_total, rbi_total, amount_diff, booking_status", "Consolidated 3-way reconciliation master record and matching status."],
        ["rev_recon_leg_linkage", "Reconciliation", "linkage_id (bigint)", "recon_id, portal_item_id, scroll_item_id, rbi_item_id", "Foreign key linkages joining the three independent evidence legs."],
        ["rev_recon_override", "Reconciliation", "override_id (bigint)", "recon_id, proposed_status, maker_id, checker_id, justification, status", "Tracks maker-checker manual match override requests and approvals."],
        ["rev_exception", "Exceptions", "exception_id (bigint)", "recon_id, exception_type, severity, status, resolution_notes", "Exception lifecycle tracking for suspense, RAT, mismatches, and duplicates."],
        ["rev_exception_letter", "Exceptions", "letter_id (bigint)", "recon_id, letter_no, bank_code, issue_date, demand_amount, status", "Official discrepancy notices issued to agency banks."],
        ["rev_penal_claim", "SLA & Penal", "claim_id (bigint)", "bank_code, delay_days, interest_amount, status", "Statutory penal interest claims assessed against agency banks."],
        ["rev_penal_letter", "SLA & Penal", "letter_id (bigint)", "claim_id, letter_no, bank_code, interest_amount, status", "Formal demand letters issued for recovery of penal interest."],
        ["rev_penal_bank_response", "SLA & Penal", "response_id (bigint)", "claim_id, response_type, agreed_amount, payment_ref", "Records bank recovery payments or formal dispute explanations."],
        ["rev_penal_waiver", "SLA & Penal", "waiver_id (bigint)", "claim_id, waived_amount, reason_code, sanction_order_no", "Records statutory penal interest waivers authorized by Finance Dept."],
        ["account_voucher", "Accounting", "voucher_id (bigint)", "voucher_no, voucher_type, debit_coa_id, credit_coa_id, amount, status", "Dual-COA accounting vouchers booking revenue into treasury ledger."],
        ["rev_refund_case", "Refunds", "refund_id (bigint)", "case_no, refund_type, challan_no, refund_amount, status, current_stage", "Master revenue refund case record tracking 7-stage lifecycle."],
        ["rev_refund_verification", "Refunds", "verification_id (bigint)", "refund_id, verification_type, verification_result, certificate_locked", "Audit record of e-stamp / departmental certificate validation."],
        ["rev_refund_bill", "Refunds", "bill_id (bigint)", "refund_id, bill_no, gross_amount, net_payable, debit_head_id", "Official treasury refund payment bill."],
        ["rev_devolution_claim", "Devolution", "claim_id (bigint)", "local_body_id, revenue_source_id, gross_amount, net_payable, status", "Local body revenue sharing claims and entitlements."],
        ["rev_devolution_advice", "Devolution", "advice_id (bigint)", "claim_id, advice_no, approved_amount, treasury_code, status", "Formal Treasury Devolution Advice issued for municipal settlement."],
        ["audit_change_log", "Security & Audit", "audit_id (bigint)", "table_name, operation, row_pk, old_data (jsonb), new_data (jsonb), changed_by, changed_at", "Immutable Change Data Capture security and transaction audit register."]
    ]
    add_table_data(doc, ann_headers, ann_data, [1.4, 0.9, 1.1, 1.5, 1.6])

    add_heading_1(doc, "Annexure B: Stored Procedures & Triggers Specification")
    add_body_p(doc, "Key stored procedures and database triggers in ifms_budget:")
    add_bullet_p(doc, "Validates and transitions upload batch from PENDING_APPROVAL to APPROVED. Executed by PAO Checker.", "sp_rev_approve_upload_batch(batch_id, checker_id, remarks): ")
    add_bullet_p(doc, "Generates dual-COA Draft receipt vouchers and penal interest rows for Matched reconciliation items.", "sp_rev_create_booking_vouchers(user_id, pao_code): ")
    add_bullet_p(doc, "Bulk approves Draft vouchers by PAO Checker and sets booking_status to BOOKED.", "sp_rev_approve_booking_vouchers(checker_id, remarks): ")
    add_bullet_p(doc, "Generates atomic, zero-padded document sequence numbers (BATCH_SEQ, TXN_SEQ, VOUCHER_SEQ, REFUND_SEQ, ADVICE_SEQ).", "fn_rev_next_seq(sequence_key, prefix, fy): ")
    add_bullet_p(doc, "Computes remittance delay beyond statutory SLA turnaround threshold (T+1 or Realisation+2).", "fn_rev_calculate_delay_days(payment_date, remittance_date, mode): ")
    add_bullet_p(doc, "Calculates statutory penal interest on delayed remittances at Repo Rate + 200 bps (8.5% p.a.).", "fn_rev_compute_penal_interest(amount, delay_days, repo_rate): ")
    add_bullet_p(doc, "CDC Trigger on rev_recon_result, capturing all automated and manual state changes into audit_change_log.", "trg_rev_recon_audit: ")
    add_bullet_p(doc, "CDC Trigger on rev_refund_case, tracking all stage advancements and approvals in audit_change_log.", "trg_rev_refund_audit: ")

    add_heading_1(doc, "Annexure C: Comprehensive Treasury Terminology Glossary")
    terms = [
        ("CPIN (Common Portal Identification Number)", "A 14-digit unique identifier generated by the revenue portal (e.g. GSTN) when a taxpayer creates a payment challan online."),
        ("CIN (Challan Identification Number)", "A 17-digit number generated by the collecting agency bank upon receiving funds, comprising the 7-digit bank BSR code, 8-digit challan date, and 5-digit serial number."),
        ("UTR (Unique Transaction Reference)", "A 16- or 22-character alphanumeric code generated in the RTGS / NEFT interbank clearing system confirming successful settlement."),
        ("RAT (Receipt Awaiting Transfer)", "A credit appearing on the agency bank scroll or RBI account for which no corresponding departmental portal challan can be found."),
        ("Suspense Record", "A departmental transaction indicating citizen payment but for which no matching agency bank remittance credit has arrived within SLA."),
        ("Dual-COA Classification", "Simultaneous double-entry booking crediting the statutory Revenue Receipt Major/Minor Head and debiting the Remittance-in-Transit Suspense Head 8658."),
        ("Luggage File", "The consolidated daily electronic scroll transmitted by RBI Central Accounts Section (CAS) Nagpur to the State Treasury summarizing agency bank net daily settlements."),
        ("Four-Eyes Principle", "Statutory requirement that every financial transaction involving government revenue ingestion, override, or disbursement must be initiated by a Maker and authorized by a distinct Checker.")
    ]
    for t_name, t_def in terms:
        add_bullet_p(doc, t_def, bold_prefix=f"{t_name} — ")

    # Save
    out_file = "IFMS_BUDGET_UPDATED_SOP.docx"
    doc.save(out_file)
    print(f"Successfully generated {out_file} ({os.path.getsize(out_file)} bytes)!")

if __name__ == '__main__':
    build_sop_document()
