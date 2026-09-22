from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RevReconRun(Base):
    __tablename__ = "rev_recon_run"
    __table_args__ = {"schema": "ifms_budget"}

    run_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    business_date: Mapped[date] = mapped_column(Date, nullable=False)
    scope_filters: Mapped[Optional[dict]] = mapped_column(JSONB)
    total_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    suspend_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rat_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mismatch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    under_investigation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_reconciled_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    total_penal_interest: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    executed_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    results: Mapped[List["RevReconResult"]] = relationship("RevReconResult", back_populates="run", cascade="all, delete-orphan")

class RevReconResult(Base):
    __tablename__ = "rev_recon_result"
    __table_args__ = {"schema": "ifms_budget"}

    recon_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rev_transaction_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_run.run_id"), nullable=False)
    group_key: Mapped[str] = mapped_column(String(255), nullable=False)
    match_key_type: Mapped[str] = mapped_column(String(50), nullable=False)
    challan_no: Mapped[Optional[str]] = mapped_column(String(100))
    cpin: Mapped[Optional[str]] = mapped_column(String(100))
    cin: Mapped[Optional[str]] = mapped_column(String(100))
    revenue_source: Mapped[str] = mapped_column(String(30), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(30), nullable=False)
    pao_code: Mapped[str] = mapped_column(String(30), nullable=False)
    receipt_head: Mapped[str] = mapped_column(String(100), nullable=False)
    payer_name: Mapped[Optional[str]] = mapped_column(String(250))
    portal_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    bank_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    rbi_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    amount_difference: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    date_variance_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_delay_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    penal_interest_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    rule_applied: Mapped[str] = mapped_column(String(30), nullable=False)
    match_type: Mapped[str] = mapped_column(String(50), default="One-to-One", nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    flags: Mapped[list] = mapped_column(ARRAY(String), default=[], nullable=False)
    match_reason: Mapped[str] = mapped_column(Text, nullable=False)
    booking_status: Mapped[str] = mapped_column(String(30), default="UNBOOKED", nullable=False)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    machine_status: Mapped[Optional[str]] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), onupdate=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    run: Mapped["RevReconRun"] = relationship("RevReconRun", back_populates="results")
    linkages: Mapped[List["RevReconLegLinkage"]] = relationship("RevReconLegLinkage", back_populates="recon_result", cascade="all, delete-orphan")
    overrides: Mapped[List["RevReconOverride"]] = relationship("RevReconOverride", back_populates="recon_result")

class RevReconLegLinkage(Base):
    __tablename__ = "rev_recon_leg_linkage"
    __table_args__ = {"schema": "ifms_budget"}

    link_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recon_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id", ondelete="CASCADE"), nullable=False)
    leg_type: Mapped[str] = mapped_column(String(20), nullable=False) # 'PORTAL', 'BANK_SCROLL', 'RBI_CREDIT'
    portal_item_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_portal_transaction_staging.portal_item_id"))
    scroll_item_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_agency_bank_scroll_staging.scroll_item_id"))
    rbi_item_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_rbi_luggage_staging.rbi_item_id"))
    leg_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    leg_reference_no: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    recon_result: Mapped["RevReconResult"] = relationship("RevReconResult", back_populates="linkages")

class RevReconOverride(Base):
    __tablename__ = "rev_recon_override"
    __table_args__ = {"schema": "ifms_budget"}

    override_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recon_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id"), nullable=False)
    original_machine_status: Mapped[str] = mapped_column(String(30), nullable=False)
    proposed_status: Mapped[str] = mapped_column(String(30), nullable=False)
    proposer_justification: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    proposed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    decision_status: Mapped[str] = mapped_column(String(30), default="PENDING_APPROVAL", nullable=False)
    checker_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    checker_remarks: Mapped[Optional[str]] = mapped_column(Text)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    recon_result: Mapped["RevReconResult"] = relationship("RevReconResult", back_populates="overrides")
