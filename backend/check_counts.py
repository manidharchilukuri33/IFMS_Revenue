import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'ifms_budget' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [r[0] for r in res.fetchall()]
        empty = []
        non_empty = []
        for t in tables:
            cnt_res = await db.execute(text(f'SELECT count(*) FROM ifms_budget."{t}"'))
            cnt = cnt_res.scalar()
            if cnt == 0:
                empty.append((t, cnt))
            else:
                non_empty.append((t, cnt))
        print(f"Total tables: {len(tables)}")
        print(f"\nEmpty tables ({len(empty)}):")
        for t, c in empty:
            print(f"  - {t}")
        print(f"\nPopulated tables ({len(non_empty)}):")
        for t, c in non_empty:
            print(f"  - {t}: {c}")

if __name__ == "__main__":
    asyncio.run(check())
