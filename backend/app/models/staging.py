from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RevUploadBatch(Base):
    __tablename__ = "rev_upload_batch"
    __table_args__ = {"schema": "ifms_budget"}

    batch_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    batch_type: Mapped[str] = mapped_column(String(30), nullable=False)  # 'PORTAL', 'BANK_SCROLL', 'RBI_LUGGAGE', 'MANUAL_ENTRY'
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    data_date: Mapped[Optional[date]] = mapped_column(Date)
    revenue_source_code: Mapped[Optional[str]] = mapped_column(String(30))
    department_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.department.department_id"))
    pao_code: Mapped[Optional[str]] = mapped_column(String(30))
    bank_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.agency_bank.bank_id"))
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    control_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_APPROVAL", nullable=False)  # 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'DELETED'
    uploaded_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    checker_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    checker_remarks: Mapped[Optional[str]] = mapped_column(Text)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    portal_items: Mapped[List["RevPortalTransactionStaging"]] = relationship("RevPortalTransactionStaging", back_populates="batch", cascade="all, delete-orphan")
    bank_items: Mapped[List["RevAgencyBankScrollStaging"]] = relationship("RevAgencyBankScrollStaging", back_populates="batch", cascade="all, delete-orphan")
    rbi_items: Mapped[List["RevRbiLuggageStaging"]] = relationship("RevRbiLuggageStaging", back_populates="batch", cascade="all, delete-orphan")
    rejected_rows: Mapped[List["RevUploadRejectedRow"]] = relationship("RevUploadRejectedRow", back_populates="batch", cascade="all, delete-orphan")

class RevPortalTransactionStaging(Base):
    __tablename__ = "rev_portal_transaction_staging"
    __table_args__ = {"schema": "ifms_budget"}

    portal_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_upload_batch.batch_id", ondelete="CASCADE"), nullable=False)
    portal_name: Mapped[str] = mapped_column(String(50), nullable=False)
    revenue_source: Mapped[str] = mapped_column(String(30), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(30), nullable=False)
    pao_code: Mapped[str] = mapped_column(String(30), nullable=False)
    ddo_code: Mapped[str] = mapped_column(String(30), nullable=False)
    portal_transaction_id: Mapped[str] = mapped_column(String(100), nullable=False)
    challan_no: Mapped[str] = mapped_column(String(100), nullable=False)
    cpin: Mapped[Optional[str]] = mapped_column(String(100))
    cin: Mapped[Optional[str]] = mapped_column(String(100))
    payer_id: Mapped[Optional[str]] = mapped_column(String(100))
    payer_name: Mapped[str] = mapped_column(String(250), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    receipt_head: Mapped[str] = mapped_column(String(100), nullable=False)
    service_description: Mapped[Optional[str]] = mapped_column(Text)
    penalty_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0.00, nullable=False)
    portal_status: Mapped[str] = mapped_column(String(30), default="PAID", nullable=False)
    dept_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dept_validated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    dept_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    batch: Mapped["RevUploadBatch"] = relationship("RevUploadBatch", back_populates="portal_items")

class RevAgencyBankScrollStaging(Base):
    __tablename__ = "rev_agency_bank_scroll_staging"
    __table_args__ = {"schema": "ifms_budget"}

    scroll_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_upload_batch.batch_id", ondelete="CASCADE"), nullable=False)
    scroll_no: Mapped[str] = mapped_column(String(100), nullable=False)
    scroll_date: Mapped[date] = mapped_column(Date, nullable=False)
    bank_code: Mapped[str] = mapped_column(String(20), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(30), nullable=False)
    revenue_source: Mapped[str] = mapped_column(String(30), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(30), nullable=False)
    pao_code: Mapped[str] = mapped_column(String(30), nullable=False)
    challan_no: Mapped[str] = mapped_column(String(100), nullable=False)
    cpin: Mapped[Optional[str]] = mapped_column(String(100))
    cin: Mapped[Optional[str]] = mapped_column(String(100))
    bank_reference_no: Mapped[str] = mapped_column(String(100), nullable=False)
    utr_no: Mapped[Optional[str]] = mapped_column(String(100))
    payer_id: Mapped[Optional[str]] = mapped_column(String(100))
    payer_name: Mapped[str] = mapped_column(String(250), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_received_date: Mapped[date] = mapped_column(Date, nullable=False)
    instrument_realization_date: Mapped[Optional[date]] = mapped_column(Date)
    bank_remittance_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    receipt_head: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_status: Mapped[str] = mapped_column(String(30), default="REMITTED", nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    batch: Mapped["RevUploadBatch"] = relationship("RevUploadBatch", back_populates="bank_items")

class RevRbiLuggageStaging(Base):
    __tablename__ = "rev_rbi_luggage_staging"
    __table_args__ = {"schema": "ifms_budget"}

    rbi_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_upload_batch.batch_id", ondelete="CASCADE"), nullable=False)
    file_reference_no: Mapped[str] = mapped_column(String(100), nullable=False)
    luggage_date: Mapped[date] = mapped_column(Date, nullable=False)
    rbi_reference_no: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_code: Mapped[str] = mapped_column(String(20), nullable=False)
    govt_account_no: Mapped[str] = mapped_column(String(50), nullable=False)
    rbi_credit_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    receipt_head: Mapped[str] = mapped_column(String(100), nullable=False)
    challan_no: Mapped[Optional[str]] = mapped_column(String(100))
    cpin: Mapped[Optional[str]] = mapped_column(String(100))
    cin: Mapped[Optional[str]] = mapped_column(String(100))
    utr_no: Mapped[Optional[str]] = mapped_column(String(100))
    rbi_status: Mapped[str] = mapped_column(String(30), default="CONFIRMED", nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    batch: Mapped["RevUploadBatch"] = relationship("RevUploadBatch", back_populates="rbi_items")

class RevUploadRejectedRow(Base):
    __tablename__ = "rev_upload_rejected_row"
    __table_args__ = {"schema": "ifms_budget"}

    rejection_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_upload_batch.batch_id", ondelete="CASCADE"))
    batch_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_csv_row: Mapped[Text] = mapped_column(Text, nullable=False)
    failure_reasons: Mapped[list] = mapped_column(ARRAY(String), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    batch: Mapped["RevUploadBatch"] = relationship("RevUploadBatch", back_populates="rejected_rows")
