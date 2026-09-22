import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("""
            SELECT recon_id, challan_no, status, match_type, portal_total, bank_total, rbi_total, receipt_head, pao_code, payer_name
            FROM ifms_budget.rev_recon_result
            ORDER BY recon_id;
        """))
        for r in res.mappings().fetchall():
            print(dict(r))

if __name__ == "__main__":
    asyncio.run(check())
