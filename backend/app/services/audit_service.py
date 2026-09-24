import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text, or_, and_
from app.models.common import AuditChangeLog, AppUser

TABLE_MODULE_MAP = {
    # Reconciliation
    "rev_recon_result": ("Reconciliation", "Reconciliation Result"),
    "rev_recon_run": ("Reconciliation", "Reconciliation Run"),
    "rev_recon_override": ("Reconciliation", "Status Override"),
    "rev_recon_rule": ("Masters", "Reconciliation Rule"),
    
    # Upload & Staging
    "rev_upload_batch": ("Upload", "Upload Batch"),
    "upload_batch": ("Upload", "Upload Batch"),
    "rev_staging_portal": ("Upload", "Portal Staging"),
    "rev_staging_bank_scroll": ("Upload", "Bank Scroll Staging"),
    "rev_staging_rbi_luggage": ("Upload", "RBI Luggage Staging"),
    
    # Exceptions & SLA
    "rev_exception": ("Exceptions", "Revenue Exception"),
    "rev_exception_letter": ("Exceptions", "Exception Letter"),
    "rev_exception_action": ("Exceptions", "Exception Action"),
    "rev_sla_rule": ("Masters", "Bank SLA Rule"),
    "rev_penal_claim": ("Bank SLA", "Penal Claim"),
    
    # Accounting & Vouchers
    "rev_receipt_voucher": ("Accounting", "Receipt Voucher"),
    "account_voucher": ("Accounting", "Account Voucher"),
    "rev_suspense_item": ("Accounting", "Suspense Item"),
    "voucher_line": ("Accounting", "Voucher Line Item"),
    
    # Refunds
    "rev_refund_case": ("Refund Management", "Refund Case"),
    "rev_refund_timeline": ("Refund Management", "Refund Milestone"),
    
    # Devolution
    "rev_devolution_claim": ("Revenue Devolution", "Devolution Claim"),
    "rev_devolution_rule": ("Masters", "Devolution Rule"),
    "rev_local_body": ("Masters", "Local Body"),
    
    # Masters & Configuration
    "department": ("Masters", "Department"),
    "ddo": ("Masters", "DDO"),
    "branch": ("Masters", "Treasury / Branch"),
    "agency_bank": ("Masters", "Agency Bank"),
    "bank_branch": ("Masters", "Bank Branch"),
    "rev_revenue_portal": ("Masters", "Revenue Portal"),
    "rev_revenue_source": ("Masters", "Revenue Source"),
    "chart_of_account": ("Masters", "Chart of Accounts Head"),
    "rev_system_config": ("Masters", "System Configuration"),
    
    # Budget Proposal & Workflow
    "budget_proposal": ("Budget", "Budget Proposal"),
    "budget_proposal_line": ("Budget", "Proposal Line"),
    "budget_allocation": ("Budget", "Budget Allocation"),
    "budget_allocation_line": ("Budget", "Allocation Line"),
    "approved_budget": ("Budget", "Approved Budget"),
    "budget_ledger_entry": ("Budget", "Ledger Entry"),
    "budget_submission": ("Budget", "Budget Submission"),
    "budget_submission_line": ("Budget", "Submission Line"),
    "fund_release": ("Budget", "Fund Release"),
    "commitment": ("Budget", "Commitment"),
    "reappropriation": ("Budget", "Reappropriation"),
    "supplementary_estimate": ("Budget", "Supplementary Estimate"),
    "surrender": ("Budget", "Budget Surrender"),
    "workflow_action_log": ("Workflow", "Workflow Action"),
}

# Invert module map for filtering by module name
MODULE_TABLES_MAP: Dict[str, List[str]] = {}
for tbl, (mod, _) in TABLE_MODULE_MAP.items():
    MODULE_TABLES_MAP.setdefault(mod.lower(), []).append(tbl)


