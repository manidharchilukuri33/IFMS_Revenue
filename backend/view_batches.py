import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT * FROM ifms_budget.rev_upload_batch"))
        for b in res.mappings().fetchall():
            print(dict(b))

if __name__ == "__main__":
    asyncio.run(check())
