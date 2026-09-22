import psycopg2
import json

conn = psycopg2.connect(dbname='ifms_budget', user='ifms_budget', password='ifms_budget', host='127.0.0.1', port=5432)
cur = conn.cursor()

# 1. Get all tables in ifms_budget
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'ifms_budget' AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = [r[0] for r in cur.fetchall()]

# 2. Get all foreign keys in ifms_budget
cur.execute("""
    SELECT
        tc.table_name, 
        kcu.column_name, 
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name,
        tc.constraint_name
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='ifms_budget';
""")
fks = cur.fetchall()
fk_map = {}
for t, col, ft, fcol, cname in fks:
    fk_map.setdefault(t, {})[col] = (ft, fcol, cname)

# 3. Get all columns in ifms_budget
cur.execute("""
    SELECT table_name, column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'ifms_budget'
    ORDER BY table_name, ordinal_position;
""")
cols = cur.fetchall()

table_cols = {}
for t, col, dt, null in cols:
    table_cols.setdefault(t, []).append((col, dt, null))

# Identify newly added columns or key columns across tables:
target_cols = [
    'organization_id', 'org_branch_id', 'branch_id', 'created_by', 'updated_by', 
    'workflow_status', 'department_id', 'scheme_id', 'project_id', 'coa_id', 
    'budget_head_id', 'office_id', 'pao_code', 'bank_id', 'recon_id', 'claim_id',
    'voucher_id', 'batch_id', 'refund_id', 'exception_id', 'local_body_id'
]

print("================================================================================")
print(" 1. Target Columns & Missing FKs in ifms_budget")
print("================================================================================")
missing_fks = []
for t in sorted(table_cols.keys()):
    c_list = table_cols[t]
    for col, dt, null in c_list:
        if col in target_cols:
            has_fk = col in fk_map.get(t, {})
            fk_info = fk_map.get(t, {}).get(col, None)
            if not has_fk:
                missing_fks.append((t, col, dt, null))
                # print(f"  [MISSING FK] {t}.{col} ({dt}, nullable={null})")

print(f"Total target column occurrences without explicit FK constraint: {len(missing_fks)}\n")
for t, col, dt, null in missing_fks:
    print(f"  - {t}.{col} ({dt}, nullable={null})")

print("\n================================================================================")
print(" 2. Detailed Inspection of 'rev_' Tables Columns & Links")
print("================================================================================")
rev_tables = [t for t in tables if t.startswith('rev_') or t in ('agency_bank', 'bank_branch')]
for rt in sorted(rev_tables):
    print(f"\nTABLE: ifms_budget.{rt}")
    for col, dt, null in table_cols.get(rt, []):
        fk = fk_map.get(rt, {}).get(col, None)
        fk_str = f"--> {fk[0]}.{fk[1]} ({fk[2]})" if fk else "NO FK CONSTRAINT"
        print(f"  - {col} [{dt}, null={null}]: {fk_str}")

print("\n================================================================================")
print(" 3. Check for Orphaned Values on unlinked target columns")
print("================================================================================")
for t, col, dt, null in missing_fks:
    # Check what table this could logically point to
    target_table = None
    target_pk = None
    if col == 'organization_id':
        target_table, target_pk = 'organization', 'organization_id'
    elif col in ('org_branch_id', 'branch_id'):
        target_table, target_pk = 'branch', 'branch_id'
    elif col in ('created_by', 'updated_by'):
        target_table, target_pk = 'app_user', 'user_id'
    elif col == 'department_id':
        target_table, target_pk = 'department', 'department_id'
    elif col == 'scheme_id':
        target_table, target_pk = 'scheme', 'scheme_id'
    elif col == 'project_id':
        target_table, target_pk = 'project', 'project_id'
    elif col == 'local_body_id':
        target_table, target_pk = 'rev_local_body', 'local_body_id'
    elif col == 'bank_id':
        target_table, target_pk = 'agency_bank', 'bank_id'
    elif col == 'recon_id':
        target_table, target_pk = 'rev_recon_result', 'recon_id'
    elif col == 'exception_id':
        target_table, target_pk = 'rev_exception', 'exception_id'
    elif col == 'claim_id':
        # could be rev_penal_claim or rev_devolution_claim
        if 'penal' in t:
            target_table, target_pk = 'rev_penal_claim', 'claim_id'
        elif 'devolution' in t:
            target_table, target_pk = 'rev_devolution_claim', 'claim_id'
    elif col == 'batch_id':
        target_table, target_pk = 'rev_upload_batch', 'batch_id'
    elif col == 'refund_id':
        target_table, target_pk = 'rev_refund_case', 'refund_id'
    elif col == 'voucher_id':
        target_table, target_pk = 'rev_receipt_voucher', 'voucher_id'

    if target_table:
        # Check if there are values in t.col not in target_table.target_pk
        try:
            cur.execute(f"""
                SELECT count(*) 
                FROM ifms_budget.{t} src
                WHERE src.{col} IS NOT NULL 
                  AND NOT EXISTS (
                      SELECT 1 FROM ifms_budget.{target_table} tgt 
                      WHERE tgt.{target_pk} = src.{col}
                  );
            """)
            orphan_count = cur.fetchone()[0]
            print(f"  Checking {t}.{col} -> {target_table}.{target_pk}: {orphan_count} orphans found.")
        except Exception as e:
            conn.rollback()
            print(f"  Error checking {t}.{col}: {e}")

conn.close()
