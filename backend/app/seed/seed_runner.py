import asyncio
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func

from app.core.database import AsyncSessionLocal
from app.models import (
    RevSystemConfig,
    RevSlaRule,
    RevDevolutionRule,
    RevLocalBody,
    RevAgencyBank,
    RevRevenueSource,
    ChartOfAccount,
    RevRefundCase,
    RevDevolutionClaim,
    RevUploadBatch,
    RevReconResult,
)
from app.services.upload_service import UploadService, SAMPLE_CSVS
from app.services.recon_engine import ReconEngine

async def seed_all():
    print("==================================================")
    print("Starting IFMS Revenue Database Seeder...")
    print("Target DB: ifms_budget / Schema: ifms_budget")
    print("==================================================")

    async with AsyncSessionLocal() as db:
        # 1. Seed System Config
        q = select(RevSystemConfig).where(RevSystemConfig.config_id == 1)
        res = await db.execute(q)
        cfg = res.scalar_one_or_none()
        if not cfg:
            cfg = RevSystemConfig(
                config_id=1,
                demo_business_date=date(2026, 9, 15),
                current_financial_year="2026-27",
                amount_tolerance=Decimal("0.01"),
                date_tolerance_days=2,
                default_penal_rate_pct=Decimal("12.00"),
                penal_day_basis=365,
                exception_escalation_days=3,
                updated_by=1
            )
            db.add(cfg)
            await db.commit()
        print("[OK] System Configuration verified/seeded.")

        # 2. Seed SLA Rules
        sla_rules = [
            ("SLA-ONLINE", "SLA for Online Receipts", "NETBANKING", 1, 0, Decimal("12.00"), "ACTUAL_365", "PAYMENT_DATE"),
            ("SLA-CASH", "SLA for Cash Collections", "CASH", 1, 0, Decimal("12.00"), "ACTUAL_365", "PAYMENT_DATE"),
            ("SLA-INSTR", "SLA for Cheque / Instruments", "CHEQUE", 1, 0, Decimal("12.00"), "ACTUAL_365", "REALISATION_DATE"),
        ]
        for code, name, pmode, days, grace, rate, basis, bdt in sla_rules:
            q = select(RevSlaRule).where(RevSlaRule.rule_code == code)
            res = await db.execute(q)
            if not res.scalar_one_or_none():
                rule = RevSlaRule(
                    rule_code=code,
                    rule_name=name,
                    payment_mode=pmode,
                    allowed_remittance_days=days,
                    grace_days=grace,
                    annual_penal_rate_pct=rate,
                    calculation_basis=basis,
                    base_date_type=bdt,
                    is_active=True,
                )
                db.add(rule)
        await db.commit()
        print("[OK] SLA Rules verified/seeded.")

        # 3. Seed Devolution Rules & Local Bodies
        local_bodies = [
            ("MC-A", "Municipal Corporation A", "MUNICIPAL_CORP", "SBIN0001001", "XXXX4501", "SBI Civil Lines Branch"),
            ("MC-B", "Municipal Corporation B", "MUNICIPAL_CORP", "HDFC0000123", "XXXX4502", "HDFC Secretariat Branch"),
            ("DLB-C", "District Local Body C", "DISTRICT_PANCHAYAT", "PUNB0005001", "XXXX4503", "PNB Tax Collection Branch"),
        ]
        lb_map = {}
        for code, name, btype, ifsc, acc, bname in local_bodies:
            q = select(RevLocalBody).where(RevLocalBody.local_body_code == code)
            res = await db.execute(q)
            lb = res.scalar_one_or_none()
            if not lb:
                lb = RevLocalBody(
                    local_body_code=code, local_body_name=name, body_type=btype,
                    ifsc_code=ifsc, bank_account_no=acc, bank_name=bname, is_active=True
                )
                db.add(lb)
                await db.flush()
            lb_map[code] = lb.local_body_id
        await db.commit()
        print("[OK] Local Bodies verified/seeded.")

        # Get chart of account IDs
        coa_res = await db.execute(select(ChartOfAccount).limit(10))
        coa_list = coa_res.scalars().all()
        coa_map = {c.coa_code: c.coa_id for c in coa_list}
        default_coa_id = coa_list[0].coa_id if coa_list else 1

        # Devolution rules
        dev_rules = [
            ("DR-01", lb_map.get("MC-A", 1), 4, coa_map.get("0030-00-102-01-00-01", default_coa_id), Decimal("10.00"), "10% of property registration"),
            ("DR-02", lb_map.get("MC-B", 1), 3, coa_map.get("0041-00-101-01-00-01", default_coa_id), Decimal("5.00"), "5% of transport levy"),
            ("DR-03", lb_map.get("DLB-C", 1), 6, coa_map.get("0070-60-800-01-00-01", default_coa_id), Decimal("2.00"), "2% of non-tax service fee"),
        ]
        for code, lb_id, src_id, head_id, val, desc_txt in dev_rules:
            q = select(RevDevolutionRule).where(RevDevolutionRule.rule_code == code)
            res = await db.execute(q)
            if not res.scalar_one_or_none():
                drule = RevDevolutionRule(
                    rule_code=code,
                    local_body_id=lb_id,
                    source_id=src_id,
                    receipt_head_id=head_id,
                    share_basis="PERCENTAGE",
                    share_value=val,
                    valid_from=date(2026, 4, 1),
                    valid_to=date(2027, 3, 31),
                    description=desc_txt,
                    is_active=True,
                )
                db.add(drule)
        await db.commit()
        print("[OK] Devolution Rules verified/seeded.")

        # 4. Upload & Approve Initial Batches (Portal, Bank, RBI)
        print("Checking baseline datasets in staging...")
        p_batch = (await db.execute(select(RevUploadBatch).where(RevUploadBatch.batch_type == "PORTAL").limit(1))).scalar_one_or_none()
        if not p_batch:
            await UploadService.load_sample_dataset(db, "portal", auto_approve=True, user_id=1)
        b_batch = (await db.execute(select(RevUploadBatch).where(RevUploadBatch.batch_type == "BANK_SCROLL").limit(1))).scalar_one_or_none()
        if not b_batch:
            await UploadService.load_sample_dataset(db, "bank", auto_approve=True, user_id=1)
        r_batch = (await db.execute(select(RevUploadBatch).where(RevUploadBatch.batch_type == "RBI_LUGGAGE").limit(1))).scalar_one_or_none()
        if not r_batch:
            await UploadService.load_sample_dataset(db, "rbi", auto_approve=True, user_id=1)
        print("[OK] Upload batches verified.")

        # 5. Execute 3-Way Reconciliation Engine
        recon_count = (await db.execute(select(func.count(RevReconResult.recon_id)))).scalar() or 0
        if recon_count == 0:
            print("Executing 3-Way Reconciliation Engine across loaded staging batches...")
            recon_summary = await ReconEngine.run_3way_reconciliation(db, business_date=date(2026, 9, 15), user_id=1)
            print(f"[OK] Reconciliation Complete: {recon_summary['matched_count']} matched, {recon_summary['exception_count']} exceptions logged.")
        else:
            print(f"[OK] Reconciliation results already present ({recon_count} records).")

        # 6. Seed Sample Refund Cases
        refund_cases = [
            ("REF-NJ-2026-0001", "NON_JUDICIAL_STAMP", "Anita Sharma", "PAN-AABCA1111A", "XXXX1234", "SBIN0001001", "CH-ST-40001", Decimal("60000.00"), "ESTAMP-1000001", None, 1, "Application Submission", "DDO"),
            ("REF-JS-2026-0001", "JUDICIAL_STAMP", "Rajesh Gupta", "PAN-ABCDE1234F", "XXXX5678", "HDFC0000123", "CH-JS-70001", Decimal("25000.00"), None, "COURT-ORDER-2026-778", 2, "Court Certificate Verification", "PAO_MAKER"),
            ("REF-NJ-2026-0002", "NON_JUDICIAL_STAMP", "Priya Deshmukh", "PAN-AACPD3333C", "XXXX9876", "ICIC0000456", "CH-ST-99990", Decimal("15000.00"), "ESTAMP-9999999", None, 1, "Application Submission", "DDO"),
        ]
        for cno, rtype, app_name, idp, bacc, ifsc, challan, amt, estamp, court, stg, sname, role in refund_cases:
            q = select(RevRefundCase).where(RevRefundCase.case_no == cno)
            res = await db.execute(q)
            if not res.scalar_one_or_none():
                rcase = RevRefundCase(
                    case_no=cno,
                    refund_type=rtype,
                    applicant_name=app_name,
                    applicant_id_proof=idp,
                    applicant_bank_acc=bacc,
                    applicant_ifsc=ifsc,
                    original_challan_no=challan,
                    reconciled_original_amount=amt,
                    claimed_amount=amt,
                    refundable_amount=amt,
                    is_amount_override=False,
                    e_stamp_cert_no=estamp,
                    court_order_no=court,
                    current_stage=stg,
                    stage_name=sname,
                    pending_role=role,
                    status="Submitted" if stg == 1 else "Under Verification",
                )
                db.add(rcase)
        await db.commit()
        print("[OK] Sample Refund Cases seeded.")

        # 7. Seed Sample Devolution Claims
        dev_claims = [
            ("DEV-2026-0001", lb_map.get("MC-A", 1), 4, coa_map.get("0030-00-102-01-00-01", default_coa_id), date(2026, 9, 1), date(2026, 9, 10), Decimal("170000.00"), Decimal("10.00"), Decimal("17000.00"), Decimal("17000.00"), "Claim Received"),
            ("DEV-2026-0002", lb_map.get("MC-B", 1), 3, coa_map.get("0041-00-101-01-00-01", default_coa_id), date(2026, 9, 1), date(2026, 9, 10), Decimal("24000.00"), Decimal("5.00"), Decimal("1200.00"), Decimal("1200.00"), "Claim Received"),
        ]
        for cno, lbid, sid, hid, pfrom, pto, elig, spct, ent, clm, st in dev_claims:
            q = select(RevDevolutionClaim).where(RevDevolutionClaim.claim_no == cno)
            res = await db.execute(q)
            if not res.scalar_one_or_none():
                dclaim = RevDevolutionClaim(
                    claim_no=cno,
                    local_body_id=lbid,
                    source_id=sid,
                    receipt_head_id=hid,
                    period_from=pfrom,
                    period_to=pto,
                    eligible_collections=elig,
                    share_pct=spct,
                    computed_entitlement=ent,
                    claimed_amount=clm,
                    variance_amount=clm - ent,
                    approved_amount=Decimal("0.00"),
                    status=st,
                )
                db.add(dclaim)
        await db.commit()
        print("[OK] Sample Devolution Claims seeded.")

    print("==================================================")
    print("Database seeding completed successfully!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(seed_all())
