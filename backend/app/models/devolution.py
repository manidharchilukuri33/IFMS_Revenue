from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RevDevolutionClaim(Base):
    __tablename__ = "rev_devolution_claim"
    __table_args__ = {"schema": "ifms_budget"}

    claim_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    claim_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    local_body_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_local_body.local_body_id"), nullable=False)
    source_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_revenue_source.source_id"), nullable=False)
    receipt_head_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)
    dev_rule_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_devolution_rule.dev_rule_id"))
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)
    eligible_collections: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    computed_entitlement: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    variance_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    approved_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Claim Received", nullable=False) # 'Claim Received', 'Bill Generated', 'Approved', 'Settled', 'Rejected'
    scrutiny_remarks: Mapped[Optional[str]] = mapped_column(Text)
    bill_no: Mapped[Optional[str]] = mapped_column(String(50))
    advice_no: Mapped[Optional[str]] = mapped_column(String(50))
    epay_ref_no: Mapped[Optional[str]] = mapped_column(String(100))
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), onupdate=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    computations: Mapped[List["RevDevolutionComputation"]] = relationship("RevDevolutionComputation", back_populates="claim", cascade="all, delete-orphan")
    advices: Mapped[List["RevDevolutionAdvice"]] = relationship("RevDevolutionAdvice", back_populates="claim")

class RevDevolutionComputation(Base):
    __tablename__ = "rev_devolution_computation"
    __table_args__ = {"schema": "ifms_budget"}

    comp_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_devolution_claim.claim_id", ondelete="CASCADE"), nullable=False)
    recon_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id"), nullable=False)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    entitled_share: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    claim: Mapped["RevDevolutionClaim"] = relationship("RevDevolutionClaim", back_populates="computations")

class RevDevolutionAdvice(Base):
    __tablename__ = "rev_devolution_advice"
    __table_args__ = {"schema": "ifms_budget"}

    advice_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    advice_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_devolution_claim.claim_id"), nullable=False)
    local_body_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_local_body.local_body_id"), nullable=False)
    advice_date: Mapped[date] = mapped_column(Date, nullable=False)
    approved_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    bank_account_no: Mapped[str] = mapped_column(String(50), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(20), nullable=False)
    epay_ref_no: Mapped[str] = mapped_column(String(100), nullable=False)
    debit_head_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)
    signed_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    claim: Mapped["RevDevolutionClaim"] = relationship("RevDevolutionClaim", back_populates="advices")
