-- ======================================================================================
-- IFMS REVENUE & RECONCILIATION MODULE - DATABASE SCHEMA UPDATE SCRIPT
-- ======================================================================================
-- Target Database: ifms_budget
-- Target Schema:   ifms_budget
-- Compatible with: PostgreSQL 14 / 15 / 16 / 17 (DBeaver / psql)
--
-- Summary of Changes:
--   1. Adds Organization, Branch & Audit Columns to all tables prefixed with 'rev_':
--      - organization_id int8 NOT NULL REFERENCES ifms_budget.organization(organization_id)
--      - org_branch_id   int8 NOT NULL REFERENCES ifms_budget.branch(branch_id)
--      - created_by      bigint REFERENCES ifms_budget.app_user(user_id)
--      - updated_by      bigint REFERENCES ifms_budget.app_user(user_id)
--      - workflow_status varchar(30)
--
--   2. Adds 'workflow_status' (varchar 30) across all tables in ifms_budget schema.
--
--   3. Updates 'ifms_budget.rev_receipt_voucher':
--      - Drops 'total_amount'
--      - Adds 'debit_amount', 'credit_amount' (numeric(15,2))
--      - Adds 'coa_code' (references ifms_budget.chart_of_account(coa_code))
--      - Adds 'major_code', 'minor_code'
--      - Adds 'department_id' (references ifms_budget.department(department_id))
--      - Adds 'office_id', 'transaction_code', 'scheme_id', 'project_id', 'budget_head_id'
--      - Adds 'workflow_status' varchar(30)
-- ======================================================================================

BEGIN;

SET search_path TO ifms_budget, public;

-- ======================================================================================
-- SECTION 1: SPECIFIC SCHEMA UPDATES FOR 'rev_receipt_voucher'
-- ======================================================================================

-- 1.1 Drop total_amount column
ALTER TABLE ifms_budget.rev_receipt_voucher 
DROP COLUMN IF EXISTS total_amount CASCADE;

-- 1.2 Add debit_amount, credit_amount, and accounting / budget dimensions
ALTER TABLE ifms_budget.rev_receipt_voucher 
ADD COLUMN IF NOT EXISTS debit_amount numeric(15,2) DEFAULT 0.00 NOT NULL,
ADD COLUMN IF NOT EXISTS credit_amount numeric(15,2) DEFAULT 0.00 NOT NULL,
ADD COLUMN IF NOT EXISTS coa_code character varying(50),
ADD COLUMN IF NOT EXISTS major_code character varying(10),
ADD COLUMN IF NOT EXISTS minor_code character varying(10),
ADD COLUMN IF NOT EXISTS department_id bigint,
ADD COLUMN IF NOT EXISTS office_id bigint,
ADD COLUMN IF NOT EXISTS transaction_code character varying(50),
ADD COLUMN IF NOT EXISTS scheme_id bigint,
ADD COLUMN IF NOT EXISTS project_id bigint,
ADD COLUMN IF NOT EXISTS budget_head_id bigint,
ADD COLUMN IF NOT EXISTS workflow_status character varying(30) DEFAULT 'DRAFT';

-- 1.3 Add foreign keys safely if target tables exist
DO $$
BEGIN
    -- FK for department_id
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rev_receipt_voucher_dept') THEN
        ALTER TABLE ifms_budget.rev_receipt_voucher
        ADD CONSTRAINT fk_rev_receipt_voucher_dept 
        FOREIGN KEY (department_id) REFERENCES ifms_budget.department(department_id);
    END IF;

    -- FK for scheme_id
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rev_receipt_voucher_scheme') THEN
        ALTER TABLE ifms_budget.rev_receipt_voucher
        ADD CONSTRAINT fk_rev_receipt_voucher_scheme 
        FOREIGN KEY (scheme_id) REFERENCES ifms_budget.scheme(scheme_id);
    END IF;

    -- FK for project_id
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rev_receipt_voucher_project') THEN
        ALTER TABLE ifms_budget.rev_receipt_voucher
        ADD CONSTRAINT fk_rev_receipt_voucher_project 
        FOREIGN KEY (project_id) REFERENCES ifms_budget.project(project_id);
    END IF;

    -- FK for coa_code
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rev_receipt_voucher_coa_code') THEN
        ALTER TABLE ifms_budget.rev_receipt_voucher
        ADD CONSTRAINT fk_rev_receipt_voucher_coa_code 
        FOREIGN KEY (coa_code) REFERENCES ifms_budget.chart_of_account(coa_code);
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Constraint notice: %', SQLERRM;
END $$;


-- ======================================================================================
-- SECTION 2: ADD ORG, BRANCH, AUDIT & WORKFLOW_STATUS TO ALL 'rev_%' TABLES
-- ======================================================================================

