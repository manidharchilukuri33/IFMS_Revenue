from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RevPenalClaim(Base):
    __tablename__ = "rev_penal_claim"
    __table_args__ = {"schema": "ifms_budget"}

    claim_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    claim_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    recon_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id"), nullable=False)
    scroll_item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_agency_bank_scroll_staging.scroll_item_id"), nullable=False)
    bank_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.agency_bank.bank_id"), nullable=False)
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    base_date: Mapped[date] = mapped_column(Date, nullable=False)
    base_date_type: Mapped[str] = mapped_column(String(30), nullable=False)
    bank_remittance_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_days: Mapped[int] = mapped_column(Integer, nullable=False)
    permitted_days: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_days: Mapped[int] = mapped_column(Integer, nullable=False)
    annual_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    penal_interest_computed: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    penal_interest_recovered: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    penal_interest_waived: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    penal_interest_outstanding: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPUTED", nullable=False) # 'COMPUTED', 'DEMAND_ISSUED', 'PARTIALLY_RECOVERED', 'RECOVERED', 'WAIVED'
    letter_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), onupdate=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    letters: Mapped[List["RevPenalLetter"]] = relationship("RevPenalLetter", back_populates="claim")
    responses: Mapped[List["RevPenalBankResponse"]] = relationship("RevPenalBankResponse", back_populates="claim")
    waivers: Mapped[List["RevPenalWaiver"]] = relationship("RevPenalWaiver", back_populates="claim")

class RevPenalLetter(Base):
    __tablename__ = "rev_penal_letter"
    __table_args__ = {"schema": "ifms_budget"}

    letter_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    letter_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_penal_claim.claim_id"), nullable=False)
    bank_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.agency_bank.bank_id"), nullable=False)
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_demand_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    letter_content: Mapped[str] = mapped_column(Text, nullable=False)
    issued_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    claim: Mapped["RevPenalClaim"] = relationship("RevPenalClaim", back_populates="letters")

class RevPenalBankResponse(Base):
    __tablename__ = "rev_penal_bank_response"
    __table_args__ = {"schema": "ifms_budget"}

    response_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_penal_claim.claim_id"), nullable=False)
    response_date: Mapped[date] = mapped_column(Date, nullable=False)
    response_type: Mapped[str] = mapped_column(String(50), nullable=False)
    remitted_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    bank_remarks: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    claim: Mapped["RevPenalClaim"] = relationship("RevPenalClaim", back_populates="responses")

class RevPenalWaiver(Base):
    __tablename__ = "rev_penal_waiver"
    __table_args__ = {"schema": "ifms_budget"}

    waiver_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    claim_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_penal_claim.claim_id"), nullable=False)
    waived_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    waiver_ground: Mapped[str] = mapped_column(String(200), nullable=False)
    sanction_order_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    waiver_remarks: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    claim: Mapped["RevPenalClaim"] = relationship("RevPenalClaim", back_populates="waivers")
