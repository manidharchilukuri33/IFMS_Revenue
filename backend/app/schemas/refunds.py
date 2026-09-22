from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class RefundVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    verification_id: int
    refund_id: int
    verification_type: str
    verification_result: str
    authority_name: Optional[str] = None
    verification_remarks: str
    verified_by: int
    verified_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class RefundBillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    bill_id: int
    bill_no: str
    refund_id: int
    department_id: int
    ddo_id: int
    pao_code: str
    bill_amount: Decimal
    debit_head_id: int
    status: str
    prepared_by: int
    prepared_at: datetime
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class RefundCaseCreate(BaseModel):
    refund_type: str = "NON_JUDICIAL_STAMP"
    case_no: Optional[str] = None
    applicant_name: str
    applicant_id_proof: Optional[str] = None
    applicant_bank_acc: Optional[str] = None
    bank_account_no: Optional[str] = None
    applicant_ifsc: Optional[str] = None
    ifsc_code: Optional[str] = None
    original_challan_no: str
    reconciled_original_amount: Optional[Decimal] = None
    claimed_amount: Decimal
    e_stamp_cert_no: Optional[str] = None
    shcil_certificate_no: Optional[str] = None
    court_order_no: Optional[str] = None
    override_reason: Optional[str] = None
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    workflow_status: Optional[str] = "DRAFT"

class RefundCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    refund_id: int
    case_no: str
    refund_type: str
    applicant_name: str
    applicant_id_proof: Optional[str] = None
    applicant_bank_acc: Optional[str] = None
    applicant_ifsc: Optional[str] = None
    original_challan_no: str
    recon_id: Optional[int] = None
    reconciled_original_amount: Decimal
    claimed_amount: Decimal
    refundable_amount: Decimal
    is_amount_override: bool
    override_reason: Optional[str] = None
    e_stamp_cert_no: Optional[str] = None
    court_order_no: Optional[str] = None
    current_stage: int
    stage_name: str
    pending_role: str
    status: str
    refund_bill_no: Optional[str] = None
    bill_prepared_by: Optional[int] = None
    bill_prepared_at: Optional[datetime] = None
    pao_approved_by: Optional[int] = None
    pao_approved_at: Optional[datetime] = None
    pao_remarks: Optional[str] = None
    epay_ref_no: Optional[str] = None
    epay_instructed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class RefundDetailResponse(BaseModel):
    case: RefundCaseResponse
    verifications: List[RefundVerificationResponse]
    bills: List[RefundBillResponse]
    checklist: List[str]
    timeline: List[dict]

class AdvanceStageRequest(BaseModel):
    action: str # 'VERIFY', 'RAISE_DEFICIENCY', 'PREPARE_BILL', 'APPROVE_PAO', 'EXECUTE_PAYMENT', 'REJECT'
    remarks: str
    verification_type: Optional[str] = None
    verification_result: Optional[str] = None
    authority_name: Optional[str] = None
    ddo_id: Optional[int] = None
    debit_head_id: Optional[int] = None
