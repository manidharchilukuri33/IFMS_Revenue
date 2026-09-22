# IFMS Revenue & Reconciliation — Page-by-Page Database Interlinking & Data Flow Specification

**Database Name**: `ifms_budget` (PostgreSQL)  
**Schema Name**: `ifms_budget`  
**Application Architecture**: React + TypeScript (Frontend) &harr; FastAPI REST Services (Backend) &harr; PostgreSQL (`ifms_budget`)  
**Scope**: Complete mapping of every frontend page, field, form, modal, and button to its destination table(s), column(s), data type(s), interlinked foreign keys, and role-based permissions.

---

## Table of Contents
1. [Master Database Schema Overview & Entity-Relationship Interlinking](#1-master-database-schema-overview--entity-relationship-interlinking)
2. [Global Interlinking Summary Matrix](#2-global-interlinking-summary-matrix)
3. [Page-by-Page Detailed Field & Table Mappings](#3-page-by-page-detailed-field--table-mappings)
   - [3.1 Executive Dashboard (`DashboardPage.tsx`)](#31-executive-dashboard-dashboardpagetsx)
   - [3.2 Revenue Collection Register (`CollectionPage.tsx`)](#32-revenue-collection-register-collectionpagetsx)
   - [3.3 Data Upload Centre (`UploadPage.tsx`)](#33-data-upload-centre-uploadpagetsx)
   - [3.4 Reconciliation Workbench (`ReconPage.tsx`)](#34-reconciliation-workbench-reconpagetsx)
   - [3.5 Exceptions & Investigation (`ExceptionsPage.tsx`)](#35-exceptions--investigation-exceptionspagetsx)
   - [3.6 Bank SLA & Penal Interest (`SlaPenalPage.tsx`)](#36-bank-sla--penal-interest-slapenalpagetsx)
   - [3.7 Refund Management (`RefundsPage.tsx`)](#37-refund-management-refundspagetsx)
   - [3.8 Citizen Status Tracking (`CitizenPage.tsx`)](#38-citizen-status-tracking-citizenpagetsx)
   - [3.9 Revenue Devolution (`DevolutionPage.tsx`)](#39-revenue-devolution-devolutionpagetsx)
   - [3.10 Accounting & Receipt Booking (`AccountingPage.tsx`)](#310-accounting--receipt-booking-accountingpagetsx)
   - [3.11 Analytical Reports & MIS (`ReportsPage.tsx`)](#311-analytical-reports--mis-reportspagetsx)
   - [3.12 Masters & System Configuration (`MastersPage.tsx`)](#312-masters--system-configuration-masterspagetsx)
   - [3.13 Audit Trail (`AuditTrailPage.tsx`)](#313-audit-trail-audittrailpagetsx)
   - [3.14 Help & Test Suite (`HelpTestPage.tsx`)](#314-help--test-suite-helptestpagetsx)
   - [3.15 Global Header, System Notifications & Quick Actions](#315-global-header-system-notifications--quick-actions)
4. [Transaction Safety, Dual Control & Change-Data-Capture (CDC) Rules](#4-transaction-safety-dual-control--change-data-capture-cdc-rules)

---

## 1. Master Database Schema Overview & Entity-Relationship Interlinking

The `ifms_budget` database organizes revenue collection, 3-way matching, accounting, and compliance into **34 distinct database tables** in the `ifms_budget` schema. These tables are strictly partitioned into core operational layers:

```
                                  ┌────────────────────────────────┐
                                  │   GLOBAL / MASTER FOUNDATION   │
                                  │ • department     • app_user    │
                                  │ • ddo            • coa         │
                                  │ • rev_agency_bank• rev_source  │
                                  └───────────────┬────────────────┘
                                                  │ Foreign Keys
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 1. SOURCE STAGING LAYER (DUAL-CONTROL)                           │
│  ┌───────────────────────┐   ┌───────────────────────────────┐   ┌────────────────────────────┐  │
│  │   rev_upload_batch    ├──►│ rev_portal_transaction_staging│   │ rev_agency_bank_scroll_    │  │
│  │ (Batch metadata, file │   │ (Dept / Tax portal receipts)  │   │  staging                   │  │
│  │  size, control totals)│   ├───────────────────────────────┤   │ (Bank scroll lines, UTR)   │  │
│  │                       ├──►│ rev_rbi_luggage_staging       │   └────────────────────────────┘  │
│  └───────────────────────┘   │ (RBI daily settlement credits)│                                   │
│                              └───────────────────────────────┘                                   │
└─────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                  │ Match Keys: CIN, CPIN, Challan, Amount, Date
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 2. 3-WAY RECONCILIATION ENGINE LAYER                             │
│  ┌──────────────────┐         ┌───────────────────────────────┐         ┌─────────────────────┐  │
│  │  rev_recon_run   ├────────►│       rev_recon_result        │◄────────┤ rev_recon_override  │  │
│  │ (Run metadata,   │         │ (Composite matched / mismatch │         │ (Propose & approve  │  │
│  │  summary metrics)│         │  reconciliation records)      │         │  manual overrides)  │  │
│  └──────────────────┘         └───────────────┬───────────────┘         └─────────────────────┘  │
│                                               │                                                  │
│                                ┌──────────────┴──────────────┐                                   │
│                                ▼                             ▼                                   │
│                 ┌─────────────────────────────┐┌──────────────────────────────┐                  │
│                 │   rev_recon_leg_linkage     ││    rev_suspense_register     │                  │
│                 │ (Links result to portal/    ││ (Unreconciled / RAT suspense │                  │
│                 │  bank/rbi staging PKs)      ││  heads & clearance tracking) │                  │
│                 └─────────────────────────────┘└──────────────────────────────┘                  │
└──────────────────────┬────────────────────────┬──────────────────────────────┬───────────────────┘
                       │                        │                              │
        ┌──────────────┘                        │                              └──────────────┐
        ▼                                       ▼                                             ▼
┌────────────────────────┐            ┌────────────────────────┐            ┌────────────────────────┐
│ 3. EXCEPTIONS & SLA    │            │ 4. OUTFLOWS & REFUNDS  │            │ 5. REVENUE ACCOUNTING  │
│ • rev_exception        │            │ • rev_refund_case      │            │ • rev_receipt_voucher  │
│ • rev_exception_note   │            │ • rev_refund_verif     │            │ • rev_voucher_item     │
│ • rev_exception_letter │            │ • rev_refund_bill      │            │ • rev_devolution_claim │
│ • rev_penal_claim      │            │ • rev_local_body       │            │ • rev_devolution_comp  │
│ • rev_penal_letter     │            │ • rev_devolution_rule  │            │ • rev_devolution_advice│
│ • rev_penal_response   │            └────────────────────────┘            └────────────────────────┘
│ • rev_penal_waiver     │
└────────────────────────┘
```

---

## 2. Global Interlinking Summary Matrix

The table below summarizes the total number of interlinked database tables accessed, queried, or updated by each frontend page:

| Page / Route | Primary Target Module | Number of Interlinked Tables | Key Referenced Tables | Primary Write Operations |
| :--- | :--- | :---: | :--- | :--- |
| **Dashboard** (`/dashboard`) | Executive Monitoring | **6** | `rev_recon_run`, `rev_recon_result`, `rev_penal_claim`, `rev_portal_transaction_staging`, `rev_exception`, `rev_system_notifications` | Read-only aggregation & live stats |
| **Revenue Collection** (`/collection`) | Transaction Register | **8** | `rev_portal_transaction_staging`, `rev_upload_batch`, `rev_recon_leg_linkage`, `department`, `app_user`, `chart_of_account`, `audit_change_log`, `rev_system_notifications` | `POST` Manual collection, `POST` Dept validation |
| **Data Upload Centre** (`/upload`) | Dual-Control Staging | **7** | `rev_upload_batch`, `rev_portal_transaction_staging`, `rev_agency_bank_scroll_staging`, `rev_rbi_luggage_staging`, `rev_upload_rejected_row`, `app_user`, `audit_change_log` | `POST` CSV files, `POST` Approve batch, `POST` Reject, `DELETE` Batch |
| **Reconciliation Workbench** (`/recon`) | 3-Way Matching Engine | **10** | `rev_recon_run`, `rev_recon_result`, `rev_recon_leg_linkage`, `rev_recon_override`, `rev_exception`, `rev_penal_claim`, `rev_suspense_register`, `rev_exception_note`, `app_user`, `audit_change_log` | `POST` Execute recon, `POST` Propose override, `POST` Approve override, `POST` Add note |
| **Exceptions & Investigation** (`/exceptions`) | Discrepancy Resolution | **6** | `rev_exception`, `rev_exception_note`, `rev_exception_letter`, `rev_recon_result`, `app_user`, `audit_change_log` | `POST` Resolve, `POST` Issue letter, `POST` Assign, `POST` Escalate |
| **Bank SLA & Penal Interest** (`/sla`) | Statutory Penalties | **7** | `rev_penal_claim`, `rev_penal_letter`, `rev_penal_bank_response`, `rev_penal_waiver`, `rev_agency_bank`, `rev_sla_rule`, `audit_change_log` | `POST` Demand letter, `POST` Bank response, `POST` Waiver |
| **Refund Management** (`/refunds`) | Multi-Stage Refunds | **8** | `rev_refund_case`, `rev_refund_verification`, `rev_refund_bill`, `rev_recon_result`, `department`, `ddo`, `chart_of_account`, `audit_change_log` | `POST` Form-I case, `POST` Verify stamp/court, `POST` Prepare bill, `POST` Approve/Pay |
| **Citizen Status Tracking** (`/citizen`) | Public Tracker | **2** | `rev_refund_case`, `rev_refund_verification` | `GET` (Read-only public query) |
| **Revenue Devolution** (`/devolution`) | Local Body Settlement | **8** | `rev_devolution_claim`, `rev_devolution_computation`, `rev_devolution_advice`, `rev_devolution_rule`, `rev_local_body`, `rev_revenue_source`, `chart_of_account`, `audit_change_log` | `POST` Claim, `POST` Approve & advice, `POST`/`PUT` Sharing rule |
| **Accounting & Receipt Booking** (`/accounting`) | Double-Entry Posting | **7** | `rev_receipt_voucher`, `rev_voucher_item`, `rev_recon_result`, `rev_suspense_register`, `chart_of_account`, `app_user`, `audit_change_log` | `POST` Create draft vouchers, `POST` Approve & post vouchers, `POST` Clear suspense |
| **Reports & MIS** (`/reports`) | Analytical MIS | **14** | All `rev_*` operational tables + master tables | Read-only dynamic SQL reports & exports |
| **Masters & Configuration** (`/masters`) | System Config & Admin | **10** | `rev_agency_bank`, `rev_bank_branch`, `rev_revenue_portal`, `rev_revenue_source`, `rev_sla_rule`, `rev_local_body`, `rev_devolution_rule`, `rev_system_config`, `chart_of_account`, `audit_change_log` | `POST`/`PUT` Master CRUD across all 8 subtabs |
| **Audit Trail** (`/audit`) | Governance & CDC | **2** | `audit_change_log`, `app_user` | Read-only immutable audit querying |
| **Help & Test Suite** (`/help`) | Self-Test & Samples | **34** | All tables in `ifms_budget` schema | `POST` Reset demo dataset, `POST` Execute 15 automated test assertions |
| **Global Controls & Notifications** | System Wide | **3** | `rev_system_notifications`, `rev_system_config`, `audit_change_log` | `POST` Mark notifications read, `PUT` FY/Date, `POST` Role change log |

---

## 3. Page-by-Page Detailed Field & Table Mappings

---

### 3.1 Executive Dashboard (`DashboardPage.tsx`)
**Route**: `/dashboard`  
**Required Capability**: `nav.dashboard`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `BANK_OPS`, `AUDITOR` (Restricted for `CITIZEN`)  
**Total Interlinked Tables**: **6**

#### Interlinked Tables
1. `ifms_budget.rev_recon_run` (Reconciliation run header & summary totals)
2. `ifms_budget.rev_recon_result` (Transaction matching status counts: Matched, Suspend, RAT, Mismatch, Duplicate)
3. `ifms_budget.rev_penal_claim` (Penal interest computed, recovered, and outstanding)
4. `ifms_budget.rev_portal_transaction_staging` (Total gross collection amounts and department breakdown)
5. `ifms_budget.rev_exception` (Open, high severity, overdue exception counts)
6. `ifms_budget.rev_system_notifications` (Real-time operational alerts for header bell)

#### Frontend Input Fields & User Actions &rarr; Target Database Mapping

| Frontend Field / Action | Trigger Element | HTTP Request | Target Database Table | Target Database Column(s) & Type | Foreign Key / Join References |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Financial Year Selector** | Top Header `<select>` | `GET /api/v1/dashboard/kpis?fy={val}` | `rev_recon_run`<br>`rev_recon_result` | Filter: `rev_recon_run.business_date` (Date) | N/A (Aggregated Query) |
| **Business Date Filter** | Header Date Chip | `GET /api/v1/dashboard/kpis?date={val}` | `rev_recon_run` | Filter: `rev_recon_run.business_date` | N/A (Aggregated Query) |
| **Quick Action: "Run 3-Way Reconciliation"** | Dashboard Button | `POST /api/v1/recon/execute` | `rev_recon_run`<br>`rev_recon_result` | `rev_recon_run.run_no` (VARCHAR)<br>`rev_recon_run.total_processed` (INT)<br>`rev_recon_run.executed_by` (BIGINT) | FK &rarr; `app_user(user_id)` |
| **Quick Action: "Reset Demo Data"** | Dashboard Button | `POST /api/v1/config/reset-demo` | All `rev_*` tables | Truncates and resets demo records | Full atomic transaction |
| **Quick Action: "Run Test Suite"** | Dashboard Button | `POST /api/v1/help/test-suite/run` | All `rev_*` tables | `rev_recon_run`, `rev_upload_batch`, etc. | Full atomic transaction |

---

### 3.2 Revenue Collection Register (`CollectionPage.tsx`)
**Route**: `/collection`  
**Required Capability**: `nav.collection`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `BANK_OPS`, `AUDITOR`  
**Total Interlinked Tables**: **8**

#### Interlinked Tables
1. `ifms_budget.rev_portal_transaction_staging` (Primary transaction table)
2. `ifms_budget.rev_upload_batch` (Parent batch for transactions)
3. `ifms_budget.rev_recon_leg_linkage` (Links portal item to reconciliation result)
4. `ifms_budget.rev_recon_result` (Reconciliation status and matched bank/rbi references)
5. `ifms_budget.department` (Administering state government department)
6. `ifms_budget.chart_of_account` (15-digit Major/Minor/Object head of account)
7. `ifms_budget.app_user` (Validation officer user identity)
8. `ifms_budget.audit_change_log` (CDC audit trail of new records / status updates)

#### Form: "Add Manual Collection" Modal Form &rarr; Database Target Mapping

When a user with `PAO_MAKER`, `TRE_ADMIN`, or `SYSADMIN` role opens the **Manual Collection** modal and clicks **Post Manual Collection Record**, the following fields are submitted and stored:

| Frontend Modal Field | Form Input Name | Data Type | Target Table in `ifms_budget` | Destination Column Name | Column Constraints & Default | Interlinked Foreign Key Table & Column |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Revenue Portal** | `portal_name` | Dropdown | `rev_portal_transaction_staging` | `portal_name` | `VARCHAR(50) NOT NULL` | Links logically to `rev_revenue_portal.portal_code` |
| **Revenue Source** | `revenue_source` | Dropdown | `rev_portal_transaction_staging` | `revenue_source` | `VARCHAR(30) NOT NULL` | Links logically to `rev_revenue_source.source_code` |
| **Department Code** | `dept_code` | Text | `rev_portal_transaction_staging` | `dept_code` | `VARCHAR(30) NOT NULL` | Links logically to `department.department_code` |
| **PAO Code** | `pao_code` | Dropdown | `rev_portal_transaction_staging` | `pao_code` | `VARCHAR(30) NOT NULL` | Treasury PAO Code |
| **DDO Code** | `ddo_code` | Dropdown | `rev_portal_transaction_staging` | `ddo_code` | `VARCHAR(30) NOT NULL` | Links logically to `ddo.ddo_code` |
| **Portal Txn ID** | `portal_transaction_id` | Text | `rev_portal_transaction_staging` | `portal_transaction_id` | `VARCHAR(100) NOT NULL` | Generated / Input Unique Reference |
| **Challan Number** | `challan_no` | Text | `rev_portal_transaction_staging` | `challan_no` | `VARCHAR(100) NOT NULL` | Primary matching key for 3-way recon |
| **CPIN** | `cpin` | Text | `rev_portal_transaction_staging` | `cpin` | `VARCHAR(100) NULL` | GST / Commercial Tax CPIN |
| **CIN** | `cin` | Text | `rev_portal_transaction_staging` | `cin` | `VARCHAR(100) NULL` | Challan Identification Number |
| **Payer ID** | `payer_id` | Text | `rev_portal_transaction_staging` | `payer_id` | `VARCHAR(100) NULL` | GSTIN / PAN / Registration No |
| **Payer Name** | `payer_name` | Text | `rev_portal_transaction_staging` | `payer_name` | `VARCHAR(250) NOT NULL` | Legal entity or citizen name |
| **Payment Date** | `payment_date` | Date Picker | `rev_portal_transaction_staging` | `payment_date` | `DATE NOT NULL` | Base date for SLA computation |
| **Service Date** | `service_date` | Date Picker | `rev_portal_transaction_staging` | `service_date` | `DATE NOT NULL` | Date service was rendered |
| **Payment Mode** | `payment_mode` | Dropdown | `rev_portal_transaction_staging` | `payment_mode` | `VARCHAR(30) NOT NULL` | `NETBANKING`, `UPI`, `CARD`, `CASH`, `CHEQUE` |
| **Amount (₹)** | `amount` | Numeric | `rev_portal_transaction_staging` | `amount` | `NUMERIC(15, 2) NOT NULL` | Main transaction gross value |
| **Receipt Head** | `receipt_head` | Text | `rev_portal_transaction_staging` | `receipt_head` | `VARCHAR(100) NOT NULL` | 15-digit Chart of Accounts string |
| **Service Description** | `service_description` | Textarea | `rev_portal_transaction_staging` | `service_description` | `TEXT NULL` | Purpose narration |
| **Penalty Amount** | `penalty_amount` | Numeric | `rev_portal_transaction_staging` | `penalty_amount` | `NUMERIC(15, 2) DEFAULT 0.00` | Statutory fine / late fee component |
| **Automatic System Fields** | `batch_id` | Auto | `rev_portal_transaction_staging` | `batch_id` | `BIGINT NOT NULL` | FK &rarr; `rev_upload_batch.batch_id` (`batch_type='MANUAL_ENTRY'`) |
| **Automatic System Fields** | `portal_status` | Auto | `rev_portal_transaction_staging` | `portal_status` | `VARCHAR(30) DEFAULT 'PAID'` | Initial status |
| **Automatic System Fields** | `created_at` | Auto | `rev_portal_transaction_staging` | `created_at` | `TIMESTAMPTZ DEFAULT clock_timestamp()` | Audit timestamp |

#### Action: "Departmental Validation" &rarr; Database Target Mapping

When a `DDO`, `PAO_MAKER`, or `TRE_ADMIN` selects one or more transactions and clicks **Validate Departmental Record(s)**:
- **API Endpoint**: `POST /api/v1/collection/validate-departmental`
- **Payload**: `{ "transaction_ids": [101, 102] }`
- **Target Table**: `ifms_budget.rev_portal_transaction_staging`
- **Updated Columns**:
  - `dept_validated` = `TRUE` (`BOOLEAN`)
  - `dept_validated_by` = Current User ID (`BIGINT`, FK &rarr; `app_user.user_id`)
  - `dept_validated_at` = `clock_timestamp()` (`TIMESTAMPTZ`)
- **Audit Trigger**: Writes CDC log entry to `ifms_budget.audit_change_log` with operation `'U'`.

---

### 3.3 Data Upload Centre (`UploadPage.tsx`)
**Route**: `/upload`  
**Required Capability**: `nav.upload`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `BANK_OPS`, `AUDITOR`  
**Total Interlinked Tables**: **7**

#### Interlinked Tables
1. `ifms_budget.rev_upload_batch` (Batch master register)
2. `ifms_budget.rev_portal_transaction_staging` (Staging for Portal files)
3. `ifms_budget.rev_agency_bank_scroll_staging` (Staging for Bank Scroll files)
4. `ifms_budget.rev_rbi_luggage_staging` (Staging for RBI Settlement files)
5. `ifms_budget.rev_upload_rejected_row` (Invalid / corrupt CSV rows held for audit)
6. `ifms_budget.app_user` (Uploaded by & Approved by user records)
7. `ifms_budget.audit_change_log` (Batch state changes and approvals)

#### File Upload & Actions &rarr; Target Database Mapping

| User Action / UI Field | Trigger Element | HTTP Request | Target Table in `ifms_budget` | Destination Columns & Data Types | Interlinked Foreign Key Table & Column |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Portal CSV File Upload** | Dropzone / File Picker | `POST /api/v1/uploads/process` | `rev_upload_batch`<br>`rev_portal_transaction_staging`<br>`rev_upload_rejected_row` | `batch_no` (VARCHAR)<br>`batch_type='PORTAL'`<br>`source_filename` (VARCHAR)<br>`file_size_bytes` (BIGINT)<br>`total_records`, `valid_records`, `invalid_records`<br>`control_total` (NUMERIC)<br>`status='PENDING_APPROVAL'`<br>`uploaded_by` (BIGINT) | `uploaded_by` &rarr; `app_user.user_id`<br>`batch_id` &rarr; `rev_portal_transaction_staging.batch_id` (CASCADE) |
| **Bank Scroll CSV Upload** | Dropzone / File Picker | `POST /api/v1/uploads/process` | `rev_upload_batch`<br>`rev_agency_bank_scroll_staging` | `batch_no` (VARCHAR)<br>`batch_type='BANK_SCROLL'`<br>`scroll_no`, `bank_code`, `branch_code`<br>`challan_no`, `bank_reference_no`, `utr_no`<br>`payment_received_date`, `bank_remittance_date`<br>`amount`, `receipt_head` | `uploaded_by` &rarr; `app_user.user_id`<br>`bank_id` &rarr; `rev_agency_bank.bank_id` |
| **RBI Luggage CSV Upload** | Dropzone / File Picker | `POST /api/v1/uploads/process` | `rev_upload_batch`<br>`rev_rbi_luggage_staging` | `batch_no` (VARCHAR)<br>`batch_type='RBI_LUGGAGE'`<br>`settlement_date`, `rbi_reference_no`<br>`agency_bank_code`, `challan_no`, `amount` | `uploaded_by` &rarr; `app_user.user_id`<br>`batch_id` &rarr; `rev_rbi_luggage_staging.batch_id` |
| **Approve Upload Batch** | PAO Checker clicks "Approve" | `POST /api/v1/uploads/batches/{id}/approve` | `rev_upload_batch` | `status='APPROVED'`<br>`checker_user_id` = Active User<br>`approved_at` = `clock_timestamp()` | `checker_user_id` &rarr; `app_user.user_id`<br>Enables records for 3-way reconciliation |
| **Reject Upload Batch** | PAO Checker clicks "Reject" | `POST /api/v1/uploads/batches/{id}/reject` | `rev_upload_batch` | `status='REJECTED'`<br>`checker_remarks` (TEXT)<br>`checker_user_id` = Active User | `checker_user_id` &rarr; `app_user.user_id`<br>Excludes records from recon |
| **Delete Batch** | SysAdmin clicks "Delete" | `DELETE /api/v1/uploads/batches/{id}` | `rev_upload_batch` | Cascades deletion to staging items | `ON DELETE CASCADE` removes child staging rows |

---

### 3.4 Reconciliation Workbench (`ReconPage.tsx`)
**Route**: `/recon`  
**Required Capability**: `nav.recon`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `AUDITOR`  
**Total Interlinked Tables**: **10**

#### Interlinked Tables
1. `ifms_budget.rev_recon_run` (Reconciliation run execution metadata)
2. `ifms_budget.rev_recon_result` (Composite reconciliation status: Matched, Suspend, RAT, Mismatch, Duplicate)
3. `ifms_budget.rev_recon_leg_linkage` (Foreign key pointers to portal, bank scroll, and RBI luggage items)
4. `ifms_budget.rev_recon_override` (Dual-control manual override proposals and decisions)
5. `ifms_budget.rev_exception` (Auto-raised exceptions for non-matched results)
6. `ifms_budget.rev_penal_claim` (Auto-calculated penal interest claims for delayed bank remittances)
7. `ifms_budget.rev_suspense_register` (Unidentified receipts & suspense entries)
8. `ifms_budget.rev_exception_note` (Chronology audit notes)
9. `ifms_budget.app_user` (Execution officer, proposer, checker identities)
10. `ifms_budget.audit_change_log` (Automated CDC audit records)

#### Actions & Forms &rarr; Database Target Mapping

| User Action / UI Form | Trigger Element | HTTP Request | Target Table in `ifms_budget` | Destination Columns & Data Types | Interlinked Foreign Key Table & Column |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Execute 3-Way Reconciliation Engine** | "Run Reconciliation" Modal Form (Scope: Date Range, Revenue Source, Dept, Tolerances) | `POST /api/v1/recon/execute` | `rev_recon_run`<br>`rev_recon_result`<br>`rev_recon_leg_linkage`<br>`rev_exception`<br>`rev_penal_claim`<br>`rev_suspense_register` | `run_no` (VARCHAR)<br>`business_date` (DATE)<br>`scope_filters` (JSONB)<br>`matched_count`, `suspend_count`, `rat_count`, `mismatch_count`, `duplicate_count`<br>`executed_by` (BIGINT)<br>`rev_recon_result.rev_transaction_id`<br>`rev_recon_result.status`<br>`rev_recon_result.portal_total`<br>`rev_recon_result.bank_total`<br>`rev_recon_result.rbi_total`<br>`rev_recon_result.amount_difference` | `executed_by` &rarr; `app_user.user_id`<br>`run_id` &rarr; `rev_recon_run.run_id`<br>`linkage.portal_item_id` &rarr; `rev_portal_transaction_staging`<br>`linkage.scroll_item_id` &rarr; `rev_agency_bank_scroll_staging`<br>`linkage.rbi_item_id` &rarr; `rev_rbi_luggage_staging`<br>`exception.recon_id` &rarr; `rev_recon_result.recon_id`<br>`claim.recon_id` &rarr; `rev_recon_result.recon_id` |
| **Propose Manual Override** | "Propose Status Change" Modal (Proposed status, Justification text) | `POST /api/v1/recon/results/{id}/override/propose` | `rev_recon_override` | `override_id` (BIGINT PK)<br>`recon_id` (BIGINT)<br>`original_machine_status` (VARCHAR)<br>`proposed_status` (VARCHAR)<br>`proposer_justification` (TEXT)<br>`proposed_by` (BIGINT)<br>`decision_status='PENDING_APPROVAL'` | `recon_id` &rarr; `rev_recon_result.recon_id`<br>`proposed_by` &rarr; `app_user.user_id` |
| **Decide Manual Override** | "Approve / Reject Override" Modal (PAO Checker) | `POST /api/v1/recon/results/{id}/override/decision` | `rev_recon_override`<br>`rev_recon_result` | `rev_recon_override.decision_status` ('APPROVED'/'REJECTED')<br>`rev_recon_override.checker_user_id`<br>`rev_recon_result.status` = proposed_status<br>`rev_recon_result.is_manual_override` = TRUE | `checker_user_id` &rarr; `app_user.user_id`<br>Updates status in `rev_recon_result` |
| **Add Chronology / Audit Note** | "Add Note" Modal (Note text, Action category) | `POST /api/v1/recon/results/{id}/notes` | `rev_exception_note` | `note_id` (BIGINT PK)<br>`exception_id` / `recon_id` (BIGINT)<br>`action_type` (VARCHAR)<br>`note_text` (TEXT)<br>`created_by` (BIGINT) | `created_by` &rarr; `app_user.user_id` |

---

### 3.5 Exceptions & Investigation (`ExceptionsPage.tsx`)
**Route**: `/exceptions`  
**Required Capability**: `nav.exceptions`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `BANK_OPS`, `AUDITOR`  
**Total Interlinked Tables**: **6**

#### Interlinked Tables
1. `ifms_budget.rev_exception` (Exception record header)
2. `ifms_budget.rev_exception_note` (Investigation comments & activity history)
3. `ifms_budget.rev_exception_letter` (Discrepancy notice letters)
4. `ifms_budget.rev_recon_result` (Underlying reconciliation transaction)
5. `ifms_budget.app_user` (Assigned officer, resolving officer)
6. `ifms_budget.audit_change_log` (CDC audit tracking)

#### Actions & Forms &rarr; Database Target Mapping

| User Action / UI Form | Trigger Element | HTTP Request | Target Table in `ifms_budget` | Destination Columns & Data Types | Interlinked Foreign Key Table & Column |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Resolve Exception** | "Resolve Exception" Modal (Resolution Reason, Remarks) | `POST /api/v1/exceptions/{id}/resolve` | `rev_exception`<br>`rev_recon_result` | `status='Resolved'`<br>`resolution_reason` (VARCHAR(150))<br>`resolution_remarks` (TEXT)<br>`resolved_by` (BIGINT)<br>`resolved_at` = `clock_timestamp()` | `resolved_by` &rarr; `app_user.user_id`<br>`recon_id` &rarr; `rev_recon_result.recon_id` |
| **Issue Follow-up Notice / Letter** | "Draft Discrepancy Letter" Modal (Subject, Recipient, Body text) | `POST /api/v1/exceptions/{id}/letters` | `rev_exception_letter` | `letter_no` (VARCHAR, via `fn_rev_next_seq`)<br>`exception_id` (BIGINT)<br>`recipient_type` (VARCHAR)<br>`recipient_name` (VARCHAR)<br>`recipient_address` (TEXT)<br>`letter_subject` (VARCHAR)<br>`letter_body` (TEXT)<br>`issued_date` (DATE)<br>`issued_by` (BIGINT)<br>`status='ISSUED'` | `exception_id` &rarr; `rev_exception.exception_id`<br>`issued_by` &rarr; `app_user.user_id` |
| **Bulk Assign Exceptions** | "Bulk Assign" Dialog (Select Officer) | `POST /api/v1/exceptions/bulk-assign` | `rev_exception` | `assigned_user_id` (BIGINT)<br>`status='Assigned'`<br>`updated_at` = `clock_timestamp()` | `assigned_user_id` &rarr; `app_user.user_id` |
| **Escalate Overdue Exceptions** | "Escalate Overdue" Button | `POST /api/v1/exceptions/escalate-overdue` | `rev_exception` | `status='Escalated'`<br>`escalation_count` = `escalation_count + 1`<br>`last_escalated_at` = `clock_timestamp()` | Updates all open exceptions where `due_date < current_date` |

---

### 3.6 Bank SLA & Penal Interest (`SlaPenalPage.tsx`)
**Route**: `/sla`  
**Required Capability**: `nav.sla`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `FINANCE`, `BANK_OPS`, `AUDITOR`  
**Total Interlinked Tables**: **7**

#### Interlinked Tables
1. `ifms_budget.rev_penal_claim` (Penal claim calculation master)
2. `ifms_budget.rev_penal_letter` (Statutory demand notice letters)
3. `ifms_budget.rev_penal_bank_response` (Bank reply, UTR, and remittance records)
4. `ifms_budget.rev_penal_waiver` (Sanctioned penalty waiver orders)
5. `ifms_budget.rev_agency_bank` (Agency bank entity master)
6. `ifms_budget.rev_sla_rule` (Permitted days & annual penal interest rate %)
7. `ifms_budget.audit_change_log` (CDC audit trail)

#### Actions & Forms &rarr; Database Target Mapping

| User Action / UI Form | Trigger Element | HTTP Request | Target Table in `ifms_budget` | Destination Columns & Data Types | Interlinked Foreign Key Table & Column |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Issue Statutory Demand Letter** | "Draft Demand Letter" Modal (Subject, Demand Amount, Content) | `POST /api/v1/sla/claims/{id}/demand-letter` | `rev_penal_letter`<br>`rev_penal_claim` | `letter_no` (VARCHAR, via `fn_rev_next_seq`)<br>`claim_id` (BIGINT)<br>`bank_id` (BIGINT)<br>`total_demand_amount` (NUMERIC)<br>`letter_content` (TEXT)<br>`issued_by` (BIGINT)<br>`claim.status='DEMAND_ISSUED'` | `claim_id` &rarr; `rev_penal_claim.claim_id`<br>`bank_id` &rarr; `rev_agency_bank.bank_id`<br>`issued_by` &rarr; `app_user.user_id` |
| **Record Bank Response & Remittance** | "Log Bank Remittance" Modal (Response type, Remitted amount, UTR, Remarks) | `POST /api/v1/sla/claims/{id}/bank-response` | `rev_penal_bank_response`<br>`rev_penal_claim` | `response_id` (BIGINT PK)<br>`claim_id` (BIGINT)<br>`response_date` (DATE)<br>`response_type` (VARCHAR)<br>`remitted_amount` (NUMERIC)<br>`bank_remarks` (TEXT)<br>`recorded_by` (BIGINT)<br>`claim.penal_interest_recovered` += remitted_amount<br>`claim.penal_interest_outstanding` -= remitted_amount | `claim_id` &rarr; `rev_penal_claim.claim_id`<br>`recorded_by` &rarr; `app_user.user_id` |
| **Grant Statutory Penalty Waiver** | "Grant Waiver" Modal (Waived Amount, Ground, Sanction Order Ref, Remarks) | `POST /api/v1/sla/claims/{id}/waiver` | `rev_penal_waiver`<br>`rev_penal_claim` | `waiver_id` (BIGINT PK)<br>`claim_id` (BIGINT)<br>`waived_amount` (NUMERIC)<br>`waiver_ground` (VARCHAR(200))<br>`sanction_order_ref` (VARCHAR(100))<br>`waiver_remarks` (TEXT)<br>`approved_by` (BIGINT)<br>`approved_at` = `clock_timestamp()`<br>`claim.penal_interest_waived` += waived_amount<br>`claim.status='WAIVED'` | `claim_id` &rarr; `rev_penal_claim.claim_id`<br>`approved_by` &rarr; `app_user.user_id` |

---

### 3.7 Refund Management (`RefundsPage.tsx`)
**Route**: `/refunds` (or `/refund`)  
**Required Capability**: `nav.refund`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `AUDITOR`, `CITIZEN`  
**Total Interlinked Tables**: **8**

#### Interlinked Tables
1. `ifms_budget.rev_refund_case` (Refund case workflow master)
2. `ifms_budget.rev_refund_verification` (SHCIL stamp / Court order verification history)
3. `ifms_budget.rev_refund_bill` (DDO Prepared refund voucher / bill)
4. `ifms_budget.rev_recon_result` (Original reconciled receipt verification)
5. `ifms_budget.department` (Sanctioning administrative department)
6. `ifms_budget.ddo` (Drawing & Disbursing Officer preparing bill)
7. `ifms_budget.chart_of_account` (Deduct-Refund 99-Object expenditure head)
8. `ifms_budget.audit_change_log` (CDC workflow audit trail)

#### Form: "Create Refund Case (Form-I)" Modal &rarr; Database Target Mapping

| Frontend Form Field | Form Field Name | Input Type | Target Table in `ifms_budget` | Destination Column Name | Column Data Type & Constraint | Interlinked Table & Foreign Key |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Refund Type** | `refund_type` | Dropdown | `rev_refund_case` | `refund_type` | `VARCHAR(50) NOT NULL` (`NON_JUDICIAL_STAMP` or `JUDICIAL_STAMP`) | Dictates 10-stage vs 7-stage workflow |
| **Applicant Full Name** | `applicant_name` | Text | `rev_refund_case` | `applicant_name` | `VARCHAR(250) NOT NULL` | Taxpayer legal name |
| **Identity Proof / PAN** | `applicant_id_proof` | Text | `rev_refund_case` | `applicant_id_proof` | `VARCHAR(100) NULL` | PAN / Aadhaar / Reg ID |
| **Bank Account Number** | `applicant_bank_acc` | Text | `rev_refund_case` | `applicant_bank_acc` | `VARCHAR(50) NULL` | Mandate payment credit account |
| **Bank IFSC Code** | `applicant_ifsc` | Text | `rev_refund_case` | `applicant_ifsc` | `VARCHAR(20) NULL` | Bank IFSC routing |
| **Original Challan Number**| `original_challan_no`| Text | `rev_refund_case` | `original_challan_no` | `VARCHAR(100) NOT NULL` | Verified against `rev_recon_result` |
| **Reconciled Original Amount**| `reconciled_original_amount`| Numeric | `rev_refund_case` | `reconciled_original_amount` | `NUMERIC(15, 2) NOT NULL` | Maximum refund cap guard |
| **Claim Amount (₹)** | `claimed_amount` | Numeric | `rev_refund_case` | `claimed_amount` | `NUMERIC(15, 2) NOT NULL` | Amount claimed by applicant |
| **Refundable Amount (₹)** | `refundable_amount` | Numeric | `rev_refund_case` | `refundable_amount` | `NUMERIC(15, 2) NOT NULL` | Entitled amount post-scrutiny |
| **E-Stamp Certificate No**| `e_stamp_cert_no` | Text | `rev_refund_case` | `e_stamp_cert_no` | `VARCHAR(100) NULL` | SHCIL e-stamp certificate |
| **Court Order Number** | `court_order_no` | Text | `rev_refund_case` | `court_order_no` | `VARCHAR(100) NULL` | Judicial refund decree order |
| **Case Number (Auto)** | `case_no` | Auto | `rev_refund_case` | `case_no` | `VARCHAR(50) UNIQUE NOT NULL` | Generated via `fn_rev_next_seq` |
| **Current Stage (Auto)** | `current_stage` | Auto | `rev_refund_case` | `current_stage` | `INT DEFAULT 1` | Initial stage: `1` |
| **Status (Auto)** | `status` | Auto | `rev_refund_case` | `status` | `VARCHAR(30) DEFAULT 'Submitted'`| Initial workflow state |

#### Multi-Stage Actions &rarr; Database Target Mapping

1. **Stamp / Court Order Verification** (Divisional Officer / Scrutiny):
   - **Table**: `ifms_budget.rev_refund_verification`
   - **Columns**: `verification_type` (SHCIL/COURT), `verification_result` ('Valid'/'Invalid'), `authority_name`, `verification_remarks`, `verified_by` (FK &rarr; `app_user`), `verified_at`.
2. **Refund Bill Preparation** (`DDO`):
   - **Table**: `ifms_budget.rev_refund_bill`
   - **Columns**: `bill_no` (via `fn_rev_next_seq`), `department_id` (FK &rarr; `department`), `ddo_id` (FK &rarr; `ddo`), `pao_code`, `bill_amount` (NUMERIC), `debit_head_id` (FK &rarr; `chart_of_account`), `prepared_by` (FK &rarr; `app_user`).
3. **PAO Checker Approval & E-Payment** (`PAO_CHECK`):
   - **Table**: `ifms_budget.rev_refund_case` & `rev_refund_bill`
   - **Columns**: `pao_approved_by` (FK &rarr; `app_user`), `pao_approved_at`, `pao_remarks`, `epay_ref_no`, `epay_instructed_at`, `paid_at`, `status='PAID'`.

---

### 3.8 Citizen Status Tracking (`CitizenPage.tsx`)
**Route**: `/citizen`  
**Required Capability**: `nav.help` / Public  
**Allowed Roles**: All roles including `CITIZEN`  
**Total Interlinked Tables**: **2**

#### Interlinked Tables
1. `ifms_budget.rev_refund_case` (Refund application status lookup)
2. `ifms_budget.rev_refund_verification` (Public stage verification remarks)

#### Frontend Input Fields &rarr; Target Database Mapping

| Frontend Input Field | UI Form | HTTP Request | Target Database Table | Lookup Column | Returned Data |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Refund Case Number** | Search Form Input (`caseNo`) | `GET /api/v1/citizen/refund-status?case_no={val}` | `rev_refund_case` | `case_no` / `applicant_id_proof` | `case_no`, `applicant_name`, `refund_type`, `claimed_amount`, `current_stage`, `stage_name`, `status`, `paid_at` |

---

### 3.9 Revenue Devolution (`DevolutionPage.tsx`)
**Route**: `/devolution`  
**Required Capability**: `nav.devolution`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `AUDITOR`  
**Total Interlinked Tables**: **8**

#### Interlinked Tables
1. `ifms_budget.rev_devolution_claim` (Statutory devolution claim master)
2. `ifms_budget.rev_devolution_computation` (Reconciliation item-level entitlement breakdown)
3. `ifms_budget.rev_devolution_advice` (Treasury payment advice order)
4. `ifms_budget.rev_devolution_rule` (Statutory sharing percentage rule)
5. `ifms_budget.rev_local_body` (PRIs / ULBs master)
6. `ifms_budget.rev_revenue_source` (Assigned revenue source)
7. `ifms_budget.chart_of_account` (3604 Compensation/Assignment Head)
8. `ifms_budget.audit_change_log` (CDC audit trail)

#### Form: "New Devolution Claim" Modal &rarr; Target Database Mapping

| Frontend Form Field | Input Name | Type | Target Table in `ifms_budget` | Destination Column Name | Constraints & Foreign Key |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Local Body** | `local_body_id` | Dropdown | `rev_devolution_claim` | `local_body_id` | `BIGINT NOT NULL`, FK &rarr; `rev_local_body.local_body_id` |
| **Revenue Source** | `source_id` | Dropdown | `rev_devolution_claim` | `source_id` | `BIGINT NOT NULL`, FK &rarr; `rev_revenue_source.source_id` |
| **Receipt Head** | `receipt_head_id` | Dropdown | `rev_devolution_claim` | `receipt_head_id` | `BIGINT NOT NULL`, FK &rarr; `chart_of_account.coa_id` |
| **Period From** | `period_from` | Date | `rev_devolution_claim` | `period_from` | `DATE NOT NULL` |
| **Period To** | `period_to` | Date | `rev_devolution_claim` | `period_to` | `DATE NOT NULL` |
| **Claimed Amount (₹)** | `claimed_amount` | Numeric | `rev_devolution_claim` | `claimed_amount` | `NUMERIC(15, 2) NOT NULL` |
| **System Computed (Auto)**| `computed_entitlement` | Auto | `rev_devolution_claim` | `computed_entitlement` | Computed strictly from `rev_recon_result` (status='Matched') |
| **Variance Amount (Auto)**| `variance_amount` | Auto | `rev_devolution_claim` | `variance_amount` | `claimed_amount - computed_entitlement` |
| **Claim No (Auto)** | `claim_no` | Auto | `rev_devolution_claim` | `claim_no` | `VARCHAR(50) UNIQUE`, via `fn_rev_next_seq` |

#### Action: "Approve Devolution & Issue Advice" &rarr; Target Database Mapping

When PAO Checker approves a claim and generates payment advice:
- **Target Table**: `ifms_budget.rev_devolution_advice`
- **Columns**: `advice_no` (via `fn_rev_next_seq`), `claim_id` (FK), `local_body_id` (FK), `advice_date` (DATE), `approved_amount` (NUMERIC), `bank_account_no`, `ifsc_code`, `epay_ref_no`, `debit_head_id` (FK &rarr; `chart_of_account`), `signed_by` (FK &rarr; `app_user`).
- **Updates in `rev_devolution_claim`**: `status='Settled'`, `advice_no`, `epay_ref_no`, `settled_at` = `clock_timestamp()`.

---

### 3.10 Accounting & Receipt Booking (`AccountingPage.tsx`)
**Route**: `/accounting`  
**Required Capability**: `nav.accounting`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `FINANCE`, `AUDITOR`  
**Total Interlinked Tables**: **7**

#### Interlinked Tables
1. `ifms_budget.rev_receipt_voucher` (Double-entry voucher header)
2. `ifms_budget.rev_voucher_item` (Double-entry Debit & Credit lines)
3. `ifms_budget.rev_recon_result` (Underlying matched receipts being booked)
4. `ifms_budget.rev_suspense_register` (Suspense & RAT ledger entries)
5. `ifms_budget.chart_of_account` (Bank clearing debit head & Revenue credit heads)
6. `ifms_budget.app_user` (Voucher Maker & Checker user IDs)
7. `ifms_budget.audit_change_log` (CDC audit records)

#### Actions & Forms &rarr; Database Target Mapping

| User Action / UI Form | Trigger Element | HTTP Request | Target Table in `ifms_budget` | Destination Columns & Data Types | Interlinked Foreign Key Table & Column |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Create Booking Voucher (Single / Bulk)** | "Create Vouchers for All Ready Receipts" (`PAO_MAKER`) | `POST /api/v1/accounting/vouchers/create-bulk` | `rev_receipt_voucher`<br>`rev_voucher_item`<br>`rev_recon_result` | `voucher_no` (VARCHAR, via `fn_rev_next_seq`)<br>`recon_id` (BIGINT)<br>`voucher_date` (DATE)<br>`financial_year` (VARCHAR)<br>`pao_code` (VARCHAR)<br>`total_amount` (NUMERIC)<br>`status='Draft'`<br>`prepared_by` (BIGINT)<br>`rev_voucher_item.entry_type` ('DEBIT'/'CREDIT')<br>`rev_voucher_item.coa_id` (BIGINT)<br>`rev_voucher_item.amount` (NUMERIC)<br>`rev_recon_result.booking_status='DRAFT_VOUCHER'` | `recon_id` &rarr; `rev_recon_result.recon_id`<br>`prepared_by` &rarr; `app_user.user_id`<br>`coa_id` &rarr; `chart_of_account.coa_id` (Debit = Bank Clearing Head, Credit = Revenue Head) |
| **Approve & Post Draft Vouchers** | "Approve All Draft Vouchers" (`PAO_CHECK`) | `POST /api/v1/accounting/vouchers/approve-bulk` | `rev_receipt_voucher`<br>`rev_recon_result` | `rev_receipt_voucher.status='Approved'`<br>`rev_receipt_voucher.checker_user_id` = Active User<br>`rev_receipt_voucher.approved_at` = `clock_timestamp()`<br>`rev_recon_result.booking_status='BOOKED'` | `checker_user_id` &rarr; `app_user.user_id`<br>Enforces dual-control separation of duties |
| **Clear Suspense / RAT Entry** | "Clear Suspense Entry" Modal (Transfer head, Remarks) | `POST /api/v1/accounting/suspense/{id}/clear` | `rev_suspense_register` | `status='CLEARED'`<br>`cleared_at` = `clock_timestamp()`<br>`clearing_remarks` (TEXT) | `suspense_id` &rarr; `rev_suspense_register.suspense_id`<br>`suspense_head_id` &rarr; `chart_of_account.coa_id` |

---

### 3.11 Analytical Reports & MIS (`ReportsPage.tsx`)
**Route**: `/reports`  
**Required Capability**: `nav.reports`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `BANK_OPS`, `AUDITOR`  
**Total Interlinked Tables**: **14**

#### Interlinked Tables
All staging, reconciliation, SLA, refund, devolution, and voucher tables + master dimensions (`department`, `rev_agency_bank`, `rev_local_body`, `chart_of_account`, `app_user`, `audit_change_log`).

#### Filter Fields & Dynamic Reports &rarr; Target Database Mapping

| Report ID | Report Name | Frontend Filter Inputs | Primary Database Source Tables | Destination Columns Queried |
| :--- | :--- | :--- | :--- | :--- |
| `r01` | Daily Collection & Mode Distribution | Date From, Date To, Revenue Source, Dept | `rev_portal_transaction_staging`, `rev_recon_result` | `payment_date`, `payment_mode`, `amount`, `dept_code` |
| `r02` | Source-wise Tax & Non-Tax Collection | Date Range, Source Type (Tax/Non-Tax) | `rev_portal_transaction_staging`, `rev_revenue_source` | `amount`, `is_tax_revenue`, `source_name` |
| `r03` | 3-Way Reconciliation Control Summary | Recon Run, Date Range | `rev_recon_run`, `rev_recon_result` | `matched_count`, `portal_total`, `bank_total`, `rbi_total`, `amount_difference` |
| `r04` | Transaction-wise Detailed Reconciliation | Status, Challan, CIN, Date Range | `rev_recon_result`, `rev_recon_leg_linkage` | `challan_no`, `cin`, `cpin`, `status`, `match_type`, `rule_applied` |
| `r05` | PAO & Department-wise Pending Recon | PAO Code, Department Code | `rev_recon_result`, `department` | `pao_code`, `dept_code`, `status='Pending'` |
| `r06` | Suspense & RAT Unidentified Credits | Suspense Type, Status, Ageing Days | `rev_suspense_register`, `chart_of_account` | `suspense_type`, `amount`, `ageing_days`, `status` |
| `r07` | Amount Mismatch & Duplicate Receipts | Revenue Source, Date Range | `rev_recon_result`, `rev_recon_leg_linkage` | `amount_difference`, `status='Mismatch'` / `'Duplicate'` |
| `r08` | Agency Bank Scroll Receipt & Processing | Bank Code, Date Range | `rev_agency_bank_scroll_staging`, `rev_agency_bank` | `bank_code`, `scroll_date`, `amount`, `bank_reference_no` |
| `r09` | Bank Remittance SLA & Penal Interest | Bank Code, Delay Days | `rev_penal_claim`, `rev_agency_bank`, `rev_sla_rule` | `delay_days`, `penal_interest_computed`, `annual_rate_pct` |
| `r10` | Penal Interest Recovery & Waiver | Bank Code, Claim Status | `rev_penal_claim`, `rev_penal_letter`, `rev_penal_waiver`| `penal_interest_recovered`, `penal_interest_waived`, `status` |
| `r11` | Refund Case Register & Ageing | Refund Type, Stage, Status | `rev_refund_case`, `department`, `ddo` | `case_no`, `claimed_amount`, `current_stage`, `status` |
| `r12` | Refund Turnaround Time & Performance | Date Range, Refund Type | `rev_refund_case` | `created_at`, `paid_at`, TAT days |
| `r13` | Statutory Devolution Claims & Settlement | Local Body, Period | `rev_devolution_claim`, `rev_local_body`, `rev_devolution_advice` | `claimed_amount`, `computed_entitlement`, `variance_amount` |
| `r14` | Head-wise Revenue Collection & Booking | Financial Year, Major Head | `chart_of_account`, `rev_receipt_voucher`, `rev_voucher_item` | `coa_code`, `head_code`, `total_amount`, `entry_type` |
| `r15` | Discrepancy & Exception Register | Category, Severity, Status | `rev_exception`, `rev_recon_result` | `category`, `severity`, `status`, `due_date` |
| `r16` | User Activity & Audit Trail | Module, Operation, User, Date Range | `audit_change_log`, `app_user` | `table_name`, `operation`, `changed_by`, `changed_at` |
| `r17` | Upload Batch & Data Quality | Batch Type, Status | `rev_upload_batch`, `rev_upload_rejected_row` | `total_records`, `invalid_records`, `control_total` |

---

### 3.12 Masters & System Configuration (`MastersPage.tsx`)
**Route**: `/masters`  
**Required Capability**: `nav.masters`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `BANK_OPS`, `AUDITOR`  
**Total Interlinked Tables**: **10**

#### Interlinked Tables
1. `ifms_budget.rev_agency_bank` (Agency Bank Master)
2. `ifms_budget.rev_bank_branch` (Bank Branch Master)
3. `ifms_budget.rev_revenue_portal` (Revenue Portal Master)
4. `ifms_budget.rev_revenue_source` (Revenue Source & Rule Master)
5. `ifms_budget.rev_sla_rule` (Statutory SLA Parameters)
6. `ifms_budget.rev_local_body` (Local Body Master)
7. `ifms_budget.rev_devolution_rule` (Devolution Percentage Sharing Rules)
8. `ifms_budget.rev_system_config` (Global System Configuration)
9. `ifms_budget.chart_of_account` (Chart of Accounts Master)
10. `ifms_budget.audit_change_log` (CDC audit records)

#### Master Subtabs & Forms &rarr; Database Target Mapping

| Master Subtab | Form Field / Modal Input | Target Table in `ifms_budget` | Destination Column Name & Data Type | Constraints & Key Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Agency Banks** | Bank Code<br>Bank Name<br>Clearing Account No<br>Nodal Officer Name<br>Nodal Officer Email<br>Nodal Officer Phone | `rev_agency_bank` | `bank_code` (VARCHAR(20) UNIQUE)<br>`bank_name` (VARCHAR(200))<br>`clearing_account_no` (VARCHAR(50))<br>`nodal_officer_name` (VARCHAR(150))<br>`nodal_officer_email` (VARCHAR(150))<br>`nodal_officer_phone` (VARCHAR(30)) | `bank_id` (PK)<br>`created_by`, `updated_by` &rarr; `app_user.user_id` |
| **Bank Branches** | Bank ID<br>Branch Code<br>Branch Name<br>IFSC Code<br>City | `rev_bank_branch` | `bank_id` (BIGINT)<br>`branch_code` (VARCHAR(30))<br>`branch_name` (VARCHAR(200))<br>`ifsc_code` (VARCHAR(20))<br>`city` (VARCHAR(100)) | `branch_id` (PK)<br>FK: `bank_id` &rarr; `rev_agency_bank.bank_id` |
| **Revenue Portals** | Portal Code<br>Portal Name<br>Department ID<br>API Endpoint<br>Technical Contact | `rev_revenue_portal` | `portal_code` (VARCHAR(50) UNIQUE)<br>`portal_name` (VARCHAR(200))<br>`department_id` (BIGINT)<br>`api_endpoint` (VARCHAR(255))<br>`technical_contact` (VARCHAR(150)) | `portal_id` (PK)<br>FK: `department_id` &rarr; `department.department_id` |
| **Revenue Sources** | Source Code<br>Source Name<br>Department ID<br>Default PAO Code<br>Portal ID<br>Default Receipt Head ID<br>Allowed Modes<br>Precedence Keys<br>SLA Rule ID<br>Is Tax Revenue | `rev_revenue_source` | `source_code` (VARCHAR(30) UNIQUE)<br>`source_name` (VARCHAR(150))<br>`department_id` (BIGINT)<br>`default_pao_code` (VARCHAR(30))<br>`portal_id` (BIGINT)<br>`default_receipt_head_id` (BIGINT)<br>`allowed_payment_modes` (ARRAY(VARCHAR))<br>`match_key_precedence` (ARRAY(VARCHAR))<br>`sla_rule_id` (BIGINT)<br>`is_tax_revenue` (BOOLEAN) | `source_id` (PK)<br>FK: `department_id` &rarr; `department`<br>FK: `portal_id` &rarr; `rev_revenue_portal`<br>FK: `default_receipt_head_id` &rarr; `chart_of_account`<br>FK: `sla_rule_id` &rarr; `rev_sla_rule` |
| **SLA Rules** | Rule Code<br>Rule Name<br>Payment Mode<br>Allowed Remittance Days<br>Grace Days<br>Annual Penal Rate %<br>Calculation Basis<br>Base Date Type | `rev_sla_rule` | `rule_code` (VARCHAR(30) UNIQUE)<br>`rule_name` (VARCHAR(150))<br>`payment_mode` (VARCHAR(30))<br>`allowed_remittance_days` (INT)<br>`grace_days` (INT)<br>`annual_penal_rate_pct` (NUMERIC(5,2))<br>`calculation_basis` (VARCHAR(30))<br>`base_date_type` (VARCHAR(30)) | `sla_rule_id` (PK) |
| **Local Bodies** | Local Body Code<br>Local Body Name<br>Body Type<br>Bank Account No<br>Bank Name<br>IFSC Code | `rev_local_body` | `local_body_code` (VARCHAR(30) UNIQUE)<br>`local_body_name` (VARCHAR(250))<br>`body_type` (VARCHAR(50))<br>`bank_account_no` (VARCHAR(50))<br>`bank_name` (VARCHAR(150))<br>`ifsc_code` (VARCHAR(20)) | `local_body_id` (PK) |
| **Devolution Rules** | Rule Code<br>Local Body ID<br>Source ID<br>Receipt Head ID<br>Share Basis<br>Share Value (%)<br>Valid From / Valid To | `rev_devolution_rule` | `rule_code` (VARCHAR(30) UNIQUE)<br>`local_body_id` (BIGINT)<br>`source_id` (BIGINT)<br>`receipt_head_id` (BIGINT)<br>`share_basis` ('PERCENTAGE')<br>`share_value` (NUMERIC(10,4))<br>`valid_from` (DATE)<br>`valid_to` (DATE) | `dev_rule_id` (PK)<br>FK: `local_body_id` &rarr; `rev_local_body`<br>FK: `source_id` &rarr; `rev_revenue_source`<br>FK: `receipt_head_id` &rarr; `chart_of_account` |
| **System Config** | Demo Business Date<br>Financial Year<br>Amount Tolerance (₹)<br>Date Tolerance (Days)<br>Default Penal Rate %<br>Suspense Head ID<br>RAT Suspense Head ID<br>Bank Clearing Head ID | `rev_system_config` | `demo_business_date` (DATE)<br>`current_financial_year` (VARCHAR(15))<br>`amount_tolerance` (NUMERIC(10,2))<br>`date_tolerance_days` (INT)<br>`default_penal_rate_pct` (NUMERIC(5,2))<br>`suspense_head_id` (BIGINT)<br>`rat_suspense_head_id` (BIGINT)<br>`bank_clearing_head_id` (BIGINT) | `config_id=1` (Single Row Singleton Config)<br>FKs &rarr; `chart_of_account.coa_id` |

---

### 3.13 Audit Trail (`AuditTrailPage.tsx`)
**Route**: `/audit`  
**Required Capability**: `nav.audit`  
**Allowed Roles**: `SYSADMIN`, `TRE_ADMIN`, `PAO_MAKER`, `PAO_CHECK`, `DDO`, `FINANCE`, `BANK_OPS`, `AUDITOR`  
**Total Interlinked Tables**: **2**

#### Interlinked Tables
1. `ifms_budget.audit_change_log` (Master CDC immutable event stream)
2. `ifms_budget.app_user` (Acting user details)

#### Filter Parameters &rarr; Database Target Mapping

| Frontend Filter Field | UI Input Type | HTTP Request | Target Database Table | Queried Columns |
| :--- | :--- | :--- | :--- | :--- |
| **Module / Table** | Dropdown | `GET /api/v1/audit/logs?table={val}` | `audit_change_log` | `table_name` (e.g. `rev_recon_result`, `rev_receipt_voucher`, `rev_upload_batch`) |
| **Operation Type** | Dropdown | `GET /api/v1/audit/logs?op={val}` | `audit_change_log` | `operation` (`'I'` = Insert, `'U'` = Update, `'D'` = Delete) |
| **Date Range** | Date Pickers | `GET /api/v1/audit/logs?from={d}&to={d}` | `audit_change_log` | `changed_at` (TIMESTAMPTZ) |
| **Audit Detail Modal**| Click Row | `GET /api/v1/audit/logs/{id}` | `audit_change_log` | `old_data` (JSONB) vs `new_data` (JSONB) diff rendering |

---

### 3.14 Help & Test Suite (`HelpTestPage.tsx`)
**Route**: `/help`  
**Required Capability**: `nav.help`  
**Allowed Roles**: All roles including `CITIZEN`  
**Total Interlinked Tables**: **34** (Full Database Reset & Verification Scope)

#### Actions & Forms &rarr; Database Target Mapping

| User Action / UI Button | HTTP Request | Target Database Tables | Operations Executed in `ifms_budget` |
| :--- | :--- | :--- | :--- |
| **Run Demo Test Suite** | `POST /api/v1/help/test-suite/run` | All 34 `rev_*` and staging tables | 1. Resets database to 3 approved batches (53 source rows)<br>2. Validates CSV structural rules & duplicate checks<br>3. Executes 3-way reconciliation engine<br>4. Asserts 17 expected matching outcomes<br>5. Asserts exceptions, penal claims, and voucher creation<br>6. Stores test report in memory & audit stream |
| **Download Sample CSVs** | `GET /api/v1/help/samples/{key}` | Static Sample Provider | Downloads sample Portal, Bank, and RBI CSV files for test uploads |

---

### 3.15 Global Header, System Notifications & Quick Actions

#### Header Controls &rarr; Target Database Mapping

| Global Header Component | Trigger Action | HTTP Request | Target Database Table | Destination Columns & Data Types |
| :--- | :--- | :--- | :--- | :--- |
| **Role Switcher Dropdown** | Select any of 9 roles | `POST /api/v1/auth/switch-role` | `app_user`<br>`audit_change_log` | Logs active persona switch to `audit_change_log`<br>Fetches role-scoped notifications |
| **Financial Year Selector** | Select FY (e.g. `2026-27`) | `PUT /api/v1/config` (`SYSADMIN` only) | `rev_system_config` | `current_financial_year` (`VARCHAR(15)`), `updated_by`, `updated_at` |
| **Business Date Chip** | Click and select Date | `PUT /api/v1/config` (`SYSADMIN` only) | `rev_system_config` | `demo_business_date` (`DATE`), `updated_by`, `updated_at` |
| **Notification Bell Modal** | Click Bell / Click "Mark all read" | `POST /api/v1/notifications/mark-read` | `rev_system_notifications` | `is_read=TRUE`, `read_at` = `clock_timestamp()` for active role |
| **Quick Actions Modal (Ctrl+K)** | Click any quick action (Recon, Vouchers, Test Suite, Reset) | Respective API Endpoint | Target module tables | Executes corresponding transactional workflows listed in sections 3.1 &ndash; 3.14 |

---

## 4. Transaction Safety, Dual Control & Change-Data-Capture (CDC) Rules

1. **Atomic Multi-Table Transactions (`BEGIN ... COMMIT`)**:
   - Every multi-step workflow (e.g. Reconciliation run writing run record + results + linkages + exceptions + penal interest + suspense) executes inside a single database transaction block. Any failure triggers a complete rollback.
2. **Deterministic Sequence Numbering (`fn_rev_next_seq`)**:
   - All document identifiers (`BAT-*`, `RV-*`, `REF-*`, `ADV-*`, `CLM-*`, `NOT-*`) are atomically allocated from `ifms_budget.document_number_sequence` with row-level locks (`FOR UPDATE`), guaranteeing zero gaps and no duplicate IDs under high concurrency.
3. **Dual-Control Separation of Duties (Maker-Checker)**:
   - File Uploads: Uploaded by `PAO_MAKER` &rarr; Approved by `PAO_CHECK`.
   - Manual Overrides: Proposed by `PAO_MAKER` &rarr; Approved by `PAO_CHECK`.
   - Receipt Vouchers: Drafted by `PAO_MAKER` &rarr; Approved and GL-posted by `PAO_CHECK`.
   - SLA Waivers: Prepared by Treasury Officer &rarr; Approved by `PAO_CHECK` / `FINANCE`.
   - Refunds: Prepared by `DDO` &rarr; Approved by `PAO_CHECK`.
   - Devolution: Claimed by `DDO` / Local Body &rarr; Approved by `PAO_CHECK`.
4. **CDC Audit Triggers**:
   - Database triggers (`trg_rev_recon_audit`, `trg_rev_voucher_audit`, `trg_rev_refund_audit`) automatically capture JSON diffs (`old_data` vs `new_data`) into `ifms_budget.audit_change_log` on every `INSERT`, `UPDATE`, and `DELETE`.
