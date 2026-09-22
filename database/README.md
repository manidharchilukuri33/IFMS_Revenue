# IFMS Revenue & Reconciliation Module - Database Scripts

This folder contains the complete, updated master SQL script for the **IFMS Revenue Collection & Reconciliation Module**.

---

## File Overview

- **`ifms_revenue_complete_master_schema_and_seed.sql`**: Master SQL script that provides 100% end-to-end database definition, migration safety blocks, views, stored procedures, and fully compliant seed data across all 89 tables in the `ifms_budget` schema.

---

## Included Database Objects & Updates

1. **Standard Organization, Branch & Audit Columns on all `rev_` Tables**:
   - `organization_id int8 NOT NULL REFERENCES ifms_budget.organization(organization_id)`
   - `org_branch_id   int8 NOT NULL REFERENCES ifms_budget.branch(branch_id)`
   - `created_by      bigint REFERENCES ifms_budget.app_user(user_id)`
   - `updated_by      bigint REFERENCES ifms_budget.app_user(user_id)`
   - `workflow_status character varying(30) DEFAULT 'ACTIVE'`

2. **Universal `workflow_status` (varchar 30)**:
   - Verified and added to **every single table** in the `ifms_budget` schema via a safe PL/pgSQL migration block.

3. **Double-Entry Accounting & Booking Voucher Updates (`rev_receipt_voucher`)**:
   - Dropped `total_amount`
   - Added `debit_amount numeric(15,2)` and `credit_amount numeric(15,2)`
   - Added `coa_id`, `major_code`, `minor_code`, `department_id`, `office_id`, `transaction_code`, `scheme_id`, `project_id`, `budget_head_id`, `workflow_status`

4. **Complete Table Seeding (0 Empty Operational Tables)**:
   - Master Tables: `agency_bank`, `bank_branch`, `rev_revenue_portal`, `rev_sla_rule`, `rev_revenue_source`, `rev_local_body`, `rev_system_config`
   - Staging & Processing: `rev_upload_batch`, `rev_portal_transaction_staging`, `rev_agency_bank_scroll_staging`, `rev_rbi_luggage_staging`, `receipt_staging`, `treasury_expenditure_staging`, `rev_upload_rejected_row`
   - Reconciliation & Exceptions: `rev_recon_run`, `rev_recon_result`, `rev_recon_leg_linkage`, `rev_recon_override`, `rev_exception`, `rev_exception_note`, `rev_exception_letter`
   - Bank SLA Penal Interest: `rev_penal_claim`, `rev_penal_letter`, `rev_penal_bank_response`, `rev_penal_waiver`
   - Double-Entry GL Accounting: `rev_receipt_voucher`, `rev_voucher_item`, `rev_suspense_register`
   - Refunds Workflow: `rev_refund_case`, `rev_refund_verification`, `rev_refund_bill`
   - Local Body Devolution: `rev_devolution_rule`, `rev_devolution_claim`, `rev_devolution_computation`, `rev_devolution_advice`

5. **Views & Stored Procedures**:
   - `rev_vw_dashboard_kpis`, `rev_vw_3way_recon_summary`, `rev_vw_bank_sla_performance`, `rev_vw_suspense_and_rat`
   - `sp_rev_create_booking_vouchers`, `sp_rev_approve_booking_vouchers`

---

## How to Execute in DBeaver

1. Open **DBeaver** and connect to your PostgreSQL database (`ifms_budget`).
2. Open a new SQL Editor window (**Ctrl + ]** or **SQL Editor -> New SQL Script**).
3. Open `ifms_revenue_complete_master_schema_and_seed.sql` in DBeaver (**File -> Open File...** or drag & drop).
4. Execute the full script by pressing **Alt + X** (Execute SQL Script).
5. Verify that all statements complete successfully and `0 empty tables` remain.

---

## How to Execute via `psql` (CLI)

```bash
psql -U ifms_budget -d ifms_budget -h 127.0.0.1 -p 5432 -f database/ifms_revenue_complete_master_schema_and_seed.sql
```
