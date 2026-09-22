from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class AccountVoucher(Base):
    __tablename__ = "account_voucher"
    __table_args__ = {"schema": "ifms_budget"}

    voucher_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sr_no: Mapped[Optional[int]] = mapped_column(BigInteger)
    voucher_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    voucher_type: Mapped[str] = mapped_column(String(30), default="REVENUE_RECEIPT", nullable=False) # 'REVENUE_RECEIPT', 'EXPENDITURE', 'REFUND', 'DEVOLUTION'
    voucher_date: Mapped[date] = mapped_column(Date, nullable=False)
    financial_year: Mapped[str] = mapped_column(String(15), nullable=False)
    pao_code: Mapped[str] = mapped_column(String(30), nullable=False)

    # Financial Values & Dual Chart of Accounts (Double Entry in Single Line)
    amount: Mapped[Decimal] = mapped_column(Numeric(17, 2), nullable=False)
    debit_coa_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)
    credit_coa_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)

    # Expenditure & Departmental Linkages
    demand_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.demand.demand_id"))
    department_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.department.department_id"))
    ddo_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.ddo.ddo_id"))
    office_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    scheme_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.scheme.scheme_id"))
    project_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.project.project_id"))

    # Reconciliation & Bill Details
    recon_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id"))
    bill_no: Mapped[Optional[str]] = mapped_column(String(50))
    bill_date: Mapped[Optional[date]] = mapped_column(Date)
    payee_name: Mapped[Optional[str]] = mapped_column(String(250))

    # Workflow & Audit Details
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Draft", nullable=False) # 'Draft', 'Approved', 'Rejected', 'Cancelled'
    prepared_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    prepared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp())
    checker_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    checker_remarks: Mapped[Optional[str]] = mapped_column(Text)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Enterprise Audit Columns
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)

# Backward-compatibility alias
RevReceiptVoucher = AccountVoucher


class RevSuspenseRegister(Base):
    __tablename__ = "rev_suspense_register"
    __table_args__ = {"schema": "ifms_budget"}

    suspense_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recon_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id"), nullable=False)
    suspense_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'UNRECONCILED_SUSPENSE', 'RAT_SUSPENSE', 'AMOUNT_MISMATCH_SUSPENSE', 'DUPLICATE_SUSPENSE'
    suspense_head_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(17, 2), nullable=False)
    ageing_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN", nullable=False) # 'OPEN', 'CLEARED', 'TRANSFERRED', 'WRITTEN_OFF'
    cleared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    clearing_remarks: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), onupdate=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")
