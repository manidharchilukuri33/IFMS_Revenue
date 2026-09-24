from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc
from datetime import date
from decimal import Decimal
from app.models.masters import (
    RevAgencyBank, RevBankBranch, RevRevenuePortal, RevSlaRule,
    RevRevenueSource, RevLocalBody, RevDevolutionRule, RevSystemConfig
)
from app.models.common import Department, ChartOfAccount
from app.schemas.masters import (
    AgencyBankCreate, BankBranchCreate, DeptPortalCreate,
    RevenueSourceCreate, SLARuleCreate, LocalBodyCreate,
)
from app.schemas.devolution import DevolutionRuleCreate
from app.core.exceptions import NotFoundException, DuplicateRecordException

class MasterService:
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
        await db.commit()
        await db.refresh(bank)
        return bank

    @staticmethod
    async def get_branches(db: AsyncSession, bank_id: Optional[int] = None, is_active: Optional[bool] = None) -> List[RevBankBranch]:
        query = select(RevBankBranch)
        if bank_id:
            query = query.where(RevBankBranch.bank_id == bank_id)
        if is_active is not None:
            query = query.where(RevBankBranch.is_active == is_active)
        res = await db.execute(query.order_by(RevBankBranch.branch_code))
        return list(res.scalars().all())

    @staticmethod
    async def create_branch(db: AsyncSession, data: BankBranchCreate, user_id: int = 1) -> RevBankBranch:
        branch = RevBankBranch(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(branch)
        await db.commit()
        await db.refresh(branch)
        return branch

    @staticmethod
    async def get_portals(db: AsyncSession, is_active: Optional[bool] = None) -> List[RevRevenuePortal]:
        query = select(RevRevenuePortal)
        if is_active is not None:
            query = query.where(RevRevenuePortal.is_active == is_active)
        res = await db.execute(query.order_by(RevRevenuePortal.portal_code))
        return list(res.scalars().all())

    @staticmethod
    async def create_portal(db: AsyncSession, data: DeptPortalCreate, user_id: int = 1) -> RevRevenuePortal:
        portal = RevRevenuePortal(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(portal)
        await db.commit()
        await db.refresh(portal)
        return portal

    @staticmethod
    async def get_sources(db: AsyncSession, is_active: Optional[bool] = None) -> List[RevRevenueSource]:
        query = select(RevRevenueSource)
        if is_active is not None:
            query = query.where(RevRevenueSource.is_active == is_active)
        res = await db.execute(query.order_by(RevRevenueSource.source_code))
        return list(res.scalars().all())

    @staticmethod
    async def create_source(db: AsyncSession, data: RevenueSourceCreate, user_id: int = 1) -> RevRevenueSource:
        source = RevRevenueSource(**data.model_dump(), created_by=user_id, updated_by=user_id)
        db.add(source)
        await db.commit()
        await db.refresh(source)
        return source

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
        await db.commit()
        await db.refresh(rule)
        return rule

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
        await db.commit()
        await db.refresh(body)
        return body

    @staticmethod
    async def get_chart_of_accounts(db: AsyncSession, is_active: Optional[bool] = None) -> List[ChartOfAccount]:
        query = select(ChartOfAccount)
        if is_active is not None:
            query = query.where(ChartOfAccount.is_active == is_active)
        res = await db.execute(query.order_by(ChartOfAccount.coa_code).limit(100))
        return list(res.scalars().all())

    @staticmethod
    async def get_paos(db: AsyncSession) -> List[Dict[str, Any]]:
        paos = [
            {"pao_code": "PAO21", "pao_name": "PAO 21 — Trade & Taxes (GST/VAT)", "dept_code": "TT"},
            {"pao_code": "PAO04", "pao_name": "PAO 04 — State Excise", "dept_code": "EXCISE"},
            {"pao_code": "PAO08", "pao_name": "PAO 08 — Transport Dept (Vahan)", "dept_code": "TPT"},
            {"pao_code": "PAO06", "pao_name": "PAO 06 — Stamps & Registration (NGDRS)", "dept_code": "REV"},
            {"pao_code": "PAO10", "pao_name": "PAO 10 — Land Revenue & Mining", "dept_code": "REV"},
            {"pao_code": "PAO01", "pao_name": "PAO 01 — Secretariat Central", "dept_code": "FIN"},
        ]
        return paos

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

        # Load COA lookup map
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

        # COA Head updates by code or ID
        if "penalInterestHeadId" in payload:
            config.penal_interest_head_id = int(payload["penalInterestHeadId"])
        elif "penalInterestHead" in payload:
            p_res = await db.execute(select(ChartOfAccount.coa_id).where(ChartOfAccount.coa_code == payload["penalInterestHead"]).limit(1))
            p_id = p_res.scalar_one_or_none()
            if p_id:
                config.penal_interest_head_id = p_id

        if "penaltyHeadId" in payload:
            config.penalty_head_id = int(payload["penaltyHeadId"])
        elif "penaltyHead" in payload:
            p_res2 = await db.execute(select(ChartOfAccount.coa_id).where(ChartOfAccount.coa_code == payload["penaltyHead"]).limit(1))
            p2_id = p_res2.scalar_one_or_none()
            if p2_id:
                config.penalty_head_id = p2_id

        config.updated_by = user_id
        await db.commit()
        await db.refresh(config)

        return await MasterService.get_system_config(db)
