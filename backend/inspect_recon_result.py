import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'ifms_budget' AND table_name = 'rev_recon_result'
            ORDER BY ordinal_position;
        """))
        for r in res.fetchall():
            print(f"  {r[0]} ({r[1]})")

if __name__ == "__main__":
    asyncio.run(check())
