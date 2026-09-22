from datetime import datetime, date
from typing import Optional
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Organization(Base):
    __tablename__ = "organization"
    __table_args__ = {"schema": "ifms_budget"}

    organization_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    organization_name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(50))
    organization_type: Mapped[str] = mapped_column(String(50), default="GOVERNMENT", nullable=False)
    registration_no: Mapped[Optional[str]] = mapped_column(String(100))
    pan_no: Mapped[Optional[str]] = mapped_column(String(20))
    gstin: Mapped[Optional[str]] = mapped_column(String(20))
    address_line1: Mapped[Optional[str]] = mapped_column(String(200))
    address_line2: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state_name: Mapped[Optional[str]] = mapped_column(String(100))
    country_name: Mapped[Optional[str]] = mapped_column(String(100), default="INDIA")
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class Branch(Base):
    __tablename__ = "branch"
    __table_args__ = {"schema": "ifms_budget"}

    branch_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), nullable=False)
    parent_branch_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"))
    branch_code: Mapped[str] = mapped_column(String(50), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(200), nullable=False)
    branch_type: Mapped[str] = mapped_column(String(50), default="HEAD_OFFICE", nullable=False)
    ddo_code: Mapped[Optional[str]] = mapped_column(String(50))
    treasury_code: Mapped[Optional[str]] = mapped_column(String(50))
    address_line1: Mapped[Optional[str]] = mapped_column(String(200))
    address_line2: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state_name: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class Department(Base):
    __tablename__ = "department"
    __table_args__ = {"schema": "ifms_budget"}

    department_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), nullable=False)
    parent_department_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.department.department_id"))
    department_code: Mapped[str] = mapped_column(String(50), nullable=False)
    department_name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_type: Mapped[str] = mapped_column(String(50), default="DEPARTMENT", nullable=False)
    administrative_branch_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class DDO(Base):
    __tablename__ = "ddo"
    __table_args__ = {"schema": "ifms_budget"}

    ddo_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), nullable=False)
    department_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.department.department_id"), nullable=False)
    demand_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.demand.demand_id"))
    branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), nullable=False)
    ddo_code: Mapped[str] = mapped_column(String(50), nullable=False)
    ddo_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ddo_type: Mapped[str] = mapped_column(String(50), default="REGULAR", nullable=False)
    ddo_officer_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    treasury_code: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class AppUser(Base):
    __tablename__ = "app_user"
    __table_args__ = {"schema": "ifms_budget"}

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), nullable=False)
    default_branch_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"))
    login_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    employee_code: Mapped[Optional[str]] = mapped_column(String(50))
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(150))
    mobile_no: Mapped[Optional[str]] = mapped_column(String(30))
    password_hash: Mapped[Optional[str]] = mapped_column(Text)
    auth_provider: Mapped[str] = mapped_column(String(50), default="LOCAL", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_from: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class ChartOfAccount(Base):
    __tablename__ = "chart_of_account"
    __table_args__ = {"schema": "ifms_budget"}

    coa_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    coa_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    coa_name: Mapped[str] = mapped_column(String(255), nullable=False)
    major_head_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sub_major_head_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    minor_head_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sub_head_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    detail_head_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    object_head_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_nature: Mapped[str] = mapped_column(String(30), nullable=False)
    is_posting_account: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, default=func.current_date(), nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class AuditChangeLog(Base):
    __tablename__ = "audit_change_log"
    __table_args__ = {"schema": "ifms_budget"}

    audit_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    schema_name: Mapped[str] = mapped_column(Text, nullable=False)
    table_name: Mapped[str] = mapped_column(Text, nullable=False)
    operation: Mapped[str] = mapped_column(String(1), nullable=False) # 'I', 'U', 'D'
    row_pk: Mapped[Optional[str]] = mapped_column(Text)
    old_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    changed_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    txid: Mapped[int] = mapped_column(BigInteger, default=func.txid_current(), nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class DocumentNumberSequence(Base):
    __tablename__ = "document_number_sequence"
    __table_args__ = {"schema": "ifms_budget"}

    sequence_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    last_number: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    padding_length: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="ACTIVE")

class SystemNotification(Base):
    __tablename__ = "rev_system_notifications"
    __table_args__ = {"schema": "ifms_budget"}

    notification_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    notification_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="info", nullable=False) # 'ok', 'warn', 'err', 'info'
    target_role: Mapped[Optional[str]] = mapped_column(String(50)) # e.g. 'PAO_CHECK', 'TRE_ADMIN', 'BANK_OPS', 'DDO', or NULL for all
    action_module: Mapped[Optional[str]] = mapped_column(String(50))
    reference_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")