def _format_values_and_remarks(table_name: str, operation: str, row_pk: str, old_data: Any, new_data: Any):
    if isinstance(old_data, str):
        try:
            old_data = json.loads(old_data)
        except Exception:
            pass
    if isinstance(new_data, str):
        try:
            new_data = json.loads(new_data)
        except Exception:
            pass

    old_dict = old_data if isinstance(old_data, dict) else {}
    new_dict = new_data if isinstance(new_data, dict) else {}

    changed_diff = []
    if operation == "UPDATE" and old_dict and new_dict:
        for k, v in new_dict.items():
            if k in old_dict and old_dict[k] != v:
                v_old_str = f"₹ {old_dict[k]:,.2f}" if isinstance(old_dict[k], (int, float)) and "amount" in k else str(old_dict[k])
                v_new_str = f"₹ {v:,.2f}" if isinstance(v, (int, float)) and "amount" in k else str(v)
                changed_diff.append(f"{k}: {v_old_str} → {v_new_str}")

    old_str = ""
    if operation in ("UPDATE", "DELETE") and old_dict:
        keys_to_show = ["status", "is_active", "amount", "booking_status", "challan_no", "voucher_no", "department_name", "department_code", "full_name"]
        present = [f"{k}: {old_dict[k]}" for k in keys_to_show if k in old_dict and old_dict[k] is not None]
        old_str = ", ".join(present[:3]) if present else (json.dumps(old_dict)[:60] if old_dict else "-")

    new_str = ""
    if operation in ("INSERT", "UPDATE") and new_dict:
        if changed_diff:
            new_str = ", ".join(changed_diff[:3])
        else:
            keys_to_show = ["status", "is_active", "amount", "booking_status", "challan_no", "voucher_no", "department_name", "department_code", "full_name"]
            present = [f"{k}: {new_dict[k]}" for k in keys_to_show if k in new_dict and new_dict[k] is not None]
            new_str = ", ".join(present[:3]) if present else (json.dumps(new_dict)[:60] if new_dict else "-")

    entity_label = TABLE_MODULE_MAP.get(table_name, ("General", table_name.replace("_", " ").title()))[1]
    row_ref = f"#{row_pk}" if row_pk else ""
    if operation == "INSERT":
        remarks = f"New {entity_label} {row_ref} created"
    elif operation == "UPDATE":
        if changed_diff:
            remarks = f"{entity_label} {row_ref} updated: {changed_diff[0]}"
        else:
            remarks = f"{entity_label} {row_ref} modified"
    elif operation == "DELETE":
        remarks = f"{entity_label} {row_ref} deleted"
    else:
        remarks = f"{operation} on {entity_label} {row_ref}"

    return old_str, new_str, remarks, old_dict, new_dict


