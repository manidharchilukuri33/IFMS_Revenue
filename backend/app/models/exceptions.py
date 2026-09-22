from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RevException(Base):
    __tablename__ = "rev_exception"
    __table_args__ = {"schema": "ifms_budget"}

    exception_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    exception_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    recon_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_recon_result.recon_id"))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False) # 'Critical', 'High', 'Medium', 'Low'
    status: Mapped[str] = mapped_column(String(30), default="Open", nullable=False) # 'Open', 'Assigned', 'Escalated', 'Resolved', 'Closed'
    ownership_type: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    exception_detail: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_reason: Mapped[Optional[str]] = mapped_column(String(150))
    resolution_remarks: Mapped[Optional[str]] = mapped_column(Text)
    resolved_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    escalation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), onupdate=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    notes: Mapped[List["RevExceptionNote"]] = relationship("RevExceptionNote", back_populates="exception", cascade="all, delete-orphan")
    letters: Mapped[List["RevExceptionLetter"]] = relationship("RevExceptionLetter", back_populates="exception")

class RevExceptionNote(Base):
    __tablename__ = "rev_exception_note"
    __table_args__ = {"schema": "ifms_budget"}

    note_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    exception_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_exception.exception_id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    exception: Mapped["RevException"] = relationship("RevException", back_populates="notes")

class RevExceptionLetter(Base):
    __tablename__ = "rev_exception_letter"
    __table_args__ = {"schema": "ifms_budget"}

    letter_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    letter_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    exception_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.rev_exception.exception_id"), nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    recipient_address: Mapped[Optional[str]] = mapped_column(Text)
    letter_subject: Mapped[str] = mapped_column(String(300), nullable=False)
    letter_body: Mapped[str] = mapped_column(Text, nullable=False)
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    issued_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ISSUED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.clock_timestamp(), nullable=False)
    organization_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.organization.organization_id"), default=1, nullable=False)
    org_branch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ifms_budget.branch.branch_id"), default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("ifms_budget.app_user.user_id"))
    workflow_status: Mapped[Optional[str]] = mapped_column(String(30), default="DRAFT")

    exception: Mapped["RevException"] = relationship("RevException", back_populates="letters")
