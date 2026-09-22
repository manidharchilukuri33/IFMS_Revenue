import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE n.nspname = 'ifms_budget' AND c.contype = 'c';
        """))
        for r in res.fetchall():
            print(f"{r[0]}: {r[1]}")

if __name__ == "__main__":
    asyncio.run(check())
