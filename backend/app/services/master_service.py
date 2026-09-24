from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc, text
from datetime import date, datetime
from decimal import Decimal
from app.models.masters import (
    RevAgencyBank, RevBankBranch, RevRevenuePortal, RevSlaRule,
    RevRevenueSource, RevLocalBody, RevDevolutionRule, RevSystemConfig
)
from app.models.common import Department, DDO, Branch, ChartOfAccount, AuditChangeLog
from app.schemas.masters import (
    AgencyBankCreate, BankBranchCreate, DeptPortalCreate,
    RevenueSourceCreate, SLARuleCreate, LocalBodyCreate,
)
from app.schemas.devolution import DevolutionRuleCreate
from app.core.exceptions import NotFoundException, DuplicateRecordException

class MasterService:
    @staticmethod
    async def _log_audit(
        db: AsyncSession,
        table_name: str,
        operation: str,
        row_pk: str,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        user_id: int = 1
    ):
        """Record every master configuration mutation in ifms_budget.audit_change_log."""
        try:
            audit = AuditChangeLog(
                schema_name="ifms_budget",
                table_name=table_name,
                operation=operation.upper(),
                row_pk=str(row_pk),
                old_data=old_data,
                new_data=new_data,
                changed_by=user_id,
                changed_at=func.clock_timestamp(),
                workflow_status="ACTIVE",
            )
            db.add(audit)
            await db.flush()
        except Exception as e:
            print(f"Warning: Failed to log master audit for {table_name}: {e}")

    # =========================================================================
    # 1. DEPARTMENTS MASTER (ifms_budget.department)
    # =========================================================================
    @staticmethod
    async def get_departments(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT department_id, department_code, department_name, department_type, is_active
            FROM ifms_budget.department
        """
        if is_active is not None:
            query += f" WHERE is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY department_id;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_department(db: AsyncSession, data: Any, user_id: int = 1) -> Dict[str, Any]:
        params = {
            "organization_id": 1,
            "department_code": data.department_code.strip().upper(),
            "department_name": data.department_name.strip(),
            "department_type": getattr(data, "department_type", "DEPARTMENT") or "DEPARTMENT",
            "is_active": data.is_active if hasattr(data, "is_active") else True,
        }
        res = await db.execute(
            text("""
                INSERT INTO ifms_budget.department (organization_id, department_code, department_name, department_type, is_active)
                VALUES (:organization_id, :department_code, :department_name, :department_type, :is_active)
                RETURNING department_id, department_code, department_name, department_type, is_active;
            """),
            params
        )
        row = dict(res.mappings().one())
        await MasterService._log_audit(db, "department", "INSERT", str(row["department_id"]), None, row, user_id)
        await db.commit()
        return row

    @staticmethod
    async def update_department(db: AsyncSession, department_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(
            text("SELECT department_id, department_code, department_name, department_type, is_active FROM ifms_budget.department WHERE department_id = :id;"),
            {"id": department_id}
        )
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Department not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": department_id}
        if hasattr(data, "department_code") and data.department_code:
            fields.append("department_code = :code")
            params["code"] = data.department_code.strip().upper()
        if hasattr(data, "department_name") and data.department_name:
            fields.append("department_name = :name")
            params["name"] = data.department_name.strip()
        if hasattr(data, "department_type") and data.department_type:
            fields.append("department_type = :type")
            params["type"] = data.department_type
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.department SET {set_clause}, updated_at = clock_timestamp() WHERE department_id = :id;"), params)

        new_res = await db.execute(
            text("SELECT department_id, department_code, department_name, department_type, is_active FROM ifms_budget.department WHERE department_id = :id;"),
            {"id": department_id}
        )
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "department", "UPDATE", str(department_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 2. PAOS MASTER (ifms_budget.rev_pao)
    # =========================================================================
    @staticmethod
    async def get_paos(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = "SELECT pao_id, pao_code, pao_name, dept_code, treasury_code, is_active FROM ifms_budget.rev_pao"
        if is_active is not None:
            query += f" WHERE is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY pao_code;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_pao(db: AsyncSession, data: Any, user_id: int = 1) -> Dict[str, Any]:
        params = {
            "pao_code": data.pao_code.strip().upper(),
            "pao_name": data.pao_name.strip(),
            "dept_code": (getattr(data, "dept_code", "") or "TT").strip().upper(),
            "treasury_code": getattr(data, "treasury_code", "TRY-DELHI") or "TRY-DELHI",
            "is_active": data.is_active if hasattr(data, "is_active") else True,
        }
        res = await db.execute(
            text("""
                INSERT INTO ifms_budget.rev_pao (pao_code, pao_name, dept_code, treasury_code, is_active)
                VALUES (:pao_code, :pao_name, :dept_code, :treasury_code, :is_active)
                RETURNING pao_id, pao_code, pao_name, dept_code, treasury_code, is_active;
            """),
            params
        )
        row = dict(res.mappings().one())
        await MasterService._log_audit(db, "rev_pao", "INSERT", str(row["pao_id"]), None, row, user_id)
        await db.commit()
        return row

    @staticmethod
    async def update_pao(db: AsyncSession, pao_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(
            text("SELECT pao_id, pao_code, pao_name, dept_code, treasury_code, is_active FROM ifms_budget.rev_pao WHERE pao_id = :id;"),
            {"id": pao_id}
        )
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("PAO not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": pao_id}
        if hasattr(data, "pao_name") and data.pao_name:
            fields.append("pao_name = :name")
            params["name"] = data.pao_name.strip()
        if hasattr(data, "dept_code") and data.dept_code:
            fields.append("dept_code = :dept")
            params["dept"] = data.dept_code.strip().upper()
        if hasattr(data, "treasury_code") and data.treasury_code:
            fields.append("treasury_code = :try")
            params["try"] = data.treasury_code
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.rev_pao SET {set_clause}, updated_at = clock_timestamp() WHERE pao_id = :id;"), params)

        new_res = await db.execute(
            text("SELECT pao_id, pao_code, pao_name, dept_code, treasury_code, is_active FROM ifms_budget.rev_pao WHERE pao_id = :id;"),
            {"id": pao_id}
        )
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "rev_pao", "UPDATE", str(pao_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 3. DDOS MASTER (ifms_budget.ddo)
    # =========================================================================
    @staticmethod
    async def get_ddos(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT d.ddo_id, d.ddo_code, d.ddo_name, d.department_id, dept.department_code, dept.department_name,
                   d.ddo_type, d.treasury_code, d.is_active
            FROM ifms_budget.ddo d
            LEFT JOIN ifms_budget.department dept ON dept.department_id = d.department_id
        """
        if is_active is not None:
            query += f" WHERE d.is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY d.ddo_id;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_ddo(db: AsyncSession, data: Any, user_id: int = 1) -> Dict[str, Any]:
        dept_id = getattr(data, "department_id", 1) or 1
        params = {
            "organization_id": 1,
            "department_id": dept_id,
            "branch_id": 1,
            "ddo_code": data.ddo_code.strip(),
            "ddo_name": data.ddo_name.strip(),
            "ddo_type": getattr(data, "ddo_type", "REGULAR") or "REGULAR",
            "treasury_code": getattr(data, "treasury_code", "TRY-DELHI") or "TRY-DELHI",
            "is_active": data.is_active if hasattr(data, "is_active") else True,
        }
        res = await db.execute(
            text("""
                INSERT INTO ifms_budget.ddo (organization_id, department_id, branch_id, ddo_code, ddo_name, ddo_type, treasury_code, is_active)
                VALUES (:organization_id, :department_id, :branch_id, :ddo_code, :ddo_name, :ddo_type, :treasury_code, :is_active)
                RETURNING ddo_id, ddo_code, ddo_name, department_id, ddo_type, treasury_code, is_active;
            """),
            params
        )
        row = dict(res.mappings().one())
        await MasterService._log_audit(db, "ddo", "INSERT", str(row["ddo_id"]), None, row, user_id)
        await db.commit()
        return row

    @staticmethod
    async def update_ddo(db: AsyncSession, ddo_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(
            text("SELECT ddo_id, ddo_code, ddo_name, department_id, ddo_type, treasury_code, is_active FROM ifms_budget.ddo WHERE ddo_id = :id;"),
            {"id": ddo_id}
        )
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("DDO not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": ddo_id}
        if hasattr(data, "ddo_name") and data.ddo_name:
            fields.append("ddo_name = :name")
            params["name"] = data.ddo_name.strip()
        if hasattr(data, "department_id") and data.department_id:
            fields.append("department_id = :dept_id")
            params["dept_id"] = data.department_id
        if hasattr(data, "treasury_code") and data.treasury_code:
            fields.append("treasury_code = :try")
            params["try"] = data.treasury_code
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.ddo SET {set_clause}, updated_at = clock_timestamp() WHERE ddo_id = :id;"), params)

        new_res = await db.execute(
            text("SELECT ddo_id, ddo_code, ddo_name, department_id, ddo_type, treasury_code, is_active FROM ifms_budget.ddo WHERE ddo_id = :id;"),
            {"id": ddo_id}
        )
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "ddo", "UPDATE", str(ddo_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 4. TREASURIES & BRANCHES (ifms_budget.branch)
    # =========================================================================
    @staticmethod
    async def get_treasuries(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = "SELECT branch_id, branch_code, branch_name, branch_type, treasury_code, city, is_active FROM ifms_budget.branch"
        if is_active is not None:
            query += f" WHERE is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY branch_id;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_treasury(db: AsyncSession, data: Any, user_id: int = 1) -> Dict[str, Any]:
        params = {
            "organization_id": 1,
            "branch_code": data.branch_code.strip().upper(),
            "branch_name": data.branch_name.strip(),
            "branch_type": getattr(data, "branch_type", "TREASURY") or "TREASURY",
            "treasury_code": getattr(data, "treasury_code", None) or data.branch_code.strip().upper(),
            "city": getattr(data, "city", "Delhi") or "Delhi",
            "is_active": data.is_active if hasattr(data, "is_active") else True,
        }
        res = await db.execute(
            text("""
                INSERT INTO ifms_budget.branch (organization_id, branch_code, branch_name, branch_type, treasury_code, city, is_active)
                VALUES (:organization_id, :branch_code, :branch_name, :branch_type, :treasury_code, :city, :is_active)
                RETURNING branch_id, branch_code, branch_name, branch_type, treasury_code, city, is_active;
            """),
            params
        )
        row = dict(res.mappings().one())
        await MasterService._log_audit(db, "branch", "INSERT", str(row["branch_id"]), None, row, user_id)
        await db.commit()
        return row

    @staticmethod
    async def update_treasury(db: AsyncSession, branch_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(
            text("SELECT branch_id, branch_code, branch_name, branch_type, treasury_code, city, is_active FROM ifms_budget.branch WHERE branch_id = :id;"),
            {"id": branch_id}
        )
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Branch/Treasury not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": branch_id}
        if hasattr(data, "branch_name") and data.branch_name:
            fields.append("branch_name = :name")
            params["name"] = data.branch_name.strip()
        if hasattr(data, "branch_type") and data.branch_type:
            fields.append("branch_type = :type")
            params["type"] = data.branch_type
        if hasattr(data, "city") and data.city:
            fields.append("city = :city")
            params["city"] = data.city
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.branch SET {set_clause}, updated_at = clock_timestamp() WHERE branch_id = :id;"), params)

        new_res = await db.execute(
            text("SELECT branch_id, branch_code, branch_name, branch_type, treasury_code, city, is_active FROM ifms_budget.branch WHERE branch_id = :id;"),
            {"id": branch_id}
        )
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "branch", "UPDATE", str(branch_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 5. BANKS & BRANCHES (ifms_budget.agency_bank & ifms_budget.bank_branch)
    # =========================================================================
    @staticmethod
    async def get_banks(db: AsyncSession, is_active: Optional[bool] = None) -> List[RevAgencyBank]:
        query = select(RevAgencyBank)
        if is_active is not None:
            query = query.where(RevAgencyBank.is_active == is_active)
        res = await db.execute(query.order_by(RevAgencyBank.bank_code))
        return list(res.scalars().all())

    @staticmethod
    async def create_bank(db: AsyncSession, data: AgencyBankCreate, user_id: int = 1) -> RevAgencyBank:
        bank = RevAgencyBank(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(bank)
        await db.flush()
        await MasterService._log_audit(db, "agency_bank", "INSERT", str(bank.bank_id), None, {"bank_code": bank.bank_code, "bank_name": bank.bank_name}, user_id)
        await db.commit()
        await db.refresh(bank)
        return bank

    @staticmethod
    async def update_bank(db: AsyncSession, bank_id: int, data: Any, user_id: int = 1) -> RevAgencyBank:
        res = await db.execute(select(RevAgencyBank).where(RevAgencyBank.bank_id == bank_id))
        bank = res.scalar_one_or_none()
        if not bank:
            raise NotFoundException("Bank not found")
        old_data = {"bank_code": bank.bank_code, "bank_name": bank.bank_name, "is_active": bank.is_active}

        if hasattr(data, "bank_name") and data.bank_name:
            bank.bank_name = data.bank_name
        if hasattr(data, "clearing_account_no") and data.clearing_account_no:
            bank.clearing_account_no = data.clearing_account_no
        if hasattr(data, "nodal_officer_name") and data.nodal_officer_name:
            bank.nodal_officer_name = data.nodal_officer_name
        if hasattr(data, "nodal_officer_phone") and data.nodal_officer_phone:
            bank.nodal_officer_phone = data.nodal_officer_phone
        if hasattr(data, "is_active") and data.is_active is not None:
            bank.is_active = data.is_active
        bank.updated_by = user_id

        await MasterService._log_audit(db, "agency_bank", "UPDATE", str(bank_id), old_data, {"bank_code": bank.bank_code, "bank_name": bank.bank_name, "is_active": bank.is_active}, user_id)
        await db.commit()
        await db.refresh(bank)
        return bank

    @staticmethod
    async def get_branches(db: AsyncSession, bank_id: Optional[int] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT br.bank_branch_id, br.bank_id, b.bank_code, b.bank_name, br.branch_code, br.branch_name, br.ifsc_code, br.city, br.is_active
            FROM ifms_budget.bank_branch br
            LEFT JOIN ifms_budget.agency_bank b ON b.bank_id = br.bank_id
            WHERE 1=1
        """
        params = {}
        if bank_id:
            query += " AND br.bank_id = :bank_id"
            params["bank_id"] = bank_id
        if is_active is not None:
            query += f" AND br.is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY br.bank_branch_id;"
        res = await db.execute(text(query), params)
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_branch(db: AsyncSession, data: BankBranchCreate, user_id: int = 1) -> RevBankBranch:
        branch = RevBankBranch(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(branch)
        await db.flush()
        await MasterService._log_audit(db, "bank_branch", "INSERT", str(branch.branch_id), None, {"branch_code": branch.branch_code, "branch_name": branch.branch_name}, user_id)
        await db.commit()
        await db.refresh(branch)
        return branch

    @staticmethod
    async def update_branch(db: AsyncSession, branch_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(text("SELECT * FROM ifms_budget.bank_branch WHERE bank_branch_id = :id;"), {"id": branch_id})
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Bank branch not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": branch_id}
        if hasattr(data, "branch_name") and data.branch_name:
            fields.append("branch_name = :name")
            params["name"] = data.branch_name
        if hasattr(data, "ifsc_code") and data.ifsc_code:
            fields.append("ifsc_code = :ifsc")
            params["ifsc"] = data.ifsc_code
        if hasattr(data, "city") and data.city:
            fields.append("city = :city")
            params["city"] = data.city
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.bank_branch SET {set_clause}, updated_at = clock_timestamp() WHERE bank_branch_id = :id;"), params)

        new_res = await db.execute(text("SELECT * FROM ifms_budget.bank_branch WHERE bank_branch_id = :id;"), {"id": branch_id})
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "bank_branch", "UPDATE", str(branch_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 6. REVENUE PORTALS (ifms_budget.rev_revenue_portal)
    # =========================================================================
    @staticmethod
    async def get_portals(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT p.portal_id, p.portal_code, p.portal_name, p.department_id, d.department_code, d.department_name,
                   p.api_endpoint, p.technical_contact, p.is_active
            FROM ifms_budget.rev_revenue_portal p
            LEFT JOIN ifms_budget.department d ON d.department_id = p.department_id
        """
        if is_active is not None:
            query += f" WHERE p.is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY p.portal_id;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_portal(db: AsyncSession, data: DeptPortalCreate, user_id: int = 1) -> RevRevenuePortal:
        portal = RevRevenuePortal(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(portal)
        await db.flush()
        await MasterService._log_audit(db, "rev_revenue_portal", "INSERT", str(portal.portal_id), None, {"portal_code": portal.portal_code, "portal_name": portal.portal_name}, user_id)
        await db.commit()
        await db.refresh(portal)
        return portal

    @staticmethod
    async def update_portal(db: AsyncSession, portal_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(text("SELECT * FROM ifms_budget.rev_revenue_portal WHERE portal_id = :id;"), {"id": portal_id})
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Portal not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": portal_id}
        if hasattr(data, "portal_name") and data.portal_name:
            fields.append("portal_name = :name")
            params["name"] = data.portal_name
        if hasattr(data, "department_id") and data.department_id:
            fields.append("department_id = :dept_id")
            params["dept_id"] = data.department_id
        if hasattr(data, "api_endpoint") and data.api_endpoint:
            fields.append("api_endpoint = :ep")
            params["ep"] = data.api_endpoint
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.rev_revenue_portal SET {set_clause}, updated_at = clock_timestamp() WHERE portal_id = :id;"), params)

        new_res = await db.execute(text("SELECT * FROM ifms_budget.rev_revenue_portal WHERE portal_id = :id;"), {"id": portal_id})
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "rev_revenue_portal", "UPDATE", str(portal_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 7. REVENUE SOURCES (ifms_budget.rev_revenue_source)
    # =========================================================================
    @staticmethod
    async def get_sources(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT s.source_id, s.source_code, s.source_name, s.department_id, d.department_code, d.department_name,
                   s.default_pao_code, s.portal_id, p.portal_code, s.default_receipt_head_id, c.coa_code as receipt_head,
                   s.allowed_payment_modes, s.is_tax_revenue, s.is_active
            FROM ifms_budget.rev_revenue_source s
            LEFT JOIN ifms_budget.department d ON d.department_id = s.department_id
            LEFT JOIN ifms_budget.rev_revenue_portal p ON p.portal_id = s.portal_id
            LEFT JOIN ifms_budget.chart_of_account c ON c.coa_id = s.default_receipt_head_id
        """
        if is_active is not None:
            query += f" WHERE s.is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY s.source_id;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_source(db: AsyncSession, data: RevenueSourceCreate, user_id: int = 1) -> RevRevenueSource:
        source = RevRevenueSource(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(source)
        await db.flush()
        await MasterService._log_audit(db, "rev_revenue_source", "INSERT", str(source.source_id), None, {"source_code": source.source_code, "source_name": source.source_name}, user_id)
        await db.commit()
        await db.refresh(source)
        return source

    @staticmethod
    async def update_source(db: AsyncSession, source_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(text("SELECT * FROM ifms_budget.rev_revenue_source WHERE source_id = :id;"), {"id": source_id})
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Revenue source not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": source_id}
        if hasattr(data, "source_name") and data.source_name:
            fields.append("source_name = :name")
            params["name"] = data.source_name
        if hasattr(data, "default_pao_code") and data.default_pao_code:
            fields.append("default_pao_code = :pao")
            params["pao"] = data.default_pao_code
        if hasattr(data, "default_receipt_head_id") and data.default_receipt_head_id:
            fields.append("default_receipt_head_id = :head_id")
            params["head_id"] = data.default_receipt_head_id
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.rev_revenue_source SET {set_clause}, updated_at = clock_timestamp() WHERE source_id = :id;"), params)

        new_res = await db.execute(text("SELECT * FROM ifms_budget.rev_revenue_source WHERE source_id = :id;"), {"id": source_id})
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "rev_revenue_source", "UPDATE", str(source_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 8. LOCAL BODIES (ifms_budget.rev_local_body)
    # =========================================================================
    @staticmethod
    async def get_local_bodies(db: AsyncSession, is_active: Optional[bool] = None) -> List[RevLocalBody]:
        query = select(RevLocalBody)
        if is_active is not None:
            query = query.where(RevLocalBody.is_active == is_active)
        res = await db.execute(query.order_by(RevLocalBody.local_body_code))
        return list(res.scalars().all())

    @staticmethod
    async def create_local_body(db: AsyncSession, data: LocalBodyCreate, user_id: int = 1) -> RevLocalBody:
        body = RevLocalBody(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(body)
        await db.flush()
        await MasterService._log_audit(db, "rev_local_body", "INSERT", str(body.local_body_id), None, {"code": body.local_body_code, "name": body.local_body_name}, user_id)
        await db.commit()
        await db.refresh(body)
        return body

    @staticmethod
    async def update_local_body(db: AsyncSession, local_body_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(text("SELECT * FROM ifms_budget.rev_local_body WHERE local_body_id = :id;"), {"id": local_body_id})
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Local body not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": local_body_id}
        if hasattr(data, "local_body_name") and data.local_body_name:
            fields.append("local_body_name = :name")
            params["name"] = data.local_body_name
        if hasattr(data, "bank_account_no") and data.bank_account_no:
            fields.append("bank_account_no = :acc")
            params["acc"] = data.bank_account_no
        if hasattr(data, "ifsc_code") and data.ifsc_code:
            fields.append("ifsc_code = :ifsc")
            params["ifsc"] = data.ifsc_code
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.rev_local_body SET {set_clause}, updated_at = clock_timestamp() WHERE local_body_id = :id;"), params)

        new_res = await db.execute(text("SELECT * FROM ifms_budget.rev_local_body WHERE local_body_id = :id;"), {"id": local_body_id})
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "rev_local_body", "UPDATE", str(local_body_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 9. CHART OF ACCOUNTS / RECEIPT HEADS (ifms_budget.chart_of_account)
    # =========================================================================
    @staticmethod
    async def get_chart_of_accounts(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT c.coa_id, c.coa_code, c.coa_name, c.major_head_id, c.sub_major_head_id, c.minor_head_id,
                   c.account_nature, c.is_active
            FROM ifms_budget.chart_of_account c
            WHERE (c.account_nature = 'REVENUE' OR c.coa_code LIKE '0%' OR c.coa_code LIKE '8658%' OR c.coa_code LIKE '3604%')
        """
        if is_active is not None:
            query += f" AND c.is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY c.coa_code LIMIT 150;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_chart_of_account(db: AsyncSession, data: Any, user_id: int = 1) -> Dict[str, Any]:
        params = {
            "coa_code": data.coa_code.strip(),
            "coa_name": data.coa_name.strip(),
            "major_head_id": getattr(data, "major_head_id", 40) or 40,
            "sub_major_head_id": getattr(data, "sub_major_head_id", 0) or 0,
            "minor_head_id": getattr(data, "minor_head_id", 102) or 102,
            "sub_head_id": 1,
            "detail_head_id": 1,
            "object_head_id": 1,
            "account_nature": getattr(data, "account_nature", "REVENUE") or "REVENUE",
            "is_posting_account": True,
            "is_active": data.is_active if hasattr(data, "is_active") else True,
        }
        res = await db.execute(
            text("""
                INSERT INTO ifms_budget.chart_of_account 
                (coa_code, coa_name, major_head_id, sub_major_head_id, minor_head_id, sub_head_id, detail_head_id, object_head_id, account_nature, is_posting_account, is_active)
                VALUES (:coa_code, :coa_name, :major_head_id, :sub_major_head_id, :minor_head_id, :sub_head_id, :detail_head_id, :object_head_id, :account_nature, :is_posting_account, :is_active)
                RETURNING coa_id, coa_code, coa_name, account_nature, is_active;
            """),
            params
        )
        row = dict(res.mappings().one())
        await MasterService._log_audit(db, "chart_of_account", "INSERT", str(row["coa_id"]), None, row, user_id)
        await db.commit()
        return row

    @staticmethod
    async def update_chart_of_account(db: AsyncSession, coa_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(text("SELECT * FROM ifms_budget.chart_of_account WHERE coa_id = :id;"), {"id": coa_id})
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Chart of Account not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": coa_id}
        if hasattr(data, "coa_name") and data.coa_name:
            fields.append("coa_name = :name")
            params["name"] = data.coa_name
        if hasattr(data, "account_nature") and data.account_nature:
            fields.append("account_nature = :nature")
            params["nature"] = data.account_nature
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.chart_of_account SET {set_clause}, updated_at = clock_timestamp() WHERE coa_id = :id;"), params)

        new_res = await db.execute(text("SELECT * FROM ifms_budget.chart_of_account WHERE coa_id = :id;"), {"id": coa_id})
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "chart_of_account", "UPDATE", str(coa_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 10. RECONCILIATION MATCHING RULES (ifms_budget.rev_recon_rule)
    # =========================================================================
    @staticmethod
    async def get_recon_rules(db: AsyncSession, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT rule_id, rule_code, rule_name, priority, primary_match_keys, 
                   amount_tolerance, date_tolerance_days, matching_mode, outcome_status, is_active
            FROM ifms_budget.rev_recon_rule
        """
        if is_active is not None:
            query += f" WHERE is_active = {'true' if is_active else 'false'}"
        query += " ORDER BY priority ASC, rule_id ASC;"
        res = await db.execute(text(query))
        return [dict(r) for r in res.mappings().all()]

    @staticmethod
    async def create_recon_rule(db: AsyncSession, data: Any, user_id: int = 1) -> Dict[str, Any]:
        params = {
            "rule_code": data.rule_code.strip().upper(),
            "rule_name": data.rule_name.strip(),
            "priority": int(getattr(data, "priority", 1) or 1),
            "primary_match_keys": data.primary_match_keys.strip(),
            "amount_tolerance": float(getattr(data, "amount_tolerance", 0.01) or 0.01),
            "date_tolerance_days": int(getattr(data, "date_tolerance_days", 2) or 2),
            "matching_mode": getattr(data, "matching_mode", "THREE_WAY_EXACT") or "THREE_WAY_EXACT",
            "outcome_status": getattr(data, "outcome_status", "Matched") or "Matched",
            "is_active": data.is_active if hasattr(data, "is_active") else True,
        }
        res = await db.execute(
            text("""
                INSERT INTO ifms_budget.rev_recon_rule 
                (rule_code, rule_name, priority, primary_match_keys, amount_tolerance, date_tolerance_days, matching_mode, outcome_status, is_active)
                VALUES (:rule_code, :rule_name, :priority, :primary_match_keys, :amount_tolerance, :date_tolerance_days, :matching_mode, :outcome_status, :is_active)
                RETURNING rule_id, rule_code, rule_name, priority, primary_match_keys, amount_tolerance, date_tolerance_days, matching_mode, outcome_status, is_active;
            """),
            params
        )
        row = dict(res.mappings().one())
        await MasterService._log_audit(db, "rev_recon_rule", "INSERT", str(row["rule_id"]), None, row, user_id)
        await db.commit()
        return row

    @staticmethod
    async def update_recon_rule(db: AsyncSession, rule_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(text("SELECT * FROM ifms_budget.rev_recon_rule WHERE rule_id = :id;"), {"id": rule_id})
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("Reconciliation rule not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": rule_id}
        if hasattr(data, "rule_name") and data.rule_name:
            fields.append("rule_name = :name")
            params["name"] = data.rule_name
        if hasattr(data, "priority") and data.priority is not None:
            fields.append("priority = :prio")
            params["prio"] = int(data.priority)
        if hasattr(data, "primary_match_keys") and data.primary_match_keys:
            fields.append("primary_match_keys = :keys")
            params["keys"] = data.primary_match_keys
        if hasattr(data, "amount_tolerance") and data.amount_tolerance is not None:
            fields.append("amount_tolerance = :amt")
            params["amt"] = float(data.amount_tolerance)
        if hasattr(data, "date_tolerance_days") and data.date_tolerance_days is not None:
            fields.append("date_tolerance_days = :dt")
            params["dt"] = int(data.date_tolerance_days)
        if hasattr(data, "matching_mode") and data.matching_mode:
            fields.append("matching_mode = :mode")
            params["mode"] = data.matching_mode
        if hasattr(data, "outcome_status") and data.outcome_status:
            fields.append("outcome_status = :status")
            params["status"] = data.outcome_status
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.rev_recon_rule SET {set_clause}, updated_at = clock_timestamp() WHERE rule_id = :id;"), params)

        new_res = await db.execute(text("SELECT * FROM ifms_budget.rev_recon_rule WHERE rule_id = :id;"), {"id": rule_id})
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "rev_recon_rule", "UPDATE", str(rule_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 11. BANK SLA & PENAL INTEREST RULES (ifms_budget.rev_sla_rule)
    # =========================================================================
    @staticmethod
    async def get_sla_rules(db: AsyncSession, is_active: Optional[bool] = None) -> List[RevSlaRule]:
        query = select(RevSlaRule)
        if is_active is not None:
            query = query.where(RevSlaRule.is_active == is_active)
        res = await db.execute(query.order_by(RevSlaRule.rule_code))
        return list(res.scalars().all())

    @staticmethod
    async def create_sla_rule(db: AsyncSession, data: SLARuleCreate, user_id: int = 1) -> RevSlaRule:
        rule = RevSlaRule(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(rule)
        await db.flush()
        await MasterService._log_audit(db, "rev_sla_rule", "INSERT", str(rule.sla_rule_id), None, {"code": rule.rule_code, "name": rule.rule_name}, user_id)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def update_sla_rule(db: AsyncSession, sla_rule_id: int, data: Any, user_id: int = 1) -> Dict[str, Any]:
        old_res = await db.execute(text("SELECT * FROM ifms_budget.rev_sla_rule WHERE sla_rule_id = :id;"), {"id": sla_rule_id})
        old_row = old_res.mappings().one_or_none()
        if not old_row:
            raise NotFoundException("SLA rule not found")
        old_data = dict(old_row)

        fields = []
        params = {"id": sla_rule_id}
        if hasattr(data, "rule_name") and data.rule_name:
            fields.append("rule_name = :name")
            params["name"] = data.rule_name
        if hasattr(data, "allowed_remittance_days") and data.allowed_remittance_days is not None:
            fields.append("allowed_remittance_days = :days")
            params["days"] = int(data.allowed_remittance_days)
        if hasattr(data, "grace_days") and data.grace_days is not None:
            fields.append("grace_days = :grace")
            params["grace"] = int(data.grace_days)
        if hasattr(data, "annual_penal_rate_pct") and data.annual_penal_rate_pct is not None:
            fields.append("annual_penal_rate_pct = :rate")
            params["rate"] = float(data.annual_penal_rate_pct)
        if hasattr(data, "is_active") and data.is_active is not None:
            fields.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if fields:
            set_clause = ", ".join(fields)
            await db.execute(text(f"UPDATE ifms_budget.rev_sla_rule SET {set_clause}, updated_at = clock_timestamp() WHERE sla_rule_id = :id;"), params)

        new_res = await db.execute(text("SELECT * FROM ifms_budget.rev_sla_rule WHERE sla_rule_id = :id;"), {"id": sla_rule_id})
        new_row = dict(new_res.mappings().one())
        await MasterService._log_audit(db, "rev_sla_rule", "UPDATE", str(sla_rule_id), old_data, new_row, user_id)
        await db.commit()
        return new_row

    # =========================================================================
    # 12. DEVOLUTION RULES
    # =========================================================================
    @staticmethod
    async def get_devolution_rules(db: AsyncSession, is_active: Optional[bool] = None) -> List[RevDevolutionRule]:
        query = select(RevDevolutionRule)
        if is_active is not None:
            query = query.where(RevDevolutionRule.is_active == is_active)
        res = await db.execute(query.order_by(RevDevolutionRule.rule_code))
        return list(res.scalars().all())

    @staticmethod
    async def create_devolution_rule(db: AsyncSession, data: DevolutionRuleCreate, user_id: int = 1) -> RevDevolutionRule:
        rule = RevDevolutionRule(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    # =========================================================================
    # 13. SYSTEM CONFIGURATION (ifms_budget.rev_system_config)
    # =========================================================================
    @staticmethod
    async def get_system_config(db: AsyncSession) -> Dict[str, Any]:
        res = await db.execute(select(RevSystemConfig).where(RevSystemConfig.config_id == 1))
        config = res.scalar_one_or_none()
        if not config:
            config = RevSystemConfig(
                config_id=1,
                demo_business_date=date(2026, 9, 15),
                current_financial_year="2026-27",
                amount_tolerance=Decimal("0.01"),
                date_tolerance_days=2,
                default_penal_rate_pct=Decimal("12.00"),
                penal_day_basis=365,
                exception_escalation_days=3,
                updated_by=1
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)

        coa_res = await db.execute(select(ChartOfAccount))
        coa_map = {c.coa_id: c for c in coa_res.scalars().all()}

        susp_coa = coa_map.get(config.suspense_head_id)
        rat_coa = coa_map.get(config.rat_suspense_head_id)
        bank_coa = coa_map.get(config.bank_clearing_head_id)
        ref_coa = coa_map.get(config.refund_deduct_head_id)
        penal_coa = coa_map.get(config.penal_interest_head_id)
        penalty_coa = coa_map.get(config.penalty_head_id)

        return {
            "bizDate": config.demo_business_date.isoformat(),
            "fy": config.current_financial_year,
            "amtTolerance": float(config.amount_tolerance),
            "dateTolerance": config.date_tolerance_days,
            "penalRate": float(config.default_penal_rate_pct),
            "penalDayBasis": config.penal_day_basis,
            "escalationDays": config.exception_escalation_days,
            "suspenseHead": susp_coa.coa_code if susp_coa else "8658-00-102-01-00-01",
            "ratHead": rat_coa.coa_code if rat_coa else "8658-00-110-01-00-01",
            "clearingAccount": bank_coa.coa_code if bank_coa else "8658-00-101-01-00-01",
            "refundHead": ref_coa.coa_code if ref_coa else "0030-00-900-01-00-01",
            "penalInterestHead": penal_coa.coa_code if penal_coa else "8658-00-102-01-00-02",
            "penaltyHead": penalty_coa.coa_code if penalty_coa else "0070-60-800-01-00-02",
            "penalInterestHeadId": config.penal_interest_head_id,
            "penaltyHeadId": config.penalty_head_id,
        }

    @staticmethod
    async def update_system_config(db: AsyncSession, payload: Dict[str, Any], user_id: int = 1) -> Dict[str, Any]:
        res = await db.execute(select(RevSystemConfig).where(RevSystemConfig.config_id == 1))
        config = res.scalar_one_or_none()
        if not config:
            config = RevSystemConfig(config_id=1)
            db.add(config)

        old_data = {
            "bizDate": config.demo_business_date.isoformat() if config.demo_business_date else None,
            "fy": config.current_financial_year,
            "amtTolerance": float(config.amount_tolerance) if config.amount_tolerance else None,
            "dateTolerance": config.date_tolerance_days,
            "penalRate": float(config.default_penal_rate_pct) if config.default_penal_rate_pct else None,
        }

        if "bizDate" in payload or "demo_business_date" in payload:
            val = payload.get("bizDate") or payload.get("demo_business_date")
            if isinstance(val, str):
                parts = [int(p) for p in val.split("-")]
                config.demo_business_date = date(parts[0], parts[1], parts[2])
            elif isinstance(val, date):
                config.demo_business_date = val

        if "fy" in payload or "current_financial_year" in payload:
            config.current_financial_year = str(payload.get("fy") or payload.get("current_financial_year"))
        if "amtTolerance" in payload or "amount_tolerance" in payload:
            config.amount_tolerance = Decimal(str(payload.get("amtTolerance") or payload.get("amount_tolerance")))
        if "dateTolerance" in payload or "date_tolerance_days" in payload:
            config.date_tolerance_days = int(payload.get("dateTolerance") or payload.get("date_tolerance_days"))
        if "penalRate" in payload or "default_penal_rate_pct" in payload:
            config.default_penal_rate_pct = Decimal(str(payload.get("penalRate") or payload.get("default_penal_rate_pct")))
        if "penalDayBasis" in payload or "penal_day_basis" in payload:
            config.penal_day_basis = int(payload.get("penalDayBasis") or payload.get("penal_day_basis"))
        if "escalationDays" in payload or "exception_escalation_days" in payload:
            config.exception_escalation_days = int(payload.get("escalationDays") or payload.get("exception_escalation_days"))

        config.updated_by = user_id
        await MasterService._log_audit(db, "rev_system_config", "UPDATE", "1", old_data, payload, user_id)
        await db.commit()
        await db.refresh(config)

        return await MasterService.get_system_config(db)
