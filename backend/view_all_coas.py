import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT coa_id, coa_code, account_nature FROM ifms_budget.chart_of_account ORDER BY coa_id"))
        for r in res.mappings().fetchall():
            print(dict(r))

if __name__ == "__main__":
    asyncio.run(check())
