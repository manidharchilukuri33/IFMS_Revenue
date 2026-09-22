from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RevRefundCase(Base):
    __tablename__ = "rev_refund_case"
    __table_args__ = {"schema": "ifms_budget"}

    refund_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    case_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    refund_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'NON_JUDICIAL_STAMP', 'JUDICIAL_STAMP'
    applicant_name: Mapped[str] = mapped_column(String(250), nullable=False)
    applicant_id_proof: Mapped[Optional[str]] = mapped_column(String(100))
    applicant_bank_acc: Mapped[Optional[str]] = mapped_column(String(50))
    applicant_ifsc: Mapped[Optional[str]] = mapped_column(String(20))
    original_challan_no: Mapped[str] = mapped_column(String(100), nullable=False)
    recon_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id"))
    reconciled_original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    refundable_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    is_amount_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[Optional[str]] = mapped_column(Text)
    e_stamp_cert_no: Mapped[Optional[str]] = mapped_column(String(100))
    court_order_no: Mapped[Optional[str]] = mapped_column(String(100))
    current_stage: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    stage_name: Mapped[str] = mapped_column(String(150), nullable=False)
    pending_role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Submitted", nullable=False)
    refund_bill_no: Mapped[Optional[str]] = mapped_column(String(50))
    bill_prepared_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    bill_prepared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pao_approved_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    pao_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    pao_remarks: Mapped[Optional[str]] = mapped_column(Text)
    epay_ref_no: Mapped[Optional[str]] = mapped_column(String(100))
    epay_instructed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), onupdate=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    verifications: Mapped[List["RevRefundVerification"]] = relationship("RevRefundVerification", back_populates="refund_case", cascade="all, delete-orphan")
    bills: Mapped[List["RevRefundBill"]] = relationship("RevRefundBill", back_populates="refund_case")

class RevRefundVerification(Base):
    __tablename__ = "rev_refund_verification"
    __table_args__ = {"schema": "ifms_budget"}

    verification_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    refund_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_refund_case.refund_id", ondelete="CASCADE"), nullable=False)
    verification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    verification_result: Mapped[str] = mapped_column(String(30), nullable=False) # 'Valid', 'Invalid', 'Not Found', 'Partially Valid'
    authority_name: Mapped[Optional[str]] = mapped_column(String(150))
    verification_remarks: Mapped[str] = mapped_column(Text, nullable=False)
    verified_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    refund_case: Mapped["RevRefundCase"] = relationship("RevRefundCase", back_populates="verifications")

class RevRefundBill(Base):
    __tablename__ = "rev_refund_bill"
    __table_args__ = {"schema": "ifms_budget"}

    bill_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bill_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    refund_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_refund_case.refund_id"), nullable=False)
    department_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.department.department_id"), nullable=False)
    ddo_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.ddo.ddo_id"), nullable=False)
    pao_code: Mapped[str] = mapped_column(String(30), nullable=False)
    bill_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    debit_head_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.chart_of_account.coa_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PREPARED", nullable=False)
    prepared_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    prepared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    refund_case: Mapped["RevRefundCase"] = relationship("RevRefundCase", back_populates="bills")
