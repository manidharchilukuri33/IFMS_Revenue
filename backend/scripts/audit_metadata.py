import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect(host='10.200.10.167', port=5432, user='ifms_budget', password='ifms_budget', database='ifms_budget')
    
    # 1. Inspect all tables and column details
    tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'ifms_budget' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    tables = await conn.fetch(tables_query)
    table_names = [t['table_name'] for t in tables]
    
    schema_info = {}
    for t in table_names:
        cols = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'ifms_budget' AND table_name = $1
            ORDER BY ordinal_position;
        """, t)
        schema_info[t] = [dict(c) for c in cols]
        
    with open('backend/scripts/db_tables_columns.json', 'w', encoding='utf-8') as f:
        json.dump(schema_info, f, indent=2, default=str)
    print(f"Dumped {len(schema_info)} tables to backend/scripts/db_tables_columns.json")
    
    # 2. Inspect foreign keys
    fk_query = """
        SELECT
            tc.table_name, kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'ifms_budget';
    """
    fks = await conn.fetch(fk_query)
    print(f"Found {len(fks)} Foreign Keys in ifms_budget")
    with open('backend/scripts/db_foreign_keys.json', 'w', encoding='utf-8') as f:
        json.dump([dict(fk) for fk in fks], f, indent=2)

    # 3. Inspect all triggers and routine definitions
    trig_query = """
        SELECT event_object_table, trigger_name, event_manipulation, action_statement, action_timing
        FROM information_schema.triggers
        WHERE trigger_schema = 'ifms_budget'
        ORDER BY event_object_table, trigger_name;
    """
    triggers = await conn.fetch(trig_query)
    with open('backend/scripts/db_triggers.json', 'w', encoding='utf-8') as f:
        json.dump([dict(tr) for tr in triggers], f, indent=2)

    # 4. Routine definitions
    routine_query = """
        SELECT p.proname, p.prokind, pg_get_functiondef(p.oid) as defn
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'ifms_budget'
        ORDER BY p.proname;
    """
    routines = await conn.fetch(routine_query)
    routines_data = {r['proname']: {'kind': r['prokind'], 'definition': r['defn']} for r in routines}
    with open('backend/scripts/db_routines.json', 'w', encoding='utf-8') as f:
        json.dump(routines_data, f, indent=2, default=str)
    print(f"Dumped {len(routines_data)} routines to backend/scripts/db_routines.json")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
