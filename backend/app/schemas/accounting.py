from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class VoucherItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    item_id: Optional[int] = None
    voucher_id: int
    entry_type: str
    coa_id: int
    head_code: str
    head_description: str
    amount: Decimal
    created_at: Optional[datetime] = None
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "ACTIVE"

class AccountVoucherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    voucher_id: int
    sr_no: Optional[int] = None
    voucher_no: str
    voucher_type: str = "REVENUE_RECEIPT"
    voucher_date: date
    financial_year: str
    pao_code: str
    amount: Decimal = Decimal("0.00")
    debit_coa_id: int
    credit_coa_id: int
    debit_coa_code: Optional[str] = None
    debit_coa_name: Optional[str] = None
    credit_coa_code: Optional[str] = None
    credit_coa_name: Optional[str] = None
    demand_id: Optional[int] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    ddo_id: Optional[int] = None
    office_id: Optional[int] = None
    scheme_id: Optional[int] = None
    project_id: Optional[int] = None
    recon_id: Optional[int] = None
    bill_no: Optional[str] = None
    bill_date: Optional[date] = None
    payee_name: Optional[str] = None
    narration: str
    status: str
    prepared_by: Optional[int] = None
    prepared_at: Optional[datetime] = None
    checker_user_id: Optional[int] = None
    checker_remarks: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    penal_interest_amount: Optional[Decimal] = Decimal("0.00")
    sla_delay_days: Optional[int] = 0
    created_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "ACTIVE"

# Backward compatibility alias
ReceiptVoucherResponse = AccountVoucherResponse

class AccountVoucherDetailResponse(BaseModel):
    voucher: AccountVoucherResponse
    debit_head: Optional[Dict[str, Any]] = None
    credit_head: Optional[Dict[str, Any]] = None
    recon_context: Optional[Dict[str, Any]] = None
    journal_entries: Optional[List[Dict[str, Any]]] = None
    total_debit: Optional[Decimal] = None
    total_credit: Optional[Decimal] = None

ReceiptVoucherDetailResponse = AccountVoucherDetailResponse

class BulkVoucherCreateRequest(BaseModel):
    pao_code: Optional[str] = None

class BulkVoucherApproveRequest(BaseModel):
    remarks: Optional[str] = "Verified and approved by PAO Checker."

class SuspenseRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    suspense_id: int
    recon_id: int
    suspense_type: str
    suspense_head_id: int
    amount: Decimal
    ageing_days: int
    status: str
    cleared_at: Optional[datetime] = None
    clearing_remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "ACTIVE"
    suspense_head_code: Optional[str] = None
    suspense_head_name: Optional[str] = None
