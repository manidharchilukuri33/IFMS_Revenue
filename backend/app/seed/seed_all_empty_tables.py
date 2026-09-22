import asyncio
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import select, text, func
from app.core.database import AsyncSessionLocal

async def seed_all_empty_tables():
    print("================================================================================")
    print(" Populating ALL 22 Empty Tables with Coherent Static & Dynamic Relational Data")
    print("================================================================================")

    async with AsyncSessionLocal() as db:
        org_id = 1
        branch_id = 1
        user_id = 1

        # ---------------------------------------------------------
        # 1. agency_bank
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.agency_bank"))).scalar()
        if cnt == 0:
            print("Seeding agency_bank...")
            await db.execute(text("""
                INSERT INTO ifms_budget.agency_bank 
                (bank_id, bank_code, bank_name, clearing_account_no, nodal_officer_name, nodal_officer_email, nodal_officer_phone, is_active, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 'SBI', 'State Bank of India', '100029384812', 'Rajesh V. Sharma', 'nodal.sbi@ifms.gov.in', '+91-9823011223', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (2, 'HDFC', 'HDFC Bank Ltd', '501002384910', 'Ananya Deshpande', 'nodal.hdfc@ifms.gov.in', '+91-9823011224', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (3, 'ICICI', 'ICICI Bank Ltd', '000405001293', 'Siddharth Roy', 'nodal.icici@ifms.gov.in', '+91-9823011225', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (4, 'PNB', 'Punjab National Bank', '112000210004', 'Vikramaditya Rao', 'nodal.pnb@ifms.gov.in', '+91-9823011226', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (bank_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] agency_bank seeded (4 banks).")

        # ---------------------------------------------------------
        # 2. bank_branch
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.bank_branch"))).scalar()
        if cnt == 0:
            print("Seeding bank_branch...")
            await db.execute(text("""
                INSERT INTO ifms_budget.bank_branch
                (bank_branch_id, bank_id, organization_id, org_branch_id, branch_code, branch_name, ifsc_code, city, is_active, created_by, updated_by, workflow_status)
                VALUES
                (1, 1, :org_id, :branch_id, 'SBI-NAG-001', 'SBI Nagpur Main Branch', 'SBIN0001001', 'Nagpur', true, :user_id, :user_id, 'ACTIVE'),
                (2, 1, :org_id, :branch_id, 'SBI-DEL-010', 'SBI Delhi Treasury Branch', 'SBIN0002002', 'Delhi', true, :user_id, :user_id, 'ACTIVE'),
                (3, 2, :org_id, :branch_id, 'HDFC-DEL-002', 'HDFC Secretariat Branch', 'HDFC0000123', 'Delhi', true, :user_id, :user_id, 'ACTIVE'),
                (4, 2, :org_id, :branch_id, 'HDFC-MUM-005', 'HDFC Nariman Point Branch', 'HDFC0000456', 'Mumbai', true, :user_id, :user_id, 'ACTIVE'),
                (5, 3, :org_id, :branch_id, 'ICICI-DEL-003', 'ICICI Barakhamba Road Branch', 'ICIC0000456', 'Delhi', true, :user_id, :user_id, 'ACTIVE'),
                (6, 3, :org_id, :branch_id, 'ICICI-NAG-004', 'ICICI Civil Lines Nagpur Branch', 'ICIC0000789', 'Nagpur', true, :user_id, :user_id, 'ACTIVE'),
                (7, 4, :org_id, :branch_id, 'PNB-DEL-005', 'PNB KG Marg Branch', 'PUNB0005001', 'Delhi', true, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (bank_branch_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] bank_branch seeded (7 branches).")

        # ---------------------------------------------------------
        # 3. rev_agency_bank_scroll_staging
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_agency_bank_scroll_staging"))).scalar()
        if cnt == 0:
            print("Seeding rev_agency_bank_scroll_staging...")
            b_res = await db.execute(text("SELECT batch_id FROM ifms_budget.rev_upload_batch WHERE batch_type = 'BANK_SCROLL' ORDER BY batch_id DESC LIMIT 1"))
            batch_id_val = b_res.scalar() or 69
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_agency_bank_scroll_staging
                (batch_id, scroll_no, scroll_date, bank_code, branch_code, revenue_source, dept_code, pao_code, challan_no, cpin, cin, bank_reference_no, utr_no, payer_id, payer_name, payment_mode, payment_received_date, instrument_realization_date, bank_remittance_date, amount, receipt_head, bank_status, is_valid, is_duplicate, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (:bid, 'SBI-20260910-001', '2026-09-10', 'SBI', 'SBI-NAG-001', 'GST', 'TT', 'PAO21', 'CH-GST-10001', 'CPIN-10001', 'CIN-10001', 'BRN-10001', 'UTR-10001', 'GSTIN27ABCDE1234F1Z5', 'ABC Traders', 'NETBANKING', '2026-09-10', NULL, '2026-09-10', 125000.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260910-001', '2026-09-10', 'SBI', 'SBI-NAG-001', 'GST', 'TT', 'PAO21', 'CH-GST-10002', 'CPIN-10002', 'CIN-10002', 'BRN-10002', 'UTR-10002', 'GSTIN27PQRSX6789K1Z2', 'Metro Supplies', 'UPI', '2026-09-10', NULL, '2026-09-10', 78500.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'HDFC-20260910-001', '2026-09-10', 'HDFC', 'HDFC-DEL-002', 'EXCISE', 'EXCISE', 'PAO10', 'CH-EX-20001', NULL, NULL, 'BRN-20001', 'UTR-20001', 'EXC-LIC-1001', 'Royal Beverages Pvt Ltd', 'NETBANKING', '2026-09-10', NULL, '2026-09-11', 250000.00, '0039-00-105-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'ICICI-20260910-001', '2026-09-10', 'ICICI', 'ICICI-DEL-003', 'TRANSPORT', 'TRANSPORT', 'PAO11', 'CH-TR-30001', NULL, NULL, 'BRN-30001', 'UTR-30001', 'DL-9876543210', 'Ramesh Kumar', 'CARD', '2026-09-10', NULL, '2026-09-10', 4500.00, '0041-00-101-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260910-002', '2026-09-10', 'SBI', 'SBI-DEL-010', 'STAMP', 'STAMPREG', 'PAO12', 'CH-ST-40001', NULL, NULL, 'BRN-40001', 'UTR-40001', 'PAN-AABCA1111A', 'Anita Sharma', 'NETBANKING', '2026-09-10', NULL, '2026-09-10', 60000.00, '0030-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'PNB-20260910-001', '2026-09-10', 'PNB', 'PNB-DEL-005', 'DVAT', 'DVAT', 'PAO06', 'CH-DV-50001', NULL, 'CIN-DV-50001', 'BRN-50001', 'UTR-50001', 'TIN-07123456789', 'Classic Enterprises', 'CHEQUE', '2026-09-10', '2026-09-12', '2026-09-13', 94000.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260910-003', '2026-09-10', 'SBI', 'SBI-NAG-001', 'NONTAX', 'GAD', 'PAO15', 'CH-NT-60001', NULL, NULL, 'BRN-60001', 'UTR-60001', 'CIT-0001', 'Sunita Patil', 'CASH', '2026-09-10', NULL, '2026-09-12', 1200.00, '0070-60-800-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260911-001', '2026-09-11', 'SBI', 'SBI-NAG-001', 'GST', 'TT', 'PAO21', 'CH-GST-10003', 'CPIN-10003', 'CIN-10003', 'BRN-10003-A', 'UTR-10003-A', 'GSTIN27LMNOP4567Q1Z8', 'Delta Manufacturing', 'NETBANKING', '2026-09-11', NULL, '2026-09-11', 100000.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260911-002', '2026-09-11', 'SBI', 'SBI-NAG-001', 'GST', 'TT', 'PAO21', 'CH-GST-10003', 'CPIN-10003', 'CIN-10003', 'BRN-10003-B', 'UTR-10003-B', 'GSTIN27LMNOP4567Q1Z8', 'Delta Manufacturing', 'NETBANKING', '2026-09-11', NULL, '2026-09-12', 50000.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'HDFC-20260911-001', '2026-09-11', 'HDFC', 'HDFC-DEL-002', 'GST', 'TT', 'PAO21', 'CH-GST-10004', 'CPIN-10004', 'CIN-10004', 'BRN-10004', 'UTR-10004', 'GSTIN27UVWXY9876R1Z1', 'Zenith Industries', 'NETBANKING', '2026-09-11', NULL, '2026-09-11', 80000.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'HDFC-20260911-002', '2026-09-11', 'HDFC', 'HDFC-DEL-002', 'EXCISE', 'EXCISE', 'PAO10', 'CH-EX-20002', NULL, NULL, 'BRN-20002', 'UTR-20002', 'EXC-LIC-1002', 'Sunrise Hotels Ltd', 'CASH', '2026-09-11', NULL, '2026-09-14', 35000.00, '0039-00-105-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'ICICI-20260911-001', '2026-09-11', 'ICICI', 'ICICI-DEL-003', 'TRANSPORT', 'TRANSPORT', 'PAO11', 'CH-TR-30002', NULL, NULL, 'BRN-30002', 'UTR-30002', 'MH31AB1234', 'Vikram Motors', 'UPI', '2026-09-11', NULL, '2026-09-11', 8500.00, '0041-00-101-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260911-003', '2026-09-11', 'SBI', 'SBI-DEL-010', 'STAMP', 'STAMPREG', 'PAO12', 'CH-ST-40002', NULL, NULL, 'BRN-40002', 'UTR-40002', 'PAN-BBCPS2222B', 'Sanjay Verma', 'NETBANKING', '2026-09-11', NULL, '2026-09-11', 110000.00, '0030-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'ICICI-20260911-002', '2026-09-11', 'ICICI', 'ICICI-NAG-004', 'NONTAX', 'PWD', 'PAO15', 'CH-NT-60002', NULL, NULL, 'BRN-60002', 'UTR-60002', 'CIT-0002', 'Meera Joshi', 'NETBANKING', '2026-09-11', NULL, '2026-09-11', 25000.00, '0070-60-800-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260912-001', '2026-09-12', 'SBI', 'SBI-NAG-001', 'TRANSPORT', 'TRANSPORT', 'PAO11', 'CH-TR-30003', NULL, NULL, 'BRN-30003-A', 'UTR-30003-A', 'MH49XY7890', 'Partial Settlement Transport', 'NETBANKING', '2026-09-12', NULL, '2026-09-12', 12000.00, '0041-00-101-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260912-002', '2026-09-12', 'SBI', 'SBI-NAG-001', 'TRANSPORT', 'TRANSPORT', 'PAO11', 'CH-TR-30003', NULL, NULL, 'BRN-30003-B', 'UTR-30003-B', 'MH49XY7890', 'Partial Settlement Transport', 'NETBANKING', '2026-09-12', NULL, '2026-09-13', 8000.00, '0041-00-101-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260912-003', '2026-09-12', 'SBI', 'SBI-NAG-001', 'GST', 'TT', 'PAO21', 'CH-GST-10006', 'CPIN-10006', 'CIN-10006', 'BRN-10006', 'UTR-10006', 'GSTIN27DUPLI1111D1Z1', 'Duplicate Demo Pvt Ltd', 'UPI', '2026-09-12', NULL, '2026-09-12', 15000.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'SBI-20260912-004', '2026-09-12', 'SBI', 'SBI-NAG-001', 'GST', 'TT', 'PAO21', 'CH-GST-10006', 'CPIN-10006', 'CIN-10006', 'BRN-10006-DUP', 'UTR-10006-DUP', 'GSTIN27DUPLI1111D1Z1', 'Duplicate Demo Pvt Ltd', 'UPI', '2026-09-12', NULL, '2026-09-12', 15000.00, '0040-00-102-01-00-01', 'REMITTED', true, true, :org_id, :branch_id, :user_id, :user_id, 'APPROVED'),
                (:bid, 'HDFC-20260912-001', '2026-09-12', 'HDFC', 'HDFC-DEL-002', 'GST', 'TT', 'PAO21', 'CH-GST-99999', 'CPIN-99999', 'CIN-99999', 'BRN-99999', 'UTR-99999', 'GSTIN27RAT0000R1Z1', 'RBI Only Candidate', 'NETBANKING', '2026-09-12', NULL, '2026-09-12', 32000.00, '0040-00-102-01-00-01', 'REMITTED', true, false, :org_id, :branch_id, :user_id, :user_id, 'APPROVED')
                ON CONFLICT DO NOTHING;
            """), {"bid": batch_id_val, "org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_agency_bank_scroll_staging seeded (19 records).")

        # ---------------------------------------------------------
        # 4. receipt_staging
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.receipt_staging"))).scalar()
        if cnt == 0:
            print("Seeding receipt_staging...")
            await db.execute(text("""
                INSERT INTO ifms_budget.receipt_staging
                (source_file_name, source_receipt_no, receipt_date, import_batch_no, budget_version_id, organization_id, department_id, demand_id, coa_id, fund_source_id, receipt_amount, transaction_status, validation_message, posted_at, created_by, updated_by, workflow_status)
                VALUES
                ('TREASURY_RECEIPTS_20260915.csv', 'REC-TR-2026-001', '2026-09-15', 'IMP-2026-09-001', 1, :org_id, 15, 1, 36, 1, 125000.00, 'VALIDATED', 'Reconciled with Portal & Bank scroll', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_RECEIPTS_20260915.csv', 'REC-TR-2026-002', '2026-09-15', 'IMP-2026-09-001', 1, :org_id, 15, 1, 36, 1, 78500.00, 'VALIDATED', 'Reconciled with Portal & Bank scroll', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_RECEIPTS_20260915.csv', 'REC-TR-2026-003', '2026-09-15', 'IMP-2026-09-001', 1, :org_id, 16, 2, 40, 1, 250000.00, 'VALIDATED', 'Reconciled with Portal & Bank scroll', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_RECEIPTS_20260915.csv', 'REC-TR-2026-004', '2026-09-15', 'IMP-2026-09-001', 1, :org_id, 17, 3, 37, 1, 60000.00, 'VALIDATED', 'Reconciled with Portal & Bank scroll', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_RECEIPTS_20260915.csv', 'REC-TR-2026-005', '2026-09-15', 'IMP-2026-09-001', 1, :org_id, 18, 4, 36, 1, 94000.00, 'VALIDATED', 'Reconciled with Portal & Bank scroll', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_RECEIPTS_20260915.csv', 'REC-TR-2026-006', '2026-09-15', 'IMP-2026-09-001', 1, :org_id, 17, 3, 37, 1, 110000.00, 'VALIDATED', 'Reconciled with Portal & Bank scroll', NOW(), :user_id, :user_id, 'ACTIVE')
                ON CONFLICT DO NOTHING;
            """), {"org_id": org_id, "user_id": user_id})
            await db.commit()
            print("  [OK] receipt_staging seeded (6 records).")

        # ---------------------------------------------------------
        # 5. treasury_expenditure_staging
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.treasury_expenditure_staging"))).scalar()
        if cnt == 0:
            print("Seeding treasury_expenditure_staging...")
            await db.execute(text("""
                INSERT INTO ifms_budget.treasury_expenditure_staging
                (source_file_name, source_transaction_no, source_transaction_date, import_batch_no, budget_version_id, organization_id, department_id, demand_id, ddo_id, coa_id, scheme_id, project_id, fund_source_id, gross_amount, transaction_status, validation_message, posted_at, created_by, updated_by, workflow_status)
                VALUES
                ('TREASURY_EXP_20260915.csv', 'EXP-TR-2026-001', '2026-09-15', 'IMP-EXP-2026-09-001', 1, :org_id, 2, 2, 1, 2, 1, 1, 1, 45000.00, 'POSTED', 'Valid treasury voucher expenditure', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_EXP_20260915.csv', 'EXP-TR-2026-002', '2026-09-15', 'IMP-EXP-2026-09-001', 1, :org_id, 3, 3, 2, 3, 1, 1, 1, 120000.00, 'POSTED', 'PWD road maintenance bill cleared', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_EXP_20260915.csv', 'EXP-TR-2026-003', '2026-09-15', 'IMP-EXP-2026-09-001', 1, :org_id, 4, 4, 3, 4, 1, 1, 1, 85000.00, 'POSTED', 'Transport office administrative grant', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_EXP_20260915.csv', 'EXP-TR-2026-004', '2026-09-15', 'IMP-EXP-2026-09-001', 1, :org_id, 1, 1, 4, 5, 1, 1, 1, 310000.00, 'POSTED', 'Education teacher salary disbursement', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_EXP_20260915.csv', 'EXP-TR-2026-005', '2026-09-15', 'IMP-EXP-2026-09-001', 1, :org_id, 1, 1, 5, 6, 1, 1, 1, 15000.00, 'POSTED', 'School supplies procurement voucher', NOW(), :user_id, :user_id, 'ACTIVE'),
                ('TREASURY_EXP_20260915.csv', 'EXP-TR-2026-006', '2026-09-15', 'IMP-EXP-2026-09-001', 1, :org_id, 2, 2, 1, 7, 1, 1, 1, 95000.00, 'POSTED', 'Health clinic medical equipments purchase', NOW(), :user_id, :user_id, 'ACTIVE')
                ON CONFLICT DO NOTHING;
            """), {"org_id": org_id, "user_id": user_id})
            await db.commit()
            print("  [OK] treasury_expenditure_staging seeded (6 records).")

        # ---------------------------------------------------------
        # 6. rev_exception
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_exception"))).scalar()
        if cnt == 0:
            print("Seeding rev_exception...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_exception
                (exception_id, organization_id, org_branch_id, exception_no, recon_id, category, severity, status, ownership_type, assigned_user_id, due_date, exception_detail, resolution_reason, resolution_remarks, resolved_by, resolved_at, escalation_count, last_escalated_at, created_by, updated_by, workflow_status)
                VALUES
                (1, :org_id, :branch_id, 'EXC-2026-0001', 597, 'AMOUNT_MISMATCH', 'High', 'Open', 'BANK', :user_id, '2026-09-22', 'Amount variance of Rs 2,000 between GST Portal (Rs 82,000) and HDFC Scroll (Rs 80,000) for Challan CH-GST-10004.', NULL, NULL, NULL, NULL, 0, NULL, :user_id, :user_id, 'ACTIVE'),
                (2, :org_id, :branch_id, 'EXC-2026-0002', 602, 'UNREMITTED_CHALLAN', 'Critical', 'Escalated', 'BANK', :user_id, '2026-09-20', 'Challan CH-GST-10005 of Rs 47,000 paid on GSTN portal on 2026-09-12 but not remitted in bank scroll beyond SLA window.', NULL, NULL, NULL, NULL, 1, '2026-09-18 10:30:00+00', :user_id, :user_id, 'ACTIVE'),
                (3, :org_id, :branch_id, 'EXC-2026-0003', 604, 'DUPLICATE_SCROLL', 'High', 'Open', 'PAO', :user_id, '2026-09-21', 'Duplicate bank scroll credit detected for Challan CH-GST-10006 (Rs 15,000 x 2 = Rs 30,000) against portal collection of Rs 15,000.', NULL, NULL, NULL, NULL, 0, NULL, :user_id, :user_id, 'ACTIVE'),
                (4, :org_id, :branch_id, 'EXC-2026-0004', 605, 'ORPHAN_BANK_CREDIT', 'Medium', 'Assigned', 'PAO', :user_id, '2026-09-25', 'Orphan bank scroll remittance of Rs 32,000 (BRN-99999) without matching portal transaction record (RAT Category).', NULL, NULL, NULL, NULL, 0, NULL, :user_id, :user_id, 'ACTIVE'),
                (5, :org_id, :branch_id, 'EXC-2026-0005', 591, 'SLA_BREACH', 'Medium', 'Assigned', 'BANK', :user_id, '2026-09-23', 'Late remittance of Rs 250,000 for Excise licence fee (CH-EX-20001); 1 day delay in bank remittance beyond T+1 window.', NULL, NULL, NULL, NULL, 0, NULL, :user_id, :user_id, 'ACTIVE'),
                (6, :org_id, :branch_id, 'EXC-2026-0006', 594, 'CHEQUE_CLEARING_DELAY', 'Low', 'Resolved', 'DEPT', :user_id, '2026-09-18', 'Cheque instrument realization cleared with 2 days delay due to outstation clearing for DVAT payment Rs 94,000.', 'PERMISSIBLE_CLEARING_WINDOW', 'Instrument realized on 2026-09-12 and remitted on 2026-09-13 within banking rules.', :user_id, '2026-09-16 14:20:00+00', 0, NULL, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (exception_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_exception seeded (6 exceptions).")

        # ---------------------------------------------------------
        # 7. rev_exception_note
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_exception_note"))).scalar()
        if cnt == 0:
            print("Seeding rev_exception_note...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_exception_note
                (note_id, exception_id, action_type, note_text, attachment_metadata, created_by, organization_id, org_branch_id, updated_by, workflow_status)
                VALUES
                (1, 1, 'STATUS_UPDATE', 'HDFC Nodal officer notified regarding Rs 2,000 difference in scroll settlement.', '{"filename": "hdfc_diff_notice.pdf", "size_kb": 142}'::jsonb, :user_id, :org_id, :branch_id, :user_id, 'ACTIVE'),
                (2, 2, 'ESCALATION', 'Escalated to Lead PAO: unremitted tax payment of Rs 47,000 exceeds 3-day aging limit.', '{"escalation_level": 1, "target_role": "LEAD_PAO"}'::jsonb, :user_id, :org_id, :branch_id, :user_id, 'ACTIVE'),
                (3, 3, 'INVESTIGATION', 'SBI Branch confirmed duplicate transmission of scroll record BRN-10006. Reversal scroll requested.', NULL, :user_id, :org_id, :branch_id, :user_id, 'ACTIVE'),
                (4, 4, 'QUERY_ISSUED', 'Query forwarded to GSTN Division to trace taxpayer identity for challan CH-GST-99999.', NULL, :user_id, :org_id, :branch_id, :user_id, 'ACTIVE'),
                (5, 5, 'PENAL_COMPUTED', 'Penal interest computed at 12% p.a. for 1 day belated remittance (Rs 82.19). Included in Bank SLA claim.', NULL, :user_id, :org_id, :branch_id, :user_id, 'ACTIVE'),
                (6, 6, 'RESOLUTION', 'Resolution validated against PNB Clearing House schedule. Case closed.', NULL, :user_id, :org_id, :branch_id, :user_id, 'ACTIVE')
                ON CONFLICT (note_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_exception_note seeded (6 notes).")

        # ---------------------------------------------------------
        # 8. rev_exception_letter
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_exception_letter"))).scalar()
        if cnt == 0:
            print("Seeding rev_exception_letter...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_exception_letter
                (letter_id, letter_no, exception_id, recipient_type, recipient_name, recipient_address, letter_subject, letter_body, issued_date, issued_by, status, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 'LTR-EXC-2026-001', 1, 'AGENCY_BANK', 'HDFC Bank Nodal Operations', 'Secretariat Branch, Delhi', 'Discrepancy in GST Scroll Settlement CH-GST-10004', 'Dear Sir/Madam, During three-way reconciliation for 2026-09-11, an amount difference of Rs 2,000 was identified between portal collection and bank scroll. Kindly examine and submit rectified scroll within 48 hours.', '2026-09-15', :user_id, 'ISSUED', :org_id, :branch_id, :user_id, :user_id, 'ISSUED'),
                (2, 'LTR-EXC-2026-002', 2, 'AGENCY_BANK', 'SBI State Head Office', 'Main Branch, Civil Lines, Nagpur', 'Demand for Unremitted Tax Collection CH-GST-10005', 'Dear Sir/Madam, Portal collection of Rs 47,000 received on 2026-09-12 remains unremitted to Government Account. Please expedite immediate remittance along with penal interest as per SLA.', '2026-09-16', :user_id, 'ISSUED', :org_id, :branch_id, :user_id, :user_id, 'ISSUED'),
                (3, 'LTR-EXC-2026-003', 3, 'AGENCY_BANK', 'SBI Settlement Division', 'Main Branch, Civil Lines, Nagpur', 'Rectification and Reversal of Duplicate Scroll Entry CH-GST-10006', 'Dear Sir/Madam, Duplicate credit of Rs 15,000 was transmitted under scroll SBI-20260912-004. You are requested to pass debit reversal scroll in the subsequent clearing cycle.', '2026-09-16', :user_id, 'ISSUED', :org_id, :branch_id, :user_id, :user_id, 'ISSUED')
                ON CONFLICT (letter_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_exception_letter seeded (3 letters).")

        # ---------------------------------------------------------
        # 9, 10, 11: rev_penal_letter, rev_penal_bank_response, rev_penal_waiver
        # ---------------------------------------------------------
        p_claims = (await db.execute(text("SELECT claim_id, bank_id, penal_interest_computed FROM ifms_budget.rev_penal_claim ORDER BY claim_id"))).fetchall()
        if p_claims:
            c1_id, c1_bank, c1_amt = p_claims[0][0], p_claims[0][1], p_claims[0][2]
            c2_id, c2_bank, c2_amt = (p_claims[1][0], p_claims[1][1], p_claims[1][2]) if len(p_claims) > 1 else (c1_id, c1_bank, c1_amt)
            c3_id, c3_bank, c3_amt = (p_claims[2][0], p_claims[2][1], p_claims[2][2]) if len(p_claims) > 2 else (c1_id, c1_bank, c1_amt)

            # 9. rev_penal_letter
            cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_penal_letter"))).scalar()
            if cnt == 0:
                print("Seeding rev_penal_letter...")
                await db.execute(text("""
                    INSERT INTO ifms_budget.rev_penal_letter
                    (letter_id, letter_no, claim_id, bank_id, issued_date, total_demand_amount, letter_content, issued_by, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                    VALUES
                    (1, 'PLTR-2026-0001', :c1_id, :c1_bank, '2026-09-15', :c1_amt, 'Formal Demand Notice for penal interest on belated remittances under Revenue SLA Rules 2026.', :user_id, :org_id, :branch_id, :user_id, :user_id, 'ISSUED'),
                    (2, 'PLTR-2026-0002', :c2_id, :c2_bank, '2026-09-15', :c2_amt, 'Formal Demand Notice for penal interest on belated remittances under Revenue SLA Rules 2026.', :user_id, :org_id, :branch_id, :user_id, :user_id, 'ISSUED'),
                    (3, 'PLTR-2026-0003', :c3_id, :c3_bank, '2026-09-15', :c3_amt, 'Formal Demand Notice for penal interest on belated remittances under Revenue SLA Rules 2026.', :user_id, :org_id, :branch_id, :user_id, :user_id, 'ISSUED')
                    ON CONFLICT (letter_id) DO NOTHING;
                """), {
                    "c1_id": c1_id, "c1_bank": c1_bank, "c1_amt": c1_amt,
                    "c2_id": c2_id, "c2_bank": c2_bank, "c2_amt": c2_amt,
                    "c3_id": c3_id, "c3_bank": c3_bank, "c3_amt": c3_amt,
                    "org_id": org_id, "branch_id": branch_id, "user_id": user_id
                })
                await db.commit()
                print("  [OK] rev_penal_letter seeded (3 letters).")

            # 10. rev_penal_bank_response
            cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_penal_bank_response"))).scalar()
            if cnt == 0:
                print("Seeding rev_penal_bank_response...")
                await db.execute(text("""
                    INSERT INTO ifms_budget.rev_penal_bank_response
                    (response_id, claim_id, response_date, response_type, remitted_amount, bank_remarks, recorded_by, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                    VALUES
                    (1, :c1_id, '2026-09-16', 'PARTIAL_ACCEPTANCE', 50.00, 'Bank remitted Rs 50.00 via RBI RTGS Ref UTR-PENAL-01. Balance requested waiver on account of state holiday.', :user_id, :org_id, :branch_id, :user_id, :user_id, 'PROCESSED'),
                    (2, :c2_id, '2026-09-17', 'FULL_ACCEPTANCE', :c2_amt, 'Bank accepted liability and remitted full penal interest to Major Head 0040.', :user_id, :org_id, :branch_id, :user_id, :user_id, 'PROCESSED'),
                    (3, :c3_id, '2026-09-18', 'DISPUTED', 0.00, 'Bank submitted clarification disputing delay citing RBI clearing maintenance.', :user_id, :org_id, :branch_id, :user_id, :user_id, 'PROCESSED')
                    ON CONFLICT (response_id) DO NOTHING;
                """), {
                    "c1_id": c1_id, "c2_id": c2_id, "c2_amt": c2_amt, "c3_id": c3_id,
                    "org_id": org_id, "branch_id": branch_id, "user_id": user_id
                })
                await db.commit()
                print("  [OK] rev_penal_bank_response seeded (3 responses).")

            # 11. rev_penal_waiver
            cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_penal_waiver"))).scalar()
            if cnt == 0:
                print("Seeding rev_penal_waiver...")
                await db.execute(text("""
                    INSERT INTO ifms_budget.rev_penal_waiver
                    (waiver_id, claim_id, waived_amount, waiver_ground, sanction_order_ref, waiver_remarks, approved_by, approved_at, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                    VALUES
                    (1, :c1_id, 11.81, 'BANKING_HOLIDAY', 'SANCTION-REV-SLA-2026-089', 'Waiver granted for holiday cutoff delay under Rule 14(2) of State Treasury Code.', :user_id, NOW(), :org_id, :branch_id, :user_id, :user_id, 'APPROVED')
                    ON CONFLICT (waiver_id) DO NOTHING;
                """), {
                    "c1_id": c1_id, "org_id": org_id, "branch_id": branch_id, "user_id": user_id
                })
                await db.commit()
                print("  [OK] rev_penal_waiver seeded (1 waiver).")

        # ---------------------------------------------------------
        # 12. rev_devolution_rule
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_devolution_rule"))).scalar()
        if cnt == 0:
            print("Seeding rev_devolution_rule...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_devolution_rule
                (dev_rule_id, rule_code, local_body_id, source_id, receipt_head_id, share_basis, share_value, valid_from, valid_to, description, is_active, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 'DR-01', 1, 4, 37, 'PERCENTAGE', 10.00, '2026-04-01', '2027-03-31', '10% Statutory Share of Stamp & Registration Duty to Municipal Corporation A', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (2, 'DR-02', 2, 3, 42, 'PERCENTAGE', 5.00, '2026-04-01', '2027-03-31', '5% Devolution of Motor Vehicle Taxes to Municipal Corporation B', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (3, 'DR-03', 3, 6, 43, 'PERCENTAGE', 2.00, '2026-04-01', '2027-03-31', '2% Non-Tax Local Cess Devolution to District Panchayat C', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (4, 'DR-04', 1, 1, 36, 'PERCENTAGE', 15.00, '2026-04-01', '2027-03-31', '15% SGST Local Body Development Grant Allocation', true, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (dev_rule_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_devolution_rule seeded (4 rules).")

        # ---------------------------------------------------------
        # 13. rev_devolution_claim
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_devolution_claim"))).scalar()
        if cnt == 0:
            print("Seeding rev_devolution_claim...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_devolution_claim
                (claim_id, organization_id, org_branch_id, claim_no, local_body_id, source_id, receipt_head_id, dev_rule_id, period_from, period_to, eligible_collections, share_pct, computed_entitlement, claimed_amount, variance_amount, approved_amount, status, scrutiny_remarks, bill_no, advice_no, epay_ref_no, settled_at, created_by, updated_by, workflow_status)
                VALUES
                (1, :org_id, :branch_id, 'DEV-2026-0001', 1, 4, 37, 1, '2026-09-01', '2026-09-10', 170000.00, 10.00, 17000.00, 17000.00, 0.00, 17000.00, 'Approved', 'Verified against reconciled e-stamp duty collections for Period 1-10 Sep 2026.', 'BILL-DEV-2026-01', 'ADV-DEV-2026-01', 'EPAY-DEV-9001', '2026-09-16 11:00:00+00', :user_id, :user_id, 'ACTIVE'),
                (2, :org_id, :branch_id, 'DEV-2026-0002', 2, 3, 42, 2, '2026-09-01', '2026-09-10', 24000.00, 5.00, 1200.00, 1200.00, 0.00, 1200.00, 'Approved', 'Verified against motor vehicle taxes receipts for Period 1-10 Sep 2026.', 'BILL-DEV-2026-02', 'ADV-DEV-2026-02', 'EPAY-DEV-9002', '2026-09-16 11:15:00+00', :user_id, :user_id, 'ACTIVE'),
                (3, :org_id, :branch_id, 'DEV-2026-0003', 3, 6, 43, 3, '2026-09-01', '2026-09-15', 26200.00, 2.00, 524.00, 550.00, 26.00, 524.00, 'Claim Received', 'Minor variance of Rs 26.00 observed; under PAO verification.', NULL, NULL, NULL, NULL, :user_id, :user_id, 'ACTIVE'),
                (4, :org_id, :branch_id, 'DEV-2026-0004', 1, 1, 36, 4, '2026-09-11', '2026-09-15', 353500.00, 15.00, 53025.00, 53025.00, 0.00, 0.00, 'Claim Received', 'Initial submission received from Municipal Corporation A.', NULL, NULL, NULL, NULL, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (claim_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_devolution_claim seeded (4 claims).")

        # ---------------------------------------------------------
        # 14. rev_devolution_computation
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_devolution_computation"))).scalar()
        if cnt == 0:
            print("Seeding rev_devolution_computation...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_devolution_computation
                (comp_id, organization_id, org_branch_id, claim_id, recon_id, receipt_date, receipt_amount, share_pct, entitled_share, created_by, updated_by, workflow_status)
                VALUES
                (1, :org_id, :branch_id, 1, 593, '2026-09-10', 60000.00, 10.00, 6000.00, :user_id, :user_id, 'COMPUTED'),
                (2, :org_id, :branch_id, 1, 600, '2026-09-11', 110000.00, 10.00, 11000.00, :user_id, :user_id, 'COMPUTED'),
                (3, :org_id, :branch_id, 2, 592, '2026-09-10', 4500.00, 5.00, 225.00, :user_id, :user_id, 'COMPUTED'),
                (4, :org_id, :branch_id, 2, 599, '2026-09-11', 8500.00, 5.00, 425.00, :user_id, :user_id, 'COMPUTED'),
                (5, :org_id, :branch_id, 2, 603, '2026-09-12', 11000.00, 5.00, 550.00, :user_id, :user_id, 'COMPUTED'),
                (6, :org_id, :branch_id, 3, 595, '2026-09-10', 1200.00, 2.00, 24.00, :user_id, :user_id, 'COMPUTED'),
                (7, :org_id, :branch_id, 3, 601, '2026-09-11', 25000.00, 2.00, 500.00, :user_id, :user_id, 'COMPUTED')
                ON CONFLICT (comp_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_devolution_computation seeded (7 line items).")

        # ---------------------------------------------------------
        # 15. rev_devolution_advice
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_devolution_advice"))).scalar()
        if cnt == 0:
            print("Seeding rev_devolution_advice...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_devolution_advice
                (advice_id, organization_id, org_branch_id, advice_no, claim_id, local_body_id, advice_date, approved_amount, bank_account_no, ifsc_code, epay_ref_no, debit_head_id, signed_by, created_by, updated_by, workflow_status)
                VALUES
                (1, :org_id, :branch_id, 'ADV-DEV-2026-01', 1, 1, '2026-09-16', 17000.00, 'XXXX4501', 'SBIN0001001', 'EPAY-DEV-9001', 37, :user_id, :user_id, :user_id, 'SIGNED'),
                (2, :org_id, :branch_id, 'ADV-DEV-2026-02', 2, 2, '2026-09-16', 1200.00, 'XXXX4502', 'HDFC0000123', 'EPAY-DEV-9002', 42, :user_id, :user_id, :user_id, 'SIGNED')
                ON CONFLICT (advice_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_devolution_advice seeded (2 advices).")

        # ---------------------------------------------------------
        # 16. account_voucher
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.account_voucher"))).scalar()
        if cnt == 0:
            print("Seeding account_voucher...")
            await db.execute(text("""
                INSERT INTO ifms_budget.account_voucher
                (voucher_id, sr_no, voucher_no, voucher_type, voucher_date, financial_year, pao_code, amount, debit_coa_id, credit_coa_id, department_id, recon_id, narration, status, prepared_by, checker_user_id, checker_remarks, approved_at, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 1, 'VR-2026-0001', 'REVENUE_RECEIPT', '2026-09-15', '2026-27', 'PAO21', 125000.00, 44, 36, 15, 589, 'Revenue receipt booking for GST collection from ABC Traders (CH-GST-10001)', 'Approved', :user_id, :user_id, 'Reconciled & Verified', NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (2, 2, 'VR-2026-0002', 'REVENUE_RECEIPT', '2026-09-15', '2026-27', 'PAO10', 250000.00, 44, 40, 16, 591, 'Revenue receipt booking for State Excise Licence fee Royal Beverages (CH-EX-20001)', 'Approved', :user_id, :user_id, 'Reconciled & Verified', NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (3, 3, 'VR-2026-0003', 'REVENUE_RECEIPT', '2026-09-15', '2026-27', 'PAO12', 60000.00, 44, 37, 17, 593, 'Revenue receipt booking for Non-Judicial Stamp duty Anita Sharma (CH-ST-40001)', 'Approved', :user_id, :user_id, 'Reconciled & Verified', NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (4, 4, 'VR-2026-0004', 'REVENUE_RECEIPT', '2026-09-15', '2026-27', 'PAO06', 94000.00, 44, 36, 18, 594, 'Revenue receipt booking for DVAT payment Classic Enterprises (CH-DV-50001)', 'Approved', :user_id, :user_id, 'Reconciled & Verified', NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (5, 5, 'VR-2026-0005', 'REVENUE_RECEIPT', '2026-09-15', '2026-27', 'PAO11', 4500.00, 44, 42, 4, 592, 'Revenue receipt booking for Transport registration fee Ramesh Kumar (CH-TR-30001)', 'Draft', :user_id, NULL, NULL, NULL, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (6, 6, 'VR-2026-0006', 'REVENUE_RECEIPT', '2026-09-15', '2026-27', 'PAO12', 110000.00, 44, 37, 17, 600, 'Revenue receipt booking for Registration Stamp duty Sanjay Verma (CH-ST-40002)', 'Approved', :user_id, :user_id, 'Reconciled & Verified', NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (voucher_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] account_voucher seeded (6 vouchers).")

        # ---------------------------------------------------------
        # 18. rev_refund_case
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_refund_case"))).scalar()
        if cnt == 0:
            print("Seeding rev_refund_case...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_refund_case
                (refund_id, case_no, refund_type, applicant_name, applicant_id_proof, applicant_bank_acc, applicant_ifsc, original_challan_no, recon_id, reconciled_original_amount, claimed_amount, refundable_amount, is_amount_override, override_reason, e_stamp_cert_no, court_order_no, current_stage, stage_name, pending_role, status, refund_bill_no, bill_prepared_by, bill_prepared_at, pao_approved_by, pao_approved_at, pao_remarks, epay_ref_no, epay_instructed_at, paid_at, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 'REF-NJ-2026-0001', 'NON_JUDICIAL_STAMP', 'Anita Sharma', 'PAN-AABCA1111A', 'XXXX1234', 'SBIN0001001', 'CH-ST-40001', 593, 60000.00, 60000.00, 60000.00, false, NULL, 'ESTAMP-1000001', NULL, 4, 'E-Payment Disbursed', 'DISBURSED', 'Paid', 'REF-BILL-2026-01', :user_id, NOW(), :user_id, NOW(), 'All statutory verifications completed successfully.', 'EPAY-REF-5001', NOW(), NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (2, 'REF-JS-2026-0001', 'JUDICIAL_STAMP', 'Rajesh Gupta', 'PAN-ABCDE1234F', 'XXXX5678', 'HDFC0000123', 'CH-JS-70001', NULL, 25000.00, 25000.00, 25000.00, false, NULL, NULL, 'COURT-ORDER-2026-778', 2, 'Court Certificate Verification', 'PAO_MAKER', 'Under Verification', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (3, 'REF-NJ-2026-0002', 'NON_JUDICIAL_STAMP', 'Priya Deshmukh', 'PAN-AACPD3333C', 'XXXX9876', 'ICIC0000456', 'CH-ST-99990', NULL, 15000.00, 15000.00, 15000.00, false, NULL, 'ESTAMP-9999999', NULL, 1, 'Application Submission', 'DDO', 'Submitted', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (4, 'REF-NJ-2026-0003', 'NON_JUDICIAL_STAMP', 'Delta Manufacturing', 'GSTIN27LMNOP4567Q1Z8', 'XXXX2244', 'SBIN0001001', 'CH-GST-10003', 596, 150000.00, 50000.00, 50000.00, false, NULL, 'ESTAMP-5544332', NULL, 3, 'PAO Approval & Sanction', 'PAO_CHECKER', 'Approved', 'REF-BILL-2026-02', :user_id, NOW(), NULL, NULL, 'Verified excess input credit against assessment order.', NULL, NULL, NULL, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (refund_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_refund_case seeded (4 cases).")

        # ---------------------------------------------------------
        # 19. rev_refund_verification
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_refund_verification"))).scalar()
        if cnt == 0:
            print("Seeding rev_refund_verification...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_refund_verification
                (verification_id, refund_id, verification_type, verification_result, authority_name, verification_remarks, verified_by, verified_at, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 1, 'CHALLAN_RECONCILIATION', 'Valid', 'IFMS 3-Way Engine', 'Original challan CH-ST-40001 verified against RBI luggage credit in recon record #593.', :user_id, NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (2, 1, 'NON_UTILISATION_CERTIFICATE', 'Valid', 'SHCIL StockHolding e-Stamping Portal', 'Certificate ESTAMP-1000001 verified as unused and locked against duplicate claims.', :user_id, NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (3, 2, 'COURT_CERTIFICATE_VERIFICATION', 'Partially Valid', 'High Court Registry', 'Certified copy of Court Order 2026-778 under verification with Legal Cell.', :user_id, NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (4, 4, 'ASSESSMENT_ORDER_VERIFICATION', 'Valid', 'State Tax Department Division IV', 'Excess tax payment refund order validated with GSTN Portal records.', :user_id, NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (verification_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_refund_verification seeded (4 verification records).")

        # ---------------------------------------------------------
        # 20. rev_refund_bill
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_refund_bill"))).scalar()
        if cnt == 0:
            print("Seeding rev_refund_bill...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_refund_bill
                (bill_id, bill_no, refund_id, department_id, ddo_id, pao_code, bill_amount, debit_head_id, status, prepared_by, prepared_at, approved_by, approved_at, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 'REF-BILL-2026-01', 1, 17, 1, 'PAO12', 60000.00, 37, 'PAID', :user_id, NOW(), :user_id, NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (2, 'REF-BILL-2026-02', 4, 15, 1, 'PAO21', 50000.00, 36, 'APPROVED', :user_id, NOW(), :user_id, NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (bill_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_refund_bill seeded (2 refund bills).")

        # ---------------------------------------------------------
        # 21. rev_recon_override
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_recon_override"))).scalar()
        if cnt == 0:
            print("Seeding rev_recon_override...")
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_recon_override
                (override_id, recon_id, original_machine_status, proposed_status, proposer_justification, proposed_by, proposed_at, decision_status, checker_user_id, checker_remarks, decided_at, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, 597, 'Mismatch', 'Matched With Adjustment', 'Bank confirmed receipt of Rs 80k base tax + Rs 2k late fee in subsequent luggage scroll.', :user_id, NOW(), 'APPROVED', :user_id, 'Approved as per Treasury Rule 45 after verifying bank rectification certificate.', NOW(), :org_id, :branch_id, :user_id, :user_id, 'ACTIVE'),
                (2, 604, 'Duplicate', 'Flagged For Bank Reversal', 'Duplicate entry in bank scroll batch 69 identified by PAO; reversal demanded.', :user_id, NOW(), 'PENDING_APPROVAL', NULL, NULL, NULL, :org_id, :branch_id, :user_id, :user_id, 'ACTIVE')
                ON CONFLICT (override_id) DO NOTHING;
            """), {"org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_recon_override seeded (2 override records).")

        # ---------------------------------------------------------
        # 22. rev_upload_rejected_row
        # ---------------------------------------------------------
        cnt = (await db.execute(text("SELECT count(*) FROM ifms_budget.rev_upload_rejected_row"))).scalar()
        if cnt == 0:
            print("Seeding rev_upload_rejected_row...")
            p_res = await db.execute(text("SELECT batch_id FROM ifms_budget.rev_upload_batch WHERE batch_type = 'PORTAL' ORDER BY batch_id DESC LIMIT 1"))
            p_bid = p_res.scalar() or 68
            await db.execute(text("""
                INSERT INTO ifms_budget.rev_upload_rejected_row
                (rejection_id, batch_id, batch_type, source_filename, file_row_number, raw_csv_row, failure_reasons, organization_id, org_branch_id, created_by, updated_by, workflow_status)
                VALUES
                (1, :p_bid, 'PORTAL', 'sample_invalid.csv', 1, 'GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-001,CH-GST-BAD-001,CPIN-BAD-001,CIN-BAD-001,GSTIN27BAD0001B1Z1,Invalid Amount Pvt Ltd,2026-09-12,2026-09-12,NETBANKING,ABC,0040-00-102-01-00-01,Invalid amount test,0.00,PAID', ARRAY['Invalid numeric amount: ABC'], :org_id, :branch_id, :user_id, :user_id, 'REJECTED'),
                (2, :p_bid, 'PORTAL', 'sample_invalid.csv', 2, 'GSTN,GST,TT,PAO21,DDO-TT-001,,CH-GST-BAD-002,CPIN-BAD-002,CIN-BAD-002,GSTIN27BAD0002B1Z1,Missing Portal Transaction,2026-09-12,2026-09-12,UPI,1000.00,0040-00-102-01-00-01,Missing ID test,0.00,PAID', ARRAY['Missing required field: portal_transaction_id'], :org_id, :branch_id, :user_id, :user_id, 'REJECTED'),
                (3, :p_bid, 'PORTAL', 'sample_invalid.csv', 3, 'UNKNOWN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-003,CH-GST-BAD-003,CPIN-BAD-003,CIN-BAD-003,GSTIN27BAD0003B1Z1,Unknown Portal,2026-09-12,2026-09-12,NETBANKING,2000.00,0040-00-102-01-00-01,Invalid portal test,0.00,PAID', ARRAY['Unrecognized revenue portal: UNKNOWN'], :org_id, :branch_id, :user_id, :user_id, 'REJECTED'),
                (4, :p_bid, 'PORTAL', 'sample_invalid.csv', 4, 'GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-004,CH-GST-BAD-004,CPIN-BAD-004,CIN-BAD-004,GSTIN27BAD0004B1Z1,Invalid Date,2026-99-99,2026-09-12,NETBANKING,3000.00,0040-00-102-01-00-01,Invalid date test,0.00,PAID', ARRAY['Invalid payment date format: 2026-99-99'], :org_id, :branch_id, :user_id, :user_id, 'REJECTED')
                ON CONFLICT (rejection_id) DO NOTHING;
            """), {"p_bid": p_bid, "org_id": org_id, "branch_id": branch_id, "user_id": user_id})
            await db.commit()
            print("  [OK] rev_upload_rejected_row seeded (4 rejected rows).")

    print("\n================================================================================")
    print(" ALL 22 EMPTY TABLES SEEDING COMPLETED SUCCESSFULLY!")
    print("================================================================================")

if __name__ == "__main__":
    asyncio.run(seed_all_empty_tables())
