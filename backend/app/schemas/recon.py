from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class ReconRunRequest(BaseModel):
    business_date: Optional[date] = None
    source_id: Optional[int] = None
    source_code: Optional[str] = None
    department_code: Optional[str] = None
    dept_code: Optional[str] = None
    pao_code: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None

class ReconRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    run_id: int
    run_no: str
    business_date: date
    total_processed: int
    matched_count: int
    pending_count: int
    suspend_count: int
    rat_count: int
    mismatch_count: int
    duplicate_count: int
    under_investigation_count: int
    total_reconciled_amount: Decimal
    total_penal_interest: Decimal
    executed_by: int
    executed_at: datetime
    is_current: bool
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class ReconResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    recon_id: int
    rev_transaction_id: str
    run_id: int
    group_key: str
    match_key_type: str
    challan_no: Optional[str] = None
    cpin: Optional[str] = None
    cin: Optional[str] = None
    revenue_source: str
    dept_code: str
    pao_code: str
    receipt_head: str
    payer_name: Optional[str] = None
    portal_total: Decimal
    bank_total: Decimal
    rbi_total: Decimal
    amount_difference: Decimal
    date_variance_days: int
    sla_delay_days: int
    penal_interest_amount: Decimal
    rule_applied: str
    match_type: str
    status: str
    flags: List[str]
    match_reason: str
    booking_status: str
    is_manual_override: bool
    machine_status: Optional[str] = None
    portal_date: Optional[date] = None
    bank_date: Optional[date] = None
    rbi_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class ReconLegLinkageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    link_id: int
    recon_id: int
    leg_type: str
    portal_item_id: Optional[int] = None
    scroll_item_id: Optional[int] = None
    rbi_item_id: Optional[int] = None
    leg_amount: Decimal
    leg_reference_no: Optional[str] = None
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class ReconDetailResponse(BaseModel):
    result: ReconResultResponse
    linkages: List[ReconLegLinkageResponse]
    portal_details: Optional[dict] = None
    bank_details: Optional[List[dict]] = None
    rbi_details: Optional[List[dict]] = None
    overrides: Optional[List[dict]] = None
    notes: Optional[List[dict]] = None

class ReconOverrideProposeRequest(BaseModel):
    recon_id: Optional[int] = None
    override_status: Optional[str] = None
    proposed_status: Optional[str] = None
    override_reason: Optional[str] = None
    justification: Optional[str] = None

class ReconOverrideApproveRequest(BaseModel):
    override_id: Optional[int] = None
    recon_id: Optional[int] = None
    approved: Optional[bool] = True
    decision: Optional[str] = "APPROVED"
    remarks: Optional[str] = None

class OverrideProposalRequest(BaseModel):
    proposed_status: str
    justification: str

class OverrideDecisionRequest(BaseModel):
    decision: str
    remarks: Optional[str] = None

class AddNoteRequest(BaseModel):
    note_text: str
    action_type: str = "MANUAL_REMARK"

class ReconSolveRequest(BaseModel):
    recon_id: Optional[int] = None
    resolution_type: str = "MANUAL_MATCH" # 'MANUAL_MATCH', 'POST_TO_SUSPENSE', 'MARK_RESOLVED', 'SPLIT_MATCH', 'DISCREPANCY_NOTICE'
    target_status: str = "Matched" # 'Matched', 'Resolved', 'Suspend', 'RAT'
    remarks: str
    reference_no: Optional[str] = None
    suspense_head_code: Optional[str] = None
    adjust_amount: Optional[Decimal] = None

class ReconLetterSendRequest(BaseModel):
    recon_id: Optional[int] = None
    recipient_type: str = "AGENCY_BANK" # 'AGENCY_BANK', 'PAO_OFFICER', 'TREASURY_ADMIN', 'DDO', 'TAXPAYER', 'CUSTOM_OFFICER'
    recipient_name: str
    recipient_address: Optional[str] = None
    letter_subject: str
    letter_body: str
    target_role: Optional[str] = "PAO_CHECK"

