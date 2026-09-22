from typing import Optional, List, Any
from pydantic import BaseModel

class ReportDataset(BaseModel):
    report_id: str
    report_name: str
    report_group: str
    description: str
    headers: List[str]
    rows: List[List[Any]]
    money_columns: List[int]
    total_records: int
    summary_values: dict[str, Any] = {}

class AuditLogResponse(BaseModel):
    audit_id: int
    schema_name: str
    table_name: str
    operation: str
    row_pk: Optional[str] = None
    old_data: Optional[dict] = None
    new_data: Optional[dict] = None
    changed_by: Optional[int] = None
    user_name: Optional[str] = None
    changed_at: str
    txid: int
