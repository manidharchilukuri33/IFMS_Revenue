from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RevAgencyBank(Base):
    __tablename__ = "agency_bank"
    __table_args__ = {"schema": "ifms_budget"}

    bank_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bank_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    clearing_account_no: Mapped[Optional[str]] = mapped_column(String(50))
    nodal_officer_name: Mapped[Optional[str]] = mapped_column(String(150))
    nodal_officer_email: Mapped[Optional[str]] = mapped_column(String(150))
    nodal_officer_phone: Mapped[Optional[str]] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), onupdate=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

    branches: Mapped[List["RevBankBranch"]] = relationship("RevBankBranch", back_populates="bank")

class RevBankBranch(Base):
    __tablename__ = "bank_branch"
    __table_args__ = {"schema": "ifms_budget"}

    branch_id: Mapped[int] = mapped_column("bank_branch_id", BigInteger, primary_key=True)
    bank_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.agency_bank.bank_id"), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(30), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

    bank: Mapped["RevAgencyBank"] = relationship("RevAgencyBank", back_populates="branches")

class RevRevenuePortal(Base):
    __tablename__ = "rev_revenue_portal"
    __table_args__ = {"schema": "ifms_budget"}

    portal_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    portal_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    portal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.department.department_id"), nullable=False)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    technical_contact: Mapped[Optional[str]] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

class RevSlaRule(Base):
    __tablename__ = "rev_sla_rule"
    __table_args__ = {"schema": "ifms_budget"}

    sla_rule_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rule_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    rule_name: Mapped[str] = mapped_column(String(150), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    allowed_remittance_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    grace_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    annual_penal_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=12.00, nullable=False)
    calculation_basis: Mapped[str] = mapped_column(String(30), default="ACTUAL_365", nullable=False)
    base_date_type: Mapped[str] = mapped_column(String(30), default="PAYMENT_DATE", nullable=False)
    min_recovery_threshold: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=10.00, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

class RevRevenueSource(Base):
    __tablename__ = "rev_revenue_source"
    __table_args__ = {"schema": "ifms_budget"}

    source_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    source_name: Mapped[str] = mapped_column(String(150), nullable=False)
    department_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.department.department_id"), nullable=False)
    default_pao_code: Mapped[str] = mapped_column(String(30), nullable=False)
    portal_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_revenue_portal.portal_id"), nullable=False)
    default_receipt_head_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)
    allowed_payment_modes: Mapped[list] = mapped_column(ARRAY(String), default=["NETBANKING", "UPI", "CARD", "CASH", "CHEQUE"], nullable=False)
    match_key_precedence: Mapped[list] = mapped_column(ARRAY(String), default=["CIN", "CHALLAN_NO", "CPIN", "PORTAL_TXN_ID"], nullable=False)
    sla_rule_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_sla_rule.sla_rule_id"))
    is_tax_revenue: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

class RevLocalBody(Base):
    __tablename__ = "rev_local_body"
    __table_args__ = {"schema": "ifms_budget"}

    local_body_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    local_body_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    local_body_name: Mapped[str] = mapped_column(String(250), nullable=False)
    body_type: Mapped[str] = mapped_column(String(50), default="MUNICIPAL_CORP", nullable=False)
    bank_account_no: Mapped[str] = mapped_column(String(50), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(150), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

class RevDevolutionRule(Base):
    __tablename__ = "rev_devolution_rule"
    __table_args__ = {"schema": "ifms_budget"}

    dev_rule_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    local_body_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_local_body.local_body_id"), nullable=False)
    source_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_revenue_source.source_id"), nullable=False)
    receipt_head_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)
    share_basis: Mapped[str] = mapped_column(String(20), default="PERCENTAGE", nullable=False)
    share_value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

class RevSystemConfig(Base):
    __tablename__ = "rev_system_config"
    __table_args__ = {"schema": "ifms_budget"}

    config_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    demo_business_date: Mapped[date] = mapped_column(Date, default=date(2026, 9, 15), nullable=False)
    current_financial_year: Mapped[str] = mapped_column(String(15), default="2026-27", nullable=False)
    amount_tolerance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.01, nullable=False)
    date_tolerance_days: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    default_penal_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=12.00, nullable=False)
    penal_day_basis: Mapped[int] = mapped_column(Integer, default=365, nullable=False)
    exception_escalation_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    suspense_head_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"))
    rat_suspense_head_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"))
    bank_clearing_head_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"))
    refund_deduct_head_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"))
    devolution_expenditure_head_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")
