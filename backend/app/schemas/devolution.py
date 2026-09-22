from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class DevolutionRuleCreate(BaseModel):
    rule_code: str
    local_body_id: int
    source_id: int
    receipt_head_id: int
    share_basis: str = "PERCENTAGE"
    share_value: Decimal
    valid_from: date
    valid_to: date
    description: Optional[str] = None
    is_active: bool = True
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class DevolutionRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    dev_rule_id: int
    rule_code: str
    local_body_id: int
    source_id: int
    receipt_head_id: int
    share_basis: str
    share_value: Decimal
    valid_from: date
    valid_to: date
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class DevolutionComputationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    comp_id: int
    claim_id: int
    recon_id: int
    receipt_date: date
    receipt_amount: Decimal
    share_pct: Decimal
    entitled_share: Decimal
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class DevolutionAdviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    advice_id: int
    advice_no: str
    claim_id: int
    local_body_id: int
    advice_date: date
    approved_amount: Decimal
    bank_account_no: str
    ifsc_code: str
    epay_ref_no: str
    debit_head_id: int
    signed_by: int
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class DevolutionClaimCreate(BaseModel):
    local_body_id: int
    source_id: int
    receipt_head_id: Optional[int] = 1
    period_from: date
    period_to: date
    claimed_amount: Optional[Decimal] = Decimal("0.00")
    dev_rule_id: Optional[int] = None
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class DevolutionClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    claim_id: int
    claim_no: str
    local_body_id: int
    source_id: int
    receipt_head_id: int
    dev_rule_id: Optional[int] = None
    period_from: date
    period_to: date
    eligible_collections: Decimal
    share_pct: Decimal
    computed_entitlement: Decimal
    claimed_amount: Decimal
    variance_amount: Decimal
    approved_amount: Decimal
    status: str
    scrutiny_remarks: Optional[str] = None
    bill_no: Optional[str] = None
    advice_no: Optional[str] = None
    epay_ref_no: Optional[str] = None
    settled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class DevolutionClaimDetailResponse(BaseModel):
    claim: DevolutionClaimResponse
    computations: List[DevolutionComputationResponse]
    advices: List[DevolutionAdviceResponse]
    local_body: Optional[dict] = None

class ApproveDevolutionRequest(BaseModel):
    approved_amount: Decimal
    scrutiny_remarks: Optional[str] = "Approved by Treasury Officer"
    debit_head_id: Optional[int] = 1