DO $$
DECLARE
    r RECORD;
    v_default_org_id bigint;
    v_default_branch_id bigint;
BEGIN
    -- Resolve fallback default IDs for NOT NULL safety on existing rows
    SELECT organization_id INTO v_default_org_id FROM ifms_budget.organization LIMIT 1;
    IF v_default_org_id IS NULL THEN v_default_org_id := 1; END IF;

    SELECT branch_id INTO v_default_branch_id FROM ifms_budget.branch LIMIT 1;
    IF v_default_branch_id IS NULL THEN v_default_branch_id := 1; END IF;

    -- Iterate over all revenue tables prefixed with 'rev_'
    FOR r IN (
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'ifms_budget' 
          AND table_type = 'BASE TABLE'
          AND table_name LIKE 'rev_%'
        ORDER BY table_name
    ) 
    LOOP
        -- 1. Add organization_id if not exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'ifms_budget' AND table_name = r.table_name AND column_name = 'organization_id'
        ) THEN
            EXECUTE format('ALTER TABLE ifms_budget.%I ADD COLUMN organization_id int8 DEFAULT %L NOT NULL', r.table_name, v_default_org_id);
            BEGIN
                EXECUTE format('ALTER TABLE ifms_budget.%I ADD CONSTRAINT fk_%s_org FOREIGN KEY (organization_id) REFERENCES ifms_budget.organization(organization_id)', r.table_name, r.table_name);
            EXCEPTION WHEN OTHERS THEN NULL;
            END;
        END IF;

        -- 2. Add org_branch_id if not exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'ifms_budget' AND table_name = r.table_name AND column_name = 'org_branch_id'
        ) THEN
            EXECUTE format('ALTER TABLE ifms_budget.%I ADD COLUMN org_branch_id int8 DEFAULT %L NOT NULL', r.table_name, v_default_branch_id);
            BEGIN
                EXECUTE format('ALTER TABLE ifms_budget.%I ADD CONSTRAINT fk_%s_branch FOREIGN KEY (org_branch_id) REFERENCES ifms_budget.branch(branch_id)', r.table_name, r.table_name);
            EXCEPTION WHEN OTHERS THEN NULL;
            END;
        END IF;

        -- 3. Add created_by if not exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'ifms_budget' AND table_name = r.table_name AND column_name = 'created_by'
        ) THEN
            EXECUTE format('ALTER TABLE ifms_budget.%I ADD COLUMN created_by bigint', r.table_name);
            BEGIN
                EXECUTE format('ALTER TABLE ifms_budget.%I ADD CONSTRAINT fk_%s_created_by FOREIGN KEY (created_by) REFERENCES ifms_budget.app_user(user_id)', r.table_name, r.table_name);
            EXCEPTION WHEN OTHERS THEN NULL;
            END;
        END IF;

        -- 4. Add updated_by if not exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'ifms_budget' AND table_name = r.table_name AND column_name = 'updated_by'
        ) THEN
            EXECUTE format('ALTER TABLE ifms_budget.%I ADD COLUMN updated_by bigint', r.table_name);
            BEGIN
                EXECUTE format('ALTER TABLE ifms_budget.%I ADD CONSTRAINT fk_%s_updated_by FOREIGN KEY (updated_by) REFERENCES ifms_budget.app_user(user_id)', r.table_name, r.table_name);
            EXCEPTION WHEN OTHERS THEN NULL;
            END;
        END IF;

        -- 5. Add workflow_status if not exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'ifms_budget' AND table_name = r.table_name AND column_name = 'workflow_status'
        ) THEN
            EXECUTE format('ALTER TABLE ifms_budget.%I ADD COLUMN workflow_status character varying(30) DEFAULT ''DRAFT''', r.table_name);
        END IF;

    END LOOP;
END $$;


-- ======================================================================================
-- SECTION 3: ADD 'workflow_status' (VARCHAR 30) TO ALL OTHER TABLES IN ifms_budget
-- ======================================================================================

DO $$
DECLARE
    t RECORD;
BEGIN
    FOR t IN (
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'ifms_budget' 
          AND table_type = 'BASE TABLE'
          AND table_name NOT IN ('spatial_ref_sys')
        ORDER BY table_name
    ) 
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'ifms_budget' AND table_name = t.table_name AND column_name = 'workflow_status'
        ) THEN
            EXECUTE format('ALTER TABLE ifms_budget.%I ADD COLUMN workflow_status character varying(30) DEFAULT ''ACTIVE''', t.table_name);
        END IF;
    END LOOP;
END $$;

COMMIT;
