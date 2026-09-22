import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

TABLES = [
    "agency_bank",
    "bank_branch",
    "receipt_staging",
    "treasury_expenditure_staging",
    "rev_agency_bank_scroll_staging",
    "rev_exception",
    "rev_exception_note",
    "rev_exception_letter",
    "rev_penal_letter",
    "rev_penal_bank_response",
    "rev_penal_waiver",
    "rev_devolution_rule"
]

async def check():
    async with AsyncSessionLocal() as db:
        for t in TABLES:
            res = await db.execute(text(f"""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_schema = 'ifms_budget' AND table_name = '{t}'
                ORDER BY ordinal_position;
            """))
            cols = [f"{r[0]} ({r[1]}, null={r[2]})" for r in res.fetchall()]
            print(f"=== {t} ===")
            print("  " + ", ".join(cols))

if __name__ == "__main__":
    asyncio.run(check())
