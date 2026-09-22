import asyncio
from app.core.database import async_engine
from sqlalchemy import text

async def check():
    async with async_engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conname LIKE 'ck_rev_%' OR conrelid = 'ifms_budget.rev_suspense_register'::regclass
        """))
        for r in res:
            print(f"{r[0]}: {r[1]}")

asyncio.run(check())
