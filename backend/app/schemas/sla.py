from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class PenalLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    letter_id: int
    letter_no: str
    claim_id: int
    bank_id: int
    issued_date: date
    total_demand_amount: Decimal
    letter_content: str
    issued_by: int
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class PenalBankResponseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    response_id: int
    claim_id: int
    response_date: date
    response_type: str
    remitted_amount: Decimal
    bank_remarks: str
    recorded_by: int
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class PenalWaiverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    waiver_id: int
    claim_id: int
    waived_amount: Decimal
    waiver_ground: str
    sanction_order_ref: str
    waiver_remarks: str
    approved_by: int
    approved_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class PenalClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    claim_id: int
    claim_no: str
    recon_id: int
    scroll_item_id: int
    bank_id: int
    principal_amount: Decimal
    payment_mode: str
    base_date: date
    base_date_type: str
    bank_remittance_date: date
    actual_days: int
    permitted_days: int
    delay_days: int
    annual_rate_pct: Decimal
    penal_interest_computed: Decimal
    penal_interest_recovered: Decimal
    penal_interest_waived: Decimal
    penal_interest_outstanding: Decimal
    status: str
    letter_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class PenalClaimDetailResponse(BaseModel):
    claim: PenalClaimResponse
    letters: List[PenalLetterResponse]
    responses: List[PenalBankResponseResponse]
    waivers: List[PenalWaiverResponse]
    bank_context: Optional[dict] = None

class DemandLetterRequest(BaseModel):
    letter_content: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_address: Optional[str] = None
    remarks: Optional[str] = None

class BankResponseRequest(BaseModel):
    response_date: Optional[date] = None
    response_type: Optional[str] = "PAYMENT"
    remitted_amount: Optional[Decimal] = None
    recovered_amount: Optional[Decimal] = None
    bank_reference_no: Optional[str] = None
    remittance_date: Optional[date] = None
    bank_remarks: Optional[str] = None
    remarks: Optional[str] = None

class PenaltyWaiverRequest(BaseModel):
    waived_amount: Decimal
    waiver_ground: str
    sanction_order_ref: str
    waiver_remarks: str
