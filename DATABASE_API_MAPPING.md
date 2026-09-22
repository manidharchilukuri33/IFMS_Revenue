# IFMS REVENUE COLLECTION & RECONCILIATION MODULE
## COMPLETE DATABASE & API IMPLEMENTATION MAPPING SPECIFICATION

**Document Version**: 1.0.0  
**Target Database**: `ifms_budget` (PostgreSQL 14+)  
**Target Schema**: `ifms_budget`  
**Application Architecture**: React + TypeScript (Vite) &harr; FastAPI (Python 3.10+) &harr; PostgreSQL (`ifms_budget`)

---

## TABLE OF CONTENTS
1. [Architecture & System Context](#1-architecture--system-context)
2. [Role-Based Access Control (RBAC) & Capabilities](#2-role-based-access-control-rbac--capabilities)
3. [Module-by-Module Detailed Mapping](#3-module-by-module-detailed-mapping)
   - [3.1 Executive Dashboard (`/dashboard`)](#31-executive-dashboard-dashboard)
   - [3.2 Data Collection & Transaction Register (`/collection`)](#32-data-collection--transaction-register-collection)
   - [3.3 File Upload & Dual-Control Staging (`/upload`)](#33-file-upload--dual-control-staging-upload)
   - [3.4 3-Way Reconciliation Engine (`/recon`)](#34-3-way-reconciliation-engine-recon)
   - [3.5 Exceptions Management & Resolution (`/exceptions`)](#35-exceptions-management--resolution-exceptions)
   - [3.6 Agency Bank SLA & Penal Interest Recovery (`/sla`)](#36-agency-bank-sla--penal-interest-recovery-sla)
   - [3.7 Multi-Stage Refund Management (`/refund`)](#37-multi-stage-refund-management-refund)
   - [3.8 Citizen Refund Tracking (`/citizen-refund`)](#38-citizen-refund-tracking-citizen-refund)
   - [3.9 Statutory Revenue Devolution (`/devolution`)](#39-statutory-revenue-devolution-devolution)
   - [3.10 Revenue Accounting & Voucher Posting (`/accounting`)](#310-revenue-accounting--voucher-posting-accounting)
   - [3.11 Analytical Reports & MIS (`/reports`)](#311-analytical-reports--mis-reports)
   - [3.12 Masters & System Configuration (`/masters`)](#312-masters--system-configuration-masters)
   - [3.13 Change Data Capture & Audit Trail (`/audit`)](#313-change-data-capture--audit-trail-audit)
   - [3.14 Help, Sample File Formats & Automated Test Suite (`/help`)](#314-help-sample-file-formats--automated-test-suite-help)
4. [Master Schema Cross-Reference & Foreign Key Matrix](#4-master-schema-cross-reference--foreign-key-matrix)
5. [Transaction & Concurrency Safety Rules](#5-transaction--concurrency-safety-rules)

---

## 1. Architecture & System Context

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               REACT + TYPESCRIPT UI                                    │
│   (Vite SPA, Tailwind CSS / HTML Reference Styling, Typed API Client, Zero LocalStorage)│
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ HTTP REST (JSON / Multipart)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                FASTAPI BACKEND LAYER                                   │
│  ┌────────────────────┬────────────────────┬───────────────────┬─────────────────────┐ │
│  │   API Routers      │  Pydantic Schemas  │  Service Layer    │  Repo / SQL Engine  │ │
│  │  (Auth, Upload,    │  (Request/Response │  (Business Rules, │  (Async/Sync        │ │
│  │   Recon, SLA, etc) │   Strict Validate) │   Recon Engine,   │   Session Handling, │ │
│  │                    │                    │   Workflows)      │   Transactions)     │ │
│  └────────────────────┴────────────────────┴───────────────────┴─────────────────────┘ │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │ PostgreSQL Connection Pool (Port 5432)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     POSTGRESQL DATABASE: ifms_budget (SCHEMA: ifms_budget)             │
│  ┌──────────────────────────────────────────────┬────────────────────────────────────┐ │
│  │ Existing Common & Budget Tables (Unmodified) │ New Revenue Objects (Prefix: rev_) │ │
│  │ • organization, department, ddo, app_user    │ • 33 Tables (Staging, Recon, SLA,  │ │
│  │ • role, permission, chart_of_account         │   Refunds, Devolution, Vouchers)   │ │
│  │ • audit_change_log, document_number_sequence │ • 4 Realtime Views (rev_vw_*)      │ │
│  │ • major_head, minor_head, sub_head, etc.     │ • 4 Functions & 3 Procedures       │ │
│  └──────────────────────────────────────────────┴────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Role-Based Access Control (RBAC) & Capabilities

The application implements strict server-side authorization mapped to the 8 standard IFMS roles:

| Role Code | Role Name | Allowed Routes / Key Capabilities |
| :--- | :--- | :--- |
| `SYSADMIN` | System Administrator | All routes, Master Data Maintenance, System Configuration, Demo Reset, Test Suite Execution |
| `TRE_ADMIN` | Treasury Administrator | All routes, Batch Management, Recon Execution, Reset, Exceptions, SLA, Devolution, Reports |
| `PAO_MAKER` | PAO Maker (Operator) | Dashboard, Collection, Upload, Recon Run, Exceptions, SLA Letters, Refund Processing, Devolution Claims, Draft Vouchers |
| `PAO_CHECK` | PAO Checker (Approver) | Dashboard, Collection, Batch Approval, Recon Override Approval, SLA Waiver Approval, Refund Approval, Voucher Approval |
| `DDO` | Drawing & Disbursing Officer | Dashboard, Collection, Departmental Validation, Refund Preparation, Devolution Claims |
| `FINANCE` | Finance Department Officer | Dashboard, Collection, Recon Oversight, SLA Monitoring, Refund Scrutiny, Devolution Approval, Reports |
| `BANK_OPS` | Agency Bank Operations Officer | Dashboard, Collection, Bank Scroll Upload, Bank SLA Responses, Reports |
| `AUDITOR` | CAG / Internal Auditor | Read-only access across Dashboard, Collection, Uploads, Recon, SLA, Refunds, Accounting, Audit Trail, Reports |
| `CITIZEN` | Public Taxpayer / Citizen | Public Portal: Citizen Refund Application & Real-time Status Tracking |

---

## 3. Module-by-Module Detailed Mapping

### 3.1 Executive Dashboard (`/dashboard`)

*Source Reference*: HTML Fragment 10 (`viewDashboard`), SOP Section 3.1

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 12 Key Performance Indicators (Gross Collection, Reconciled, Pending, Suspense, RAT, Mismatch, SLA Delays, Penal Interest) | Page Load / Date Filter Change | `GET /api/v1/dashboard/kpis?date={date}&fy={fy}` | `routers/dashboard.py`<br>`DashboardService.get_kpis` | `ifms_budget.rev_vw_dashboard_kpis`<br>`ifms_budget.rev_recon_result`<br>`ifms_budget.rev_penal_claim` | N/A (Aggregated Query / Materialized View) | Read-only |
| Reconciliation Status Donut & Breakdown Table | Filter by Status / Date | `GET /api/v1/dashboard/recon-summary` | `routers/dashboard.py`<br>`DashboardService.get_recon_summary` | `ifms_budget.rev_vw_3way_recon_summary` | N/A (View) | Read-only |
| Source-wise Collection Bar Chart | Filter by Revenue Source | `GET /api/v1/dashboard/source-distribution` | `routers/dashboard.py`<br>`DashboardService.get_source_stats` | `ifms_budget.rev_portal_transaction_staging`<br>`ifms_budget.rev_revenue_source` | `rev_revenue_source.source_id` | Read-only |
| Quick Action: "Run Reconciliation" | Button Click | `POST /api/v1/recon/runs` | `routers/recon.py`<br>`ReconEngineService.run_recon` | `ifms_budget.rev_recon_run`<br>`ifms_budget.rev_recon_result` | PK: `run_id`<br>FK: `executed_by` &rarr; `app_user(user_id)` | `BEGIN..COMMIT`<br>Trigger: `trg_rev_recon_audit` |
| Quick Action: "View Exceptions" | Button Click | Navigation to `/exceptions` | Frontend Navigation | N/A | N/A | N/A |
| Quick Action: "Export Summary" | Button Click | `GET /api/v1/dashboard/export?format=csv` | `routers/dashboard.py`<br>`DashboardService.export_kpis` | `ifms_budget.rev_vw_dashboard_kpis` | N/A | Read-only |

---

### 3.2 Data Collection & Transaction Register (`/collection`)

*Source Reference*: HTML Fragment 11 (`viewCollection`), SOP Section 4

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Departmental Transaction Table | Page Load / Filter by Source, PAO, Date, Search Challan/CIN | `GET /api/v1/collection/transactions` | `routers/collection.py`<br>`CollectionService.list_transactions` | `ifms_budget.rev_portal_transaction_staging` | PK: `portal_item_id`<br>FK: `batch_id` &rarr; `rev_upload_batch` | Read-only |
| Transaction Detail Modal | Click "View" Row Action | `GET /api/v1/collection/transactions/{id}` | `routers/collection.py`<br>`CollectionService.get_transaction_detail` | `ifms_budget.rev_portal_transaction_staging`<br>`ifms_budget.rev_recon_leg_linkage`<br>`ifms_budget.rev_agency_bank_scroll_staging`<br>`ifms_budget.rev_rbi_luggage_staging` | PK: `portal_item_id`<br>FK: `dept_validated_by` &rarr; `app_user(user_id)` | Read-only |
| "Add Manual Collection" Modal Form (Portal, Source, PAO, DDO, Challan, CIN, CPIN, Payer, Mode, Amount, Head) | Submit New Receipt | `POST /api/v1/collection/manual` | `routers/collection.py`<br>`CollectionService.create_manual_receipt` | `ifms_budget.rev_upload_batch`<br>`ifms_budget.rev_portal_transaction_staging` | Batch PK: `batch_id`<br>Item PK: `portal_item_id`<br>FK: `uploaded_by` &rarr; `app_user(user_id)` | `BEGIN..COMMIT`<br>Creates `batch_type='MANUAL_ENTRY'`<br>Logs in `audit_change_log` |
| "Departmental Validation" Button | Checkbox Select & Validate | `POST /api/v1/collection/validate-departmental` | `routers/collection.py`<br>`CollectionService.validate_departmental` | `ifms_budget.rev_portal_transaction_staging` | PK: `portal_item_id`<br>Update: `dept_validated=true`, `dept_validated_by=user_id` | `BEGIN..COMMIT`<br>Logs in `audit_change_log` |

---

### 3.3 File Upload & Dual-Control Staging (`/upload`)

*Source Reference*: HTML Fragment 12 (`viewUpload`), SOP Section 5

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Upload Batches Table (Portal, Bank, RBI files) | Page Load / Filter by Type, Status | `GET /api/v1/uploads/batches` | `routers/upload.py`<br>`UploadService.list_batches` | `ifms_budget.rev_upload_batch` | PK: `batch_id`<br>FK: `department_id`, `bank_id`, `uploaded_by`, `checker_user_id` | Read-only |
| File Upload Modal (Drag & Drop CSV for Portal, Bank Scroll, or RBI Luggage) | Submit File Upload | `POST /api/v1/uploads/process` (Multipart form-data) | `routers/upload.py`<br>`UploadService.process_upload_file` | `ifms_budget.rev_upload_batch`<br>`ifms_budget.rev_portal_transaction_staging`<br>`ifms_budget.rev_agency_bank_scroll_staging`<br>`ifms_budget.rev_rbi_luggage_staging`<br>`ifms_budget.rev_upload_rejected_row` | PK: `batch_id`<br>Child PKs: `portal_item_id`, `scroll_item_id`, `rbi_item_id`, `rejection_id`<br>FK: `batch_id` | `BEGIN..COMMIT`<br>Parses CSV, validates data types, calculates control total, records valid/invalid rows<br>Status: `PENDING_APPROVAL` |
| Batch Records Review Modal | Click "Records" Button | `GET /api/v1/uploads/batches/{id}/records` | `routers/upload.py`<br>`UploadService.get_batch_records` | Staging tables + `rev_upload_rejected_row` | FK: `batch_id` | Read-only |
| Dual-Control Batch Approval | PAO Checker Clicks "Approve" | `POST /api/v1/uploads/batches/{id}/approve` | `routers/upload.py`<br>`UploadService.approve_batch`<br>&rarr; `sp_rev_approve_upload_batch` | `ifms_budget.rev_upload_batch` | PK: `batch_id`<br>Update: `status='APPROVED'`, `checker_user_id`, `approved_at` | Stored Procedure: `CALL sp_rev_approve_upload_batch(...)`<br>Logs in `audit_change_log` |
| Batch Rejection | PAO Checker Clicks "Reject" | `POST /api/v1/uploads/batches/{id}/reject` | `routers/upload.py`<br>`UploadService.reject_batch` | `ifms_budget.rev_upload_batch` | PK: `batch_id`<br>Update: `status='REJECTED'`, `checker_remarks` | `BEGIN..COMMIT`<br>Logs in `audit_change_log` |
| Batch Deletion | SysAdmin Clicks "Delete" | `DELETE /api/v1/uploads/batches/{id}` | `routers/upload.py`<br>`UploadService.delete_batch` | `ifms_budget.rev_upload_batch`<br>Cascades to staging items | PK: `batch_id` (ON DELETE CASCADE) | `BEGIN..COMMIT`<br>Logs in `audit_change_log` |
| "Load Demo Datasets" Button | Click "Load Demo Dataset" | `POST /api/v1/uploads/seed-demo-dataset` | `routers/upload.py`<br>`UploadService.seed_demo_batches` | `ifms_budget.rev_upload_batch` + Staging tables | Pre-approved demo batches 1, 2, 3 | Full atomic transaction |

---

### 3.4 3-Way Reconciliation Engine (`/recon`)

*Source Reference*: HTML Fragment 13 (`viewRecon`), SOP Section 6 (Rules RR-01 to RR-08)

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Reconciliation Results Table (11 Statuses) | Page Load / Filter by Status, Source, PAO, Date Range | `GET /api/v1/recon/results` | `routers/recon.py`<br>`ReconService.list_results` | `ifms_budget.rev_recon_result`<br>`ifms_budget.rev_recon_run` | PK: `recon_id`<br>FK: `run_id` &rarr; `rev_recon_run` | Read-only |
| "Run Reconciliation" Modal (Filter by Source, Dept, Date Range, Tolerances) | Click "Run Reconciliation" & Confirm | `POST /api/v1/recon/execute` | `routers/recon.py`<br>`ReconEngineService.execute_matching_engine` | `ifms_budget.rev_recon_run`<br>`ifms_budget.rev_recon_result`<br>`ifms_budget.rev_recon_leg_linkage`<br>`ifms_budget.rev_exception`<br>`ifms_budget.rev_penal_claim`<br>`ifms_budget.rev_suspense_register` | Run PK: `run_id`<br>Result PK: `recon_id`<br>Linkage PK: `link_id`<br>Exceptions: `exception_id`<br>Penal: `claim_id` | `BEGIN..COMMIT`<br>Full atomic matching algorithm (RR-01 to RR-08)<br>Triggers: `trg_rev_recon_audit` |
| Reconciliation Detail Modal (3 Legs Evidence, Chronology, Notes) | Click "Open" Row Action | `GET /api/v1/recon/results/{id}` | `routers/recon.py`<br>`ReconService.get_result_detail` | `ifms_budget.rev_recon_result`<br>`ifms_budget.rev_recon_leg_linkage`<br>`ifms_budget.rev_portal_transaction_staging`<br>`ifms_budget.rev_agency_bank_scroll_staging`<br>`ifms_budget.rev_rbi_luggage_staging`<br>`ifms_budget.rev_recon_override` | PK: `recon_id` | Read-only |
| Manual Override Proposal Modal | PAO Maker proposes status change with justification | `POST /api/v1/recon/results/{id}/override/propose` | `routers/recon.py`<br>`ReconService.propose_override` | `ifms_budget.rev_recon_override` | PK: `override_id`<br>FK: `recon_id`, `proposed_by` &rarr; `app_user(user_id)` | `BEGIN..COMMIT`<br>Status: `PENDING_APPROVAL` |
| Manual Override Decision Modal | PAO Checker Approves/Rejects override | `POST /api/v1/recon/results/{id}/override/decision` | `routers/recon.py`<br>`ReconService.decide_override` | `ifms_budget.rev_recon_override`<br>`ifms_budget.rev_recon_result` | PK: `override_id`<br>Update: `status`, `is_manual_override=true`, `checker_user_id` | `BEGIN..COMMIT`<br>Trigger: `trg_rev_recon_audit` |
| Add Timeline Note Modal | Add Audit Note to Recon Result | `POST /api/v1/recon/results/{id}/notes` | `routers/recon.py`<br>`ReconService.add_recon_note` | `ifms_budget.rev_exception_note` | PK: `note_id`<br>FK: `recon_id`, `created_by` | `BEGIN..COMMIT` |

---

### 3.5 Exceptions Management & Resolution (`/exceptions`)

*Source Reference*: HTML Fragment 14 (`viewExceptions`), SOP Section 7

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Exceptions Table (14 Categories, Severity, SLA Ageing) | Page Load / Filter by Category, Severity, Status, Overdue | `GET /api/v1/exceptions` | `routers/exceptions.py`<br>`ExceptionService.list_exceptions` | `ifms_budget.rev_exception`<br>`ifms_budget.rev_recon_result` | PK: `exception_id`<br>FK: `recon_id`, `assigned_user_id` | Read-only |
| Exception Detail & Timeline Modal | Click "Open" Exception | `GET /api/v1/exceptions/{id}` | `routers/exceptions.py`<br>`ExceptionService.get_exception_detail` | `ifms_budget.rev_exception`<br>`ifms_budget.rev_exception_note`<br>`ifms_budget.rev_exception_letter` | PK: `exception_id` | Read-only |
| Resolve Exception Modal | PAO Maker/Checker enters resolution reason & remarks | `POST /api/v1/exceptions/{id}/resolve` | `routers/exceptions.py`<br>`ExceptionService.resolve_exception` | `ifms_budget.rev_exception`<br>`ifms_budget.rev_recon_result` | PK: `exception_id`<br>Update: `status='Resolved'`, `resolved_by`, `resolved_at` | `BEGIN..COMMIT`<br>Logs in `audit_change_log` |
| Issue Follow-up Notice / Letter Modal | Generate formal discrepancy letter | `POST /api/v1/exceptions/{id}/letters` | `routers/exceptions.py`<br>`ExceptionService.create_exception_letter` | `ifms_budget.rev_exception_letter` | PK: `letter_id`<br>FK: `exception_id`, `issued_by` | `BEGIN..COMMIT`<br>Sequence: `fn_rev_next_seq` |
| Bulk Assign Modal | Select exceptions & assign to officer | `POST /api/v1/exceptions/bulk-assign` | `routers/exceptions.py`<br>`ExceptionService.bulk_assign` | `ifms_budget.rev_exception` | PK: `exception_id`<br>Update: `assigned_user_id` | `BEGIN..COMMIT` |
| Escalate Overdue Cases | Click "Escalate Overdue" | `POST /api/v1/exceptions/escalate-overdue` | `routers/exceptions.py`<br>`ExceptionService.escalate_overdue` | `ifms_budget.rev_exception` | PK: `exception_id`<br>Update: `status='Escalated'`, `escalation_count++` | `BEGIN..COMMIT` |

---

### 3.6 Agency Bank SLA & Penal Interest Recovery (`/sla`)

*Source Reference*: HTML Fragment 15 (`viewSLA`), SOP Section 8

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Bank SLA Register & Performance Summary Table | Page Load / Filter by Bank, Mode, Delay Status | `GET /api/v1/sla/claims` | `routers/sla.py`<br>`SLAService.list_claims` | `ifms_budget.rev_penal_claim`<br>`ifms_budget.rev_agency_bank`<br>`ifms_budget.rev_vw_bank_sla_performance` | PK: `claim_id`<br>FK: `bank_id`, `recon_id`, `scroll_item_id` | Read-only |
| SLA Claim Detail Modal | Click "Open" Row Action | `GET /api/v1/sla/claims/{id}` | `routers/sla.py`<br>`SLAService.get_claim_detail` | `ifms_budget.rev_penal_claim`<br>`ifms_budget.rev_penal_letter`<br>`ifms_budget.rev_penal_bank_response`<br>`ifms_budget.rev_penal_waiver` | PK: `claim_id` | Read-only |
| Issue Demand Letter Modal | Treasury Officer issues demand notice to bank | `POST /api/v1/sla/claims/{id}/demand-letter` | `routers/sla.py`<br>`SLAService.issue_demand_letter` | `ifms_budget.rev_penal_letter`<br>`ifms_budget.rev_penal_claim` | Letter PK: `letter_id`<br>FK: `claim_id`, `bank_id`, `issued_by`<br>Update: `claim.status='DEMAND_ISSUED'` | `BEGIN..COMMIT`<br>Sequence: `fn_rev_next_seq` |
| Record Bank Response & Remittance Modal | Bank Ops / PAO records remittance proof / UTR | `POST /api/v1/sla/claims/{id}/bank-response` | `routers/sla.py`<br>`SLAService.record_bank_response` | `ifms_budget.rev_penal_bank_response`<br>`ifms_budget.rev_penal_claim` | Response PK: `response_id`<br>FK: `claim_id`, `recorded_by`<br>Update: `penal_interest_recovered` | `BEGIN..COMMIT`<br>Updates outstanding amount |
| Grant Penalty Waiver Modal | PAO Checker / Finance approves sanction waiver | `POST /api/v1/sla/claims/{id}/waiver` | `routers/sla.py`<br>`SLAService.grant_waiver` | `ifms_budget.rev_penal_waiver`<br>`ifms_budget.rev_penal_claim` | Waiver PK: `waiver_id`<br>FK: `claim_id`, `approved_by`<br>Update: `penal_interest_waived`, `status='WAIVED'` | `BEGIN..COMMIT`<br>Dual-control checker validation |

---

### 3.7 Multi-Stage Refund Management (`/refund`)

*Source Reference*: HTML Fragment 16 (`viewRefund`), SOP Section 9

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Refund Cases Table (10-stage Non-Judicial & 7-stage Judicial) | Page Load / Filter by Type, Status, PAO | `GET /api/v1/refunds` | `routers/refunds.py`<br>`RefundService.list_cases` | `ifms_budget.rev_refund_case` | PK: `refund_id`<br>FK: `recon_id`, `bill_prepared_by`, `pao_approved_by` | Read-only |
| "New Refund Case" Modal (Form-I: Applicant, PAN/ID, Original Challan, Claim Amt, Stamp/Court Ref, Bank Acc, IFSC) | Submit New Refund Application | `POST /api/v1/refunds` | `routers/refunds.py`<br>`RefundService.create_refund_case` | `ifms_budget.rev_refund_case` | PK: `refund_id`<br>Sequence: `fn_rev_next_seq`<br>Status: `'Submitted'` | `BEGIN..COMMIT`<br>Trigger: `trg_rev_refund_audit` |
| Refund Case Stage Progression Modal (SHCIL Verification, Deficiency, Bill Prep, PAO Approval, E-Payment) | Progress Workflow Stage / Save Action | `POST /api/v1/refunds/{id}/stages/{stage}/action` | `routers/refunds.py`<br>`RefundService.advance_refund_stage` | `ifms_budget.rev_refund_case`<br>`ifms_budget.rev_refund_verification`<br>`ifms_budget.rev_refund_bill` | PK: `refund_id`<br>Bill PK: `bill_id`<br>FK: `ddo_id`, `debit_head_id` | `BEGIN..COMMIT`<br>Enforces role permission per stage<br>Trigger: `trg_rev_refund_audit` |
| Import Sample Refund Cases | Click "Import sample refund cases" | `POST /api/v1/refunds/seed-sample-cases` | `routers/refunds.py`<br>`RefundService.seed_samples` | `ifms_budget.rev_refund_case` | Seed 3 standard SOP cases | `BEGIN..COMMIT` |

---

### 3.8 Citizen Refund Tracking (`/citizen-refund`)

*Source Reference*: HTML Fragment 17 (`viewCitizenRefund`), SOP Section 9.7

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Public Tracking Form (Refund Case Number / Challan No + Applicant PAN / Mobile) | Click "Track my refund" | `GET /api/v1/citizen/refund-status?ref={caseNo}&key={pan}` | `routers/citizen.py`<br>`CitizenService.track_refund` | `ifms_budget.rev_refund_case` | PK: `refund_id` (Filtered by `case_no` and masked identity) | Read-only (Public endpoint with rate-limiting) |
| Interactive Stage Tracker Visualizer (10/7 Stage Progress Bar) | View Timeline & Official Remarks | (Rendered from `GET` response) | React Component `CitizenTracker.tsx` | N/A | N/A | Masked bank account & PII |

---

### 3.9 Statutory Revenue Devolution (`/devolution`)

*Source Reference*: HTML Fragment 18 (`viewDevolution`), SOP Section 10

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Devolution Claims & Entitlement Register | Page Load / Filter by Local Body, Source, Status | `GET /api/v1/devolution/claims` | `routers/devolution.py`<br>`DevolutionService.list_claims` | `ifms_budget.rev_devolution_claim`<br>`ifms_budget.rev_local_body`<br>`ifms_budget.rev_devolution_rule` | PK: `claim_id`<br>FK: `local_body_id`, `source_id`, `receipt_head_id`, `dev_rule_id` | Read-only |
| Statutory Sharing Rules Tab | Click "Sharing Rules" Tab | `GET /api/v1/devolution/rules` | `routers/devolution.py`<br>`DevolutionService.list_rules` | `ifms_budget.rev_devolution_rule`<br>`ifms_budget.rev_local_body` | PK: `dev_rule_id`<br>FK: `local_body_id`, `source_id` | Read-only |
| "New Devolution Claim" Modal Form | Local body submits claim for period | `POST /api/v1/devolution/claims` | `routers/devolution.py`<br>`DevolutionService.create_claim` | `ifms_budget.rev_devolution_claim`<br>`ifms_budget.rev_devolution_computation` | PK: `claim_id`<br>Computes eligible collections from `rev_recon_result` (status='Matched') | `BEGIN..COMMIT`<br>Calculates entitlement & variance |
| Scrutiny & Approval Modal | PAO Checker approves devolution bill & statutory advice | `POST /api/v1/devolution/claims/{id}/approve` | `routers/devolution.py`<br>`DevolutionService.approve_claim` | `ifms_budget.rev_devolution_claim`<br>`ifms_budget.rev_devolution_advice` | Advice PK: `advice_id`<br>Update: `claim.status='Approved'`, `advice_no` | `BEGIN..COMMIT`<br>Generates Advice No via `fn_rev_next_seq` |
| Add / Edit Sharing Rule Modal | SysAdmin configures local body % share | `POST /api/v1/devolution/rules`<br>`PUT /api/v1/devolution/rules/{id}` | `routers/devolution.py`<br>`DevolutionService.save_rule` | `ifms_budget.rev_devolution_rule` | PK: `dev_rule_id`<br>FK: `local_body_id`, `source_id`, `receipt_head_id` | `BEGIN..COMMIT`<br>Logs in `audit_change_log` |

---

### 3.10 Revenue Accounting & Voucher Posting (`/accounting`)

*Source Reference*: HTML Fragment 19 (`viewAccounting`), SOP Section 11

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Receipt Vouchers Tab (Draft & Approved Vouchers) | Page Load / Filter by Status, FY, PAO | `GET /api/v1/accounting/vouchers` | `routers/accounting.py`<br>`AccountingService.list_vouchers` | `ifms_budget.rev_receipt_voucher`<br>`ifms_budget.rev_voucher_item`<br>`ifms_budget.chart_of_account` | PK: `voucher_id`<br>FK: `recon_id`, `prepared_by`, `checker_user_id` | Read-only |
| Suspense & RAT Register Tab | Click "Suspense & RAT" Tab | `GET /api/v1/accounting/suspense` | `routers/accounting.py`<br>`AccountingService.list_suspense` | `ifms_budget.rev_suspense_register`<br>`ifms_budget.rev_vw_suspense_and_rat` | PK: `suspense_id`<br>FK: `recon_id`, `suspense_head_id` | Read-only |
| "Create Vouchers for All Ready Receipts" | PAO Maker clicks Bulk Create | `POST /api/v1/accounting/vouchers/create-bulk` | `routers/accounting.py`<br>`AccountingService.bulk_create_vouchers`<br>&rarr; `sp_rev_create_booking_vouchers` | `ifms_budget.rev_receipt_voucher`<br>`ifms_budget.rev_voucher_item`<br>`ifms_budget.rev_recon_result` | Voucher PK: `voucher_id`<br>Item PK: `item_id`<br>FK: `recon_id`, `coa_id` | Stored Procedure: `CALL sp_rev_create_booking_vouchers(...)`<br>Double-entry Debit/Credit rows<br>Trigger: `trg_rev_voucher_audit` |
| "Approve All Draft Vouchers" | PAO Checker clicks Bulk Approve | `POST /api/v1/accounting/vouchers/approve-bulk` | `routers/accounting.py`<br>`AccountingService.bulk_approve_vouchers`<br>&rarr; `sp_rev_approve_booking_vouchers` | `ifms_budget.rev_receipt_voucher`<br>`ifms_budget.rev_recon_result` | Update: `rev_receipt_voucher.status='Approved'`, `rev_recon_result.booking_status='BOOKED'` | Stored Procedure: `CALL sp_rev_approve_booking_vouchers(...)`<br>Trigger: `trg_rev_voucher_audit` |
| Single Voucher PDF / Print Modal | Click "View Voucher" | `GET /api/v1/accounting/vouchers/{id}` | `routers/accounting.py`<br>`AccountingService.get_voucher_detail` | `ifms_budget.rev_receipt_voucher`<br>`ifms_budget.rev_voucher_item` | PK: `voucher_id` | Read-only |

---

### 3.11 Analytical Reports & MIS (`/reports`)

*Source Reference*: HTML Fragment 19 (`viewReports`), SOP Section 12 (17 Reports `r01` to `r17`)

| Report Code | Report Title | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Objects |
| :--- | :--- | :--- | :--- | :--- |
| `r01` | Daily Collection & Mode Distribution Report | `GET /api/v1/reports/r01?from={d}&to={d}&source={s}&dept={d}` | `routers/reports.py`<br>`ReportService.build_r01` | `rev_portal_transaction_staging`, `rev_recon_result` |
| `r02` | Source-wise Tax & Non-Tax Collection Report | `GET /api/v1/reports/r02` | `routers/reports.py`<br>`ReportService.build_r02` | `rev_portal_transaction_staging`, `rev_revenue_source` |
| `r03` | 3-Way Reconciliation Control Summary | `GET /api/v1/reports/r03` | `routers/reports.py`<br>`ReportService.build_r03` | `rev_vw_3way_recon_summary`, `rev_recon_result` |
| `r04` | Transaction-wise Detailed Reconciliation Report | `GET /api/v1/reports/r04` | `routers/reports.py`<br>`ReportService.build_r04` | `rev_recon_result`, `rev_recon_leg_linkage` |
| `r05` | PAO & Department-wise Pending Reconciliation | `GET /api/v1/reports/r05` | `routers/reports.py`<br>`ReportService.build_r05` | `rev_recon_result`, `department`, `app_user` |
| `r06` | Suspense & RAT Unidentified Credits Report | `GET /api/v1/reports/r06` | `routers/reports.py`<br>`ReportService.build_r06` | `rev_vw_suspense_and_rat`, `rev_suspense_register` |
| `r07` | Amount Mismatch & Duplicate Receipt Report | `GET /api/v1/reports/r07` | `routers/reports.py`<br>`ReportService.build_r07` | `rev_recon_result`, `rev_recon_leg_linkage` |
| `r08` | Agency Bank Scroll Receipt & Processing Report | `GET /api/v1/reports/r08` | `routers/reports.py`<br>`ReportService.build_r08` | `rev_agency_bank_scroll_staging`, `rev_agency_bank` |
| `r09` | Bank Remittance SLA & Penal Interest Report | `GET /api/v1/reports/r09` | `routers/reports.py`<br>`ReportService.build_r09` | `rev_penal_claim`, `rev_agency_bank`, `rev_sla_rule` |
| `r10` | Penal Interest Recovery & Waiver Register | `GET /api/v1/reports/r10` | `routers/reports.py`<br>`ReportService.build_r10` | `rev_penal_claim`, `rev_penal_letter`, `rev_penal_waiver` |
| `r11` | Refund Case Register & Ageing Report | `GET /api/v1/reports/r11` | `routers/reports.py`<br>`ReportService.build_r11` | `rev_refund_case`, `department`, `ddo` |
| `r12` | Refund Turnaround Time & Performance MIS | `GET /api/v1/reports/r12` | `routers/reports.py`<br>`ReportService.build_r12` | `rev_refund_case` (Grouped by status & TAT days) |
| `r13` | Statutory Devolution Claims & Settlement Report | `GET /api/v1/reports/r13` | `routers/reports.py`<br>`ReportService.build_r13` | `rev_devolution_claim`, `rev_local_body`, `rev_devolution_advice` |
| `r14` | Head-wise Revenue Collection & Booking Report | `GET /api/v1/reports/r14` | `routers/reports.py`<br>`ReportService.build_r14` | `chart_of_account`, `major_head`, `rev_receipt_voucher` |
| `r15` | Discrepancy & Exception Register Report | `GET /api/v1/reports/r15` | `routers/reports.py`<br>`ReportService.build_r15` | `rev_exception`, `rev_recon_result` |
| `r16` | User Activity & Audit Trail Report | `GET /api/v1/reports/r16` | `routers/reports.py`<br>`ReportService.build_r16` | `ifms_budget.audit_change_log`, `app_user` |
| `r17` | Upload Batch & Data Quality Report | `GET /api/v1/reports/r17` | `routers/reports.py`<br>`ReportService.build_r17` | `rev_upload_batch`, `rev_upload_rejected_row` |
| Export CSV/PDF | Export Active Report | `GET /api/v1/reports/{id}/export?format={csv\|pdf}` | `routers/reports.py`<br>`ReportService.export_report` | Dynamic query generation per report definition |

---

### 3.12 Masters & System Configuration (`/masters`)

*Source Reference*: HTML Fragment 04 & 19 (`viewMasters`), SOP Section 13

| Master Area | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Table | Key Columns & Constraints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Agency Banks | Add / Edit Bank | `GET /api/v1/masters/banks`<br>`POST /api/v1/masters/banks`<br>`PUT /api/v1/masters/banks/{id}` | `routers/masters.py`<br>`MasterService.manage_banks` | `ifms_budget.rev_agency_bank` | PK: `bank_id`, `bank_code` UNIQUE, `bank_name`, `clearing_account_no` |
| Bank Branches | Add / Edit Branch | `GET /api/v1/masters/branches`<br>`POST /api/v1/masters/branches`<br>`PUT /api/v1/masters/branches/{id}` | `routers/masters.py`<br>`MasterService.manage_branches` | `ifms_budget.rev_bank_branch` | PK: `branch_id`, FK: `bank_id`, `branch_code`, `ifsc_code` |
| Revenue Portals | Add / Edit Portal | `GET /api/v1/masters/portals`<br>`POST /api/v1/masters/portals`<br>`PUT /api/v1/masters/portals/{id}` | `routers/masters.py`<br>`MasterService.manage_portals` | `ifms_budget.rev_revenue_portal` | PK: `portal_id`, FK: `department_id`, `portal_code` UNIQUE |
| Revenue Sources | Add / Edit Source | `GET /api/v1/masters/sources`<br>`POST /api/v1/masters/sources`<br>`PUT /api/v1/masters/sources/{id}` | `routers/masters.py`<br>`MasterService.manage_sources` | `ifms_budget.rev_revenue_source` | PK: `source_id`, FK: `department_id`, `portal_id`, `default_receipt_head_id` |
| SLA Rules | Add / Edit SLA Rule | `GET /api/v1/masters/sla-rules`<br>`POST /api/v1/masters/sla-rules`<br>`PUT /api/v1/masters/sla-rules/{id}` | `routers/masters.py`<br>`MasterService.manage_sla_rules` | `ifms_budget.rev_sla_rule` | PK: `sla_rule_id`, `allowed_remittance_days`, `annual_penal_rate_pct` |
| Local Bodies | Add / Edit Local Body | `GET /api/v1/masters/local-bodies`<br>`POST /api/v1/masters/local-bodies`<br>`PUT /api/v1/masters/local-bodies/{id}` | `routers/masters.py`<br>`MasterService.manage_local_bodies` | `ifms_budget.rev_local_body` | PK: `local_body_id`, `local_body_code` UNIQUE, `bank_account_no`, `ifsc_code` |
| System Configuration | Save Tolerances & Heads | `GET /api/v1/config`<br>`PUT /api/v1/config` | `routers/config.py`<br>`ConfigService.update_config` | `ifms_budget.rev_system_config` | PK: `config_id=1`, `demo_business_date`, `current_financial_year`, `amount_tolerance`, `suspense_head_id` |

---

### 3.13 Change Data Capture & Audit Trail (`/audit`)

*Source Reference*: HTML Fragment 19 (`viewAudit`), SOP Section 14

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Audit Trail Table | Page Load / Filter by Module, Action, User, Date Range | `GET /api/v1/audit/logs` | `routers/audit.py`<br>`AuditService.list_logs` | `ifms_budget.audit_change_log`<br>`ifms_budget.app_user` | PK: `audit_id`<br>FK: `changed_by` &rarr; `app_user(user_id)` | Read-only |
| Audit Log Detail Modal | Click Log Entry | `GET /api/v1/audit/logs/{id}` | `routers/audit.py`<br>`AuditService.get_log_detail` | `ifms_budget.audit_change_log` | PK: `audit_id`<br>JSON Diff: `old_data` vs `new_data` | Read-only |

---

### 3.14 Help, Sample File Formats & Automated Test Suite (`/help`)

*Source Reference*: HTML Fragment 19 (`viewHelp`), SOP Section 15

| Field / UI Element | User Action | API Endpoint & Method | Backend Router & Service | PostgreSQL Target Object | Primary / Foreign Keys | Transaction & Audit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Sample File Downloads (6 Sample CSVs) | Click Download Sample File | `GET /api/v1/help/samples/{key}` | `routers/help.py`<br>`HelpService.get_sample_csv` | Server Static Asset / Sample Provider | N/A | Read-only |
| "Run Demo Test Suite" Modal | Click "Run Demo Test Suite" & Confirm | `POST /api/v1/help/test-suite/run` | `routers/help.py`<br>`TestSuiteService.execute_full_suite` | All `rev_*` tables in `ifms_budget` | Atomic Execution of 15 automated test assertions | `BEGIN..COMMIT`<br>Tests Reset, Upload, Approval, Recon, Exceptions, SLA, Vouchers, Refund, Devolution |

---

## 4. Master Schema Cross-Reference & Foreign Key Matrix

The following table summarizes how the Revenue module tables interact with the existing IFMS database without creating duplicate tables:

| Revenue Table | Target Existing Table | Referencing Column | Target Existing Column | Purpose / Business Rule |
| :--- | :--- | :--- | :--- | :--- |
| `rev_revenue_portal` | `ifms_budget.department` | `department_id` | `department_id` | Associates portal (GSTN, ESCIMS, etc.) with parent department. |
| `rev_revenue_source` | `ifms_budget.department` | `department_id` | `department_id` | Associates revenue head with administering department. |
| `rev_revenue_source` | `ifms_budget.chart_of_account` | `default_receipt_head_id` | `coa_id` | Links revenue source to standard 15-digit Chart of Accounts string. |
| `rev_upload_batch` | `ifms_budget.app_user` | `uploaded_by`, `checker_user_id` | `user_id` | Enforces dual-control maker/checker identity and accountability. |
| `rev_recon_run` | `ifms_budget.app_user` | `executed_by` | `user_id` | Logs the specific officer who triggered the matching engine. |
| `rev_recon_override` | `ifms_budget.app_user` | `proposed_by`, `checker_user_id` | `user_id` | Dual-control tracking for manual reconciliation classification changes. |
| `rev_exception` | `ifms_budget.app_user` | `assigned_user_id`, `resolved_by`| `user_id` | Officer ownership for SLA resolution. |
| `rev_receipt_voucher` | `ifms_budget.app_user` | `prepared_by`, `checker_user_id` | `user_id` | Dual-control maker/checker for revenue receipt booking. |
| `rev_voucher_item` | `ifms_budget.chart_of_account` | `coa_id` | `coa_id` | Double-entry line references Debit (Bank Clearing) and Credit (Revenue Head). |
| `rev_refund_bill` | `ifms_budget.department` | `department_id` | `department_id` | Department sanctioning the refund bill. |
| `rev_refund_bill` | `ifms_budget.ddo` | `ddo_id` | `ddo_id` | DDO responsible for drawing the refund bill. |
| `rev_refund_bill` | `ifms_budget.chart_of_account` | `debit_head_id` | `coa_id` | Deduct-Refund 99-Object head. |
| `rev_devolution_advice`| `ifms_budget.chart_of_account` | `debit_head_id` | `coa_id` | 3604 Compensation/Assignment Head. |

---

## 5. Transaction & Concurrency Safety Rules

1. **Explicit Multi-Table Transactions**:
   - Any operation creating or altering related entities (e.g. Reconciliation execution creating Run + Results + Linkages + Exceptions + Penal Claims + Suspense) executes inside a single database transaction block (`BEGIN ... COMMIT`).
   - If any step fails, an automatic `ROLLBACK` is triggered and a structured error is returned to the client.
2. **Deterministic Sequence Numbering**:
   - Sequential document numbers (e.g. `RV-2026-27-000001`, `REF-NJ-2026-000001`, `BAT-PORTAL-000001`) are generated atomically via `fn_rev_next_seq` referencing `ifms_budget.document_number_sequence` with row-level locking (`FOR UPDATE` / `ON CONFLICT DO UPDATE`).
3. **Change-Data-Capture (CDC) Audit Triggers**:
   - Triggers `trg_rev_recon_audit`, `trg_rev_voucher_audit`, and `trg_rev_refund_audit` automatically fire on `INSERT`, `UPDATE`, and `DELETE` on core revenue tables, writing JSON snapshots to `ifms_budget.audit_change_log`.
