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

# Department Schemas
class DepartmentCreate(BaseModel):
    department_code: str
    department_name: str
    department_type: Optional[str] = "DEPARTMENT"
    head_of_department: Optional[str] = None
    is_active: bool = True

class DepartmentUpdate(BaseModel):
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    department_type: Optional[str] = None
    head_of_department: Optional[str] = None
    is_active: Optional[bool] = None

# DDO Schemas
class DdoCreate(BaseModel):
    ddo_code: str
    ddo_name: str
    department_id: Optional[int] = 1
    dept_code: Optional[str] = None
    treasury_code: Optional[str] = "TRY-DELHI"
    ddo_type: Optional[str] = "REGULAR"
    is_active: bool = True

class DdoUpdate(BaseModel):
    ddo_name: Optional[str] = None
    department_id: Optional[int] = None
    treasury_code: Optional[str] = None
    ddo_type: Optional[str] = None
    is_active: Optional[bool] = None

# Treasury Schemas
class TreasuryCreate(BaseModel):
    branch_code: str
    branch_name: str
    branch_type: Optional[str] = "TREASURY"
    treasury_code: Optional[str] = None
    city: Optional[str] = "Delhi"
    is_active: bool = True

class TreasuryUpdate(BaseModel):
    branch_name: Optional[str] = None
    branch_type: Optional[str] = None
    treasury_code: Optional[str] = None
    city: Optional[str] = None
    is_active: Optional[bool] = None

# PAO Schemas
class PaoCreate(BaseModel):
    pao_code: str
    pao_name: str
    dept_code: Optional[str] = None
    treasury_code: Optional[str] = "TRY-DELHI"
    is_active: bool = True

class PaoUpdate(BaseModel):
    pao_name: Optional[str] = None
    dept_code: Optional[str] = None
    treasury_code: Optional[str] = None
    is_active: Optional[bool] = None

# Recon Rule Schemas
class ReconRuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    priority: int = 1
    primary_match_keys: str
    amount_tolerance: Decimal = Decimal("0.01")
    date_tolerance_days: int = 2
    matching_mode: str = "THREE_WAY_EXACT"
    outcome_status: str = "Matched"
    is_active: bool = True

class ReconRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    priority: Optional[int] = None
    primary_match_keys: Optional[str] = None
    amount_tolerance: Optional[Decimal] = None
    date_tolerance_days: Optional[int] = None
    matching_mode: Optional[str] = None
    outcome_status: Optional[str] = None
    is_active: Optional[bool] = None

# Generic Update Schemas
class GeneralMasterUpdate(BaseModel):
    name: Optional[str] = None
    desc: Optional[str] = None
    is_active: Optional[bool] = None
    extra: Optional[dict] = None
