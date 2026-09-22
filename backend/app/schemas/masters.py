from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

# Bank Schemas
class BankBase(BaseModel):
    bank_code: str
    bank_name: str
    clearing_account_no: Optional[str] = None
    nodal_officer_name: Optional[str] = None
    nodal_officer_email: Optional[str] = None
    nodal_officer_phone: Optional[str] = None
    is_active: bool = True
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "ACTIVE"

class BankCreate(BankBase):
    pass

class BankUpdate(BaseModel):
    bank_name: Optional[str] = None
    clearing_account_no: Optional[str] = None
    nodal_officer_name: Optional[str] = None
    nodal_officer_email: Optional[str] = None
    nodal_officer_phone: Optional[str] = None
    is_active: Optional[bool] = None
    workflow_status: Optional[str] = None

class BankResponse(BankBase):
    model_config = ConfigDict(from_attributes=True)
    bank_id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

# Branch Schemas
class BranchBase(BaseModel):
    bank_id: int
    branch_code: str
    branch_name: str
    ifsc_code: str
    city: Optional[str] = None
    is_active: bool = True
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "ACTIVE"

class BranchCreate(BranchBase):
    pass

class BranchResponse(BranchBase):
    model_config = ConfigDict(from_attributes=True)
    branch_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

# Portal Schemas
class PortalBase(BaseModel):
    portal_code: str
    portal_name: str
    department_id: int
    api_endpoint: Optional[str] = None
    technical_contact: Optional[str] = None
    is_active: bool = True
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class PortalCreate(PortalBase):
    pass

class PortalResponse(PortalBase):
    model_config = ConfigDict(from_attributes=True)
    portal_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

# Source Schemas
class SourceBase(BaseModel):
    source_code: str
    source_name: str
    department_id: int
    default_pao_code: str
    portal_id: int
    default_receipt_head_id: int
    allowed_payment_modes: List[str] = ["NETBANKING", "UPI", "CARD", "CASH", "CHEQUE"]
    match_key_precedence: List[str] = ["CIN", "CHALLAN_NO", "CPIN", "PORTAL_TXN_ID"]
    sla_rule_id: Optional[int] = None
    is_tax_revenue: bool = True
    is_active: bool = True
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class SourceCreate(SourceBase):
    pass

class SourceResponse(SourceBase):
    model_config = ConfigDict(from_attributes=True)
    source_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

# SLA Rule Schemas
class SlaRuleBase(BaseModel):
    rule_code: str
    rule_name: str
    payment_mode: str
    allowed_remittance_days: int = 1
    grace_days: int = 0
    annual_penal_rate_pct: Decimal = Decimal("12.00")
    calculation_basis: str = "ACTUAL_365"
    base_date_type: str = "PAYMENT_DATE"
    min_recovery_threshold: Decimal = Decimal("10.00")
    is_active: bool = True
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class SlaRuleCreate(SlaRuleBase):
    pass

class SlaRuleResponse(SlaRuleBase):
    model_config = ConfigDict(from_attributes=True)
    sla_rule_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

# Local Body Schemas
class LocalBodyBase(BaseModel):
    local_body_code: str
    local_body_name: str
    body_type: str = "MUNICIPAL_CORP"
    bank_account_no: str
    bank_name: str
    ifsc_code: str
    is_active: bool = True
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class LocalBodyCreate(LocalBodyBase):
    pass

class LocalBodyResponse(LocalBodyBase):
    model_config = ConfigDict(from_attributes=True)
    local_body_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

# System Config Schemas
class SystemConfigBase(BaseModel):
    demo_business_date: date
    current_financial_year: str
    amount_tolerance: Decimal
    date_tolerance_days: int
    default_penal_rate_pct: Decimal
    penal_day_basis: int
    exception_escalation_days: int
    suspense_head_id: Optional[int] = None
    rat_suspense_head_id: Optional[int] = None
    bank_clearing_head_id: Optional[int] = None
    refund_deduct_head_id: Optional[int] = None
    devolution_expenditure_head_id: Optional[int] = None
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class SystemConfigUpdate(BaseModel):
    demo_business_date: Optional[date] = None
    current_financial_year: Optional[str] = None
    amount_tolerance: Optional[Decimal] = None
    date_tolerance_days: Optional[int] = None
    default_penal_rate_pct: Optional[Decimal] = None
    penal_day_basis: Optional[int] = None
    exception_escalation_days: Optional[int] = None
    suspense_head_id: Optional[int] = None
    rat_suspense_head_id: Optional[int] = None
    bank_clearing_head_id: Optional[int] = None
    refund_deduct_head_id: Optional[int] = None
    devolution_expenditure_head_id: Optional[int] = None
    workflow_status: Optional[str] = None

class SystemConfigResponse(SystemConfigBase):
    model_config = ConfigDict(from_attributes=True)
    config_id: int
    updated_at: datetime
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

# Schema Aliases
AgencyBankCreate = BankCreate
BankBranchCreate = BranchCreate
DeptPortalCreate = PortalCreate
RevenueSourceCreate = SourceCreate
SLARuleCreate = SlaRuleCreate
