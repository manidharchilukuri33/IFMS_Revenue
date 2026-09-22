import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        print("=== rev_upload_batch ===")
        batches = await db.execute(text("SELECT * FROM ifms_budget.rev_upload_batch"))
        for b in batches.mappings().fetchall():
            print(f"  {b}")
            
        print("\n=== rev_recon_result (sample 5) ===")
        recons = await db.execute(text("SELECT recon_id, recon_status, match_type, portal_challan_no, bank_challan_no, matched_amount FROM ifms_budget.rev_recon_result LIMIT 5"))
        for r in recons.mappings().fetchall():
            print(f"  {r}")
            
        print("\n=== rev_penal_claim ===")
        claims = await db.execute(text("SELECT claim_id, claim_no, bank_code, net_penal_payable, status FROM ifms_budget.rev_penal_claim"))
        for c in claims.mappings().fetchall():
            print(f"  {c}")

        print("\n=== rev_local_body ===")
        lbs = await db.execute(text("SELECT * FROM ifms_budget.rev_local_body"))
        for lb in lbs.mappings().fetchall():
            print(f"  {lb}")

if __name__ == "__main__":
    asyncio.run(check())