class AuditService:
    @staticmethod
    async def get_audit_summary(db: AsyncSession) -> Dict[str, Any]:
        """Returns KPI statistics and available filter options directly from PostgreSQL."""
        total_count = (await db.execute(text("SELECT count(*) FROM ifms_budget.audit_change_log;"))).scalar() or 0
        distinct_modules_count = (await db.execute(text("SELECT count(DISTINCT table_name) FROM ifms_budget.audit_change_log;"))).scalar() or 0
        distinct_actions_count = (await db.execute(text("SELECT count(DISTINCT operation) FROM ifms_budget.audit_change_log;"))).scalar() or 0

        min_date = (await db.execute(text("SELECT min(changed_at) FROM ifms_budget.audit_change_log;"))).scalar()
        max_date = (await db.execute(text("SELECT max(changed_at) FROM ifms_budget.audit_change_log;"))).scalar()

        # Available modules
        raw_tables = (await db.execute(text("SELECT DISTINCT table_name FROM ifms_budget.audit_change_log ORDER BY table_name;"))).scalars().all()
        module_set = set()
        for tbl in raw_tables:
            mod = TABLE_MODULE_MAP.get(tbl, ("Other", ""))[0]
            module_set.add(mod)
        available_modules = sorted(list(module_set))

        # Available actions
        raw_ops = (await db.execute(text("SELECT DISTINCT operation FROM ifms_budget.audit_change_log ORDER BY operation;"))).scalars().all()
        available_actions = [op.upper() for op in raw_ops if op]

        return {
            "total_entries": total_count,
            "distinct_modules": distinct_modules_count,
            "distinct_actions": distinct_actions_count,
            "earliest_entry": min_date.strftime("%d-%b-%Y %H:%M:%S") if min_date else "-",
            "latest_entry": max_date.strftime("%d-%b-%Y %H:%M:%S") if max_date else "-",
            "modules": available_modules,
            "actions": available_actions,
        }

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        table_name: Optional[str] = None,
        module: Optional[str] = None,
        record_id: Optional[str] = None,
        action: Optional[str] = None,
        user: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Fetch paginated, filtered audit logs from PostgreSQL ifms_budget.audit_change_log."""
        # 1. Fetch user map for quick resolution of changed_by
        user_rows = (await db.execute(select(AppUser))).scalars().all()
        user_map: Dict[int, AppUser] = {u.user_id: u for u in user_rows}

        # Build dynamic query
        query = select(AuditChangeLog)

        # Filter by table_name or module
        if table_name and table_name.lower() != "all":
            query = query.where(AuditChangeLog.table_name == table_name)
        elif module and module.lower() != "all":
            mod_key = module.strip().lower()
            matching_tables = MODULE_TABLES_MAP.get(mod_key, [])
            if matching_tables:
                query = query.where(AuditChangeLog.table_name.in_(matching_tables))
            else:
                # Fallback: check if table_name equals module
                query = query.where(func.lower(AuditChangeLog.table_name) == mod_key)

        if record_id:
            query = query.where(AuditChangeLog.row_pk == str(record_id).strip())

        if action and action.upper() != "ALL":
            query = query.where(func.upper(AuditChangeLog.operation) == action.strip().upper())

        if from_date:
            try:
                dt_from = datetime.strptime(from_date.strip(), "%Y-%m-%d")
                query = query.where(AuditChangeLog.changed_at >= dt_from)
            except Exception:
                pass

        if to_date:
            try:
                dt_to = datetime.strptime(f"{to_date.strip()} 23:59:59", "%Y-%m-%d %H:%M:%S")
                query = query.where(AuditChangeLog.changed_at <= dt_to)
            except Exception:
                pass

        if user:
            u_clean = user.strip().lower()
            # Match user ID or names
            matched_uids = [
                uid for uid, usr in user_map.items()
                if u_clean in (usr.login_name or "").lower() or u_clean in (usr.full_name or "").lower()
            ]
            if matched_uids:
                query = query.where(or_(AuditChangeLog.changed_by.in_(matched_uids), AuditChangeLog.row_pk.ilike(f"%{u_clean}%")))
            else:
                query = query.where(AuditChangeLog.row_pk.ilike(f"%{u_clean}%"))

        if search:
            s_clean = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    AuditChangeLog.table_name.ilike(s_clean),
                    AuditChangeLog.operation.ilike(s_clean),
                    AuditChangeLog.row_pk.ilike(s_clean),
                    text("ifms_budget.audit_change_log.new_data::text ILIKE :s_clean").bindparams(s_clean=s_clean)
                )
            )

        # Count total matching
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        # Execute paginated query ordered by audit_id DESC
        query = query.order_by(desc(AuditChangeLog.audit_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        logs = result.scalars().all()

        items = []
        for log in logs:
            # Resolve user details
            u_info = user_map.get(log.changed_by) if log.changed_by else None
            user_name = u_info.full_name if u_info else (u_info.login_name if u_info else ("admin.system" if log.changed_by == 1 else "system.cdc_trigger"))
            user_role = "SYSADMIN" if (log.changed_by == 1 or not u_info) else ("PAO_MAKER" if "maker" in (u_info.login_name or "") else ("PAO_CHECK" if "approver" in (u_info.login_name or "") else "DDO"))

            # Resolve module & entity
            mod_name, entity_name = TABLE_MODULE_MAP.get(
                log.table_name,
                ("General", log.table_name.replace("_", " ").title())
            )

            # Format values and descriptive remarks
            old_str, new_str, remarks, old_dict, new_dict = _format_values_and_remarks(
                log.table_name,
                log.operation,
                log.row_pk or "",
                log.old_data,
                log.new_data
            )

            ts_formatted = log.changed_at.strftime("%d-%b-%Y %H:%M:%S") if log.changed_at else ""

            items.append({
                "id": log.audit_id,
                "audit_id": log.audit_id,
                "ts": ts_formatted,
                "timestamp": ts_formatted,
                "created_at": ts_formatted,
                "user": user_name,
                "user_name": user_name,
                "role": user_role,
                "user_role": user_role,
                "module": mod_name,
                "module_name": mod_name,
                "action": log.operation,
                "action_type": log.operation,
                "operation": log.operation,
                "entity": entity_name,
                "entity_type": entity_name,
                "table_name": log.table_name,
                "entityId": log.row_pk or f"#{log.audit_id}",
                "entity_id": log.row_pk or f"#{log.audit_id}",
                "row_pk": log.row_pk,
                "oldV": old_str,
                "old_value": old_str,
                "newV": new_str,
                "new_value": new_str,
                "old_data": old_dict,
                "new_data": new_dict,
                "remarks": remarks,
                "txid": log.txid,
            })

        summary = await AuditService.get_audit_summary(db)

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "summary": summary,
            "items": items,
        }
