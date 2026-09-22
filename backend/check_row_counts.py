import asyncio
from app.core.database import async_engine
from sqlalchemy import text

async def main():
    async with async_engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='ifms_budget' AND table_type='BASE TABLE'
            ORDER BY table_name;
        """))
        tables = [r[0] for r in res.fetchall()]
        print("TABLE ROW COUNTS IN ifms_budget:")
        empty_tables = []
        for t in tables:
            try:
                cnt_res = await conn.execute(text(f'SELECT count(*) FROM ifms_budget."{t}"'))
                cnt = cnt_res.scalar()
                print(f"{t}: {cnt} rows")
                if cnt == 0:
                    empty_tables.append(t)
            except Exception as e:
                print(f"{t}: ERROR ({e})")
        print("\nTOTAL EMPTY TABLES:", len(empty_tables))
        print("EMPTY TABLES LIST:", empty_tables)

asyncio.run(main())
