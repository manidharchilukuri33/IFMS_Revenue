import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check_fk_values():
    async with AsyncSessionLocal() as db:
        print("=== app_user ===")
        users = await db.execute(text("SELECT * FROM ifms_budget.app_user LIMIT 3"))
        for u in users.mappings().fetchall():
            print(f"  {dict(u)}")

        print("\n=== organization ===")
        orgs = await db.execute(text("SELECT * FROM ifms_budget.organization"))
        for o in orgs.mappings().fetchall():
            print(f"  {dict(o)}")

        print("\n=== branch ===")
        branches = await db.execute(text("SELECT * FROM ifms_budget.branch"))
        for b in branches.mappings().fetchall():
            print(f"  {dict(b)}")

        print("\n=== department ===")
        depts = await db.execute(text("SELECT * FROM ifms_budget.department LIMIT 5"))
        for d in depts.mappings().fetchall():
            print(f"  {dict(d)}")

        print("\n=== ddo ===")
        ddos = await db.execute(text("SELECT * FROM ifms_budget.ddo LIMIT 5"))
        for dd in ddos.mappings().fetchall():
            print(f"  {dict(dd)}")

        print("\n=== chart_of_account ===")
        coas = await db.execute(text("SELECT coa_id, coa_code, account_nature FROM ifms_budget.chart_of_account LIMIT 10"))
        for c in coas.mappings().fetchall():
            print(f"  {dict(c)}")

        print("\n=== rev_revenue_source ===")
        srcs = await db.execute(text("SELECT * FROM ifms_budget.rev_revenue_source"))
        for s in srcs.mappings().fetchall():
            print(f"  {dict(s)}")

if __name__ == "__main__":
    asyncio.run(check_fk_values())
