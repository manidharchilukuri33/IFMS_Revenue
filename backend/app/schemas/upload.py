from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class UploadBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    batch_id: int
    batch_no: str
    batch_type: str
    source_filename: str
    file_size_bytes: int
    data_date: Optional[date] = None
    revenue_source_code: Optional[str] = None
    department_id: Optional[int] = None
    pao_code: Optional[str] = None
    bank_id: Optional[int] = None
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    control_total: Decimal
    status: str
    uploaded_by: int
    uploaded_at: datetime
    checker_user_id: Optional[int] = None
    checker_remarks: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class BatchApproveRequest(BaseModel):
    remarks: Optional[str] = "Approved by checker"

class BatchApprovalRequest(BaseModel):
    remarks: Optional[str] = "Approved by checker"

class BatchRejectionRequest(BaseModel):
    remarks: str

class SampleLoadRequest(BaseModel):
    sample_key: str = "portal"
    auto_approve: bool = False

class CsvUploadPayload(BaseModel):
    filename: str
    csv_content: str
    bank_code: Optional[str] = "SBI"

class RejectedRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rejection_id: int
    batch_id: Optional[int] = None
    batch_type: str
    source_filename: str
    file_row_number: int
    raw_csv_row: str
    failure_reasons: List[str]
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class BatchReviewResponse(BaseModel):
    batch: UploadBatchResponse
    rejected_rows: List[RejectedRowResponse]
    sample_records: List[dict]
