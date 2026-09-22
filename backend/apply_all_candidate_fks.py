import psycopg2

conn = psycopg2.connect(dbname='ifms_budget', user='ifms_budget', password='ifms_budget', host='127.0.0.1', port=5432)
cur = conn.cursor()

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'ifms_budget' AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = [r[0] for r in cur.fetchall()]

# Test adding FK constraints in a transaction and see if all succeed
print("Testing candidate Foreign Key constraints...")

candidate_fks = []

# 1. organization_id -> organization(organization_id)
# 2. org_branch_id / branch_id -> branch(branch_id)
# 3. created_by / updated_by -> app_user(user_id)

for t in tables:
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='ifms_budget' AND table_name='{t}';")
    cols = [r[0] for r in cur.fetchall()]
    
    if 'organization_id' in cols and t != 'organization':
        candidate_fks.append((t, 'organization_id', 'organization', 'organization_id', f'fk_{t}_org'))
    if 'org_branch_id' in cols:
        candidate_fks.append((t, 'org_branch_id', 'branch', 'branch_id', f'fk_{t}_org_branch'))
    if 'branch_id' in cols and t != 'branch':
        candidate_fks.append((t, 'branch_id', 'branch', 'branch_id', f'fk_{t}_branch'))
    if 'created_by' in cols:
        candidate_fks.append((t, 'created_by', 'app_user', 'user_id', f'fk_{t}_created_by'))
    if 'updated_by' in cols:
        candidate_fks.append((t, 'updated_by', 'app_user', 'user_id', f'fk_{t}_updated_by'))

# Specific rev_receipt_voucher candidate FKs
candidate_fks.extend([
    ('rev_receipt_voucher', 'department_id', 'department', 'department_id', 'fk_rev_receipt_voucher_dept'),
    ('rev_receipt_voucher', 'scheme_id', 'scheme', 'scheme_id', 'fk_rev_receipt_voucher_scheme'),
    ('rev_receipt_voucher', 'project_id', 'project', 'project_id', 'fk_rev_receipt_voucher_project'),
    ('rev_receipt_voucher', 'budget_head_id', 'chart_of_account', 'coa_id', 'fk_rev_receipt_voucher_bhead'),
    ('rev_receipt_voucher', 'coa_id', 'chart_of_account', 'coa_code', 'fk_rev_receipt_voucher_coa_code'),
])

success = []
failed = []

for t, col, ref_t, ref_col, cname in candidate_fks:
    # check if constraint already exists
    cur.execute(f"""
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_schema='ifms_budget' AND table_name='{t}' AND constraint_name='{cname}';
    """)
    if cur.fetchone():
        # print(f"  [EXISTS] {t}.{col} -> {ref_t}.{ref_col} ({cname})")
        continue

    # test adding constraint
    savepoint = f"sp_{t}_{col}"
    try:
        cur.execute(f"SAVEPOINT {savepoint};")
        cur.execute(f"""
            ALTER TABLE ifms_budget.{t}
            ADD CONSTRAINT {cname}
            FOREIGN KEY ({col}) REFERENCES ifms_budget.{ref_t}({ref_col});
        """)
        cur.execute(f"RELEASE SAVEPOINT {savepoint};")
        success.append((t, col, ref_t, ref_col, cname))
        print(f"  [SUCCESS] Added FK: {t}.{col} -> {ref_t}.{ref_col} ({cname})")
    except Exception as e:
        cur.execute(f"ROLLBACK TO SAVEPOINT {savepoint};")
        failed.append((t, col, ref_t, ref_col, cname, str(e).strip()))
        print(f"  [FAILED] {t}.{col} -> {ref_t}.{ref_col} ({cname}): {e}")

conn.commit()
print(f"\nSummary: {len(success)} new FKs created, {len(failed)} failed.")

conn.close()
