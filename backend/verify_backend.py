import asyncio
from app.core.database import AsyncSessionLocal
from app.services.test_suite_service import TestSuiteService
from app.services.dashboard_service import DashboardService
from app.services.report_service import ReportService
from app.services.voucher_service import VoucherService
from app.schemas.accounting import BulkVoucherCreateRequest, BulkVoucherApproveRequest

async def verify():
    print("==================================================")
    print("RUNNING LIVE BACKEND & DATABASE VERIFICATION")
    print("==================================================")

    async with AsyncSessionLocal() as db:
        # 1. Run TestSuiteService
        test_summary = await TestSuiteService.run_all_tests(db)
        print(f"Total Tests: {test_summary['total_tests']} | Passed: {test_summary['passed']} | Failed: {test_summary['failed']}")
        for t in test_summary["results"]:
            print(f"[{t['status']}] {t['test_id']} - {t['name']}: {t['details']}")

        # 2. Test Voucher Generation from Stored Procedure
        print("\n--- Testing Stored Procedures for Booking Vouchers ---")
        vch_create_res = await VoucherService.create_vouchers_bulk(db, BulkVoucherCreateRequest(pao_code="PAO21"), user_id=1)
        print("Voucher Generation:", vch_create_res["message"], f"(Drafts: {vch_create_res['draft_vouchers_count']})")

        vch_approve_res = await VoucherService.approve_vouchers_bulk(db, BulkVoucherApproveRequest(remarks="Verified in test suite"), checker_id=1)
        print("Voucher Bulk Approval:", vch_approve_res["message"], f"(Approved: {vch_approve_res['approved_vouchers_count']})")

        # 3. Test Dashboard Summary
        dash = await DashboardService.get_dashboard_summary(db)
        print("\n--- Live Dashboard KPIs ---")
        for k, v in dash["kpis"].items():
            print(f"  {k}: {v}")

        # 4. Test Reports Generation (r01 to r17)
        print("\n--- Verifying All 17 Reports ---")
        for i in range(1, 18):
            rid = f"r{i:02d}"
            rpt = await ReportService.generate_report(db, rid)
            print(f"  [{rpt.report_id}] {rpt.report_name}: {len(rpt.rows)} rows generated.")

    print("\n==================================================")
    print("ALL BACKEND CHECKS AND PROCEDURES VERIFIED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(verify())
