from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class ManualCollectionCreate(BaseModel):
    portal_name: str = "MANUAL_PORTAL"
    revenue_source: str
    dept_code: str = "REV"
    pao_code: str = "PAO01"
    ddo_code: Optional[str] = "DDO01"
    challan_no: Optional[str] = None
    cpin: Optional[str] = None
    cin: Optional[str] = None
    payer_id: Optional[str] = None
    payer_name: str
    payment_date: date
    service_date: Optional[date] = None
    payment_mode: str = "NETBANKING"
    amount: Decimal
    receipt_head: str
    service_description: Optional[str] = None
    narration: Optional[str] = None
    penalty_amount: Decimal = Decimal("0.00")


class DepartmentalValidationRequest(BaseModel):
    portal_item_ids: List[int]

class PortalTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    portal_item_id: int
    batch_id: int
    portal_name: str
    revenue_source: str
    dept_code: str
    pao_code: str
    ddo_code: str
    portal_transaction_id: str
    challan_no: str
    cpin: Optional[str] = None
    cin: Optional[str] = None
    payer_id: Optional[str] = None
    payer_name: str
    payment_date: date
    service_date: date
    payment_mode: str
    amount: Decimal
    receipt_head: str
    service_description: Optional[str] = None
    penalty_amount: Decimal
    portal_status: str
    dept_validated: bool
    dept_validated_by: Optional[int] = None
    dept_validated_at: Optional[datetime] = None
    is_valid: bool
    is_duplicate: bool
    created_at: datetime
