import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

TABLES = [
    "agency_bank",
    "bank_branch",
    "receipt_staging",
    "treasury_expenditure_staging",
    "rev_agency_bank_scroll_staging"
]

async def inspect():
    async with AsyncSessionLocal() as db:
        for tbl in TABLES:
            print(f"\n==================== TABLE: {tbl} ====================")
            cols = await db.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'ifms_budget' AND table_name = '{tbl}'
                ORDER BY ordinal_position;
            """))
            for c in cols.fetchall():
                print(f"  {c[0]} | {c[1]} | nullable={c[2]} | default={c[3]}")
                
            fks = await db.execute(text(f"""
                SELECT
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                  AND tc.table_schema = 'ifms_budget'
                  AND tc.table_name = '{tbl}';
            """))
            print("  --- Foreign Keys ---")
            for fk in fks.fetchall():
                print(f"  FK: {fk[0]} -> {fk[1]}({fk[2]})")

if __name__ == "__main__":
    asyncio.run(inspect())
