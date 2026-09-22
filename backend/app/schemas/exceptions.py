from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class ExceptionNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    note_id: int
    exception_id: int
    action_type: str
    note_text: str
    attachment_metadata: Optional[dict] = None
    created_by: int
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class ExceptionLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    letter_id: int
    letter_no: str
    exception_id: int
    recipient_type: str
    recipient_name: str
    recipient_address: Optional[str] = None
    letter_subject: str
    letter_body: str
    issued_date: date
    issued_by: int
    status: str
    created_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class ExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    exception_id: int
    exception_no: str
    recon_id: Optional[int] = None
    category: str
    severity: str
    status: str
    ownership_type: str
    assigned_user_id: Optional[int] = None
    due_date: date
    exception_detail: str
    resolution_reason: Optional[str] = None
    resolution_remarks: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    escalation_count: int
    last_escalated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[int] = 1
    org_branch_id: Optional[int] = 1
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    workflow_status: Optional[str] = "DRAFT"

class ExceptionDetailResponse(BaseModel):
    exception: ExceptionResponse
    notes: List[ExceptionNoteResponse]
    letters: List[ExceptionLetterResponse]
    recon_context: Optional[dict] = None

class ExceptionResolveRequest(BaseModel):
    resolution_reason: str
    resolution_remarks: str

# Alias for backwards compatibility
ResolveExceptionRequest = ExceptionResolveRequest

class DiscrepancyLetterCreate(BaseModel):
    recipient_type: str
    recipient_name: str
    recipient_address: Optional[str] = None
    letter_subject: str
    letter_body: str

# Alias for backwards compatibility
CreateLetterRequest = DiscrepancyLetterCreate

class BulkAssignRequest(BaseModel):
    exception_ids: List[int]
    assigned_user_id: int
