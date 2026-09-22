from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel

class CitizenTrackResponse(BaseModel):
    case_no: str
    refund_type: str
    applicant_name: str
    original_challan_no: str
    claimed_amount: Decimal
    refundable_amount: Decimal
    status: str
    current_stage: int
    total_stages: int
    stage_name: str
    pending_role: str
    application_date: datetime
    last_update: datetime
    masked_account: str
    epay_ref_no: Optional[str] = None
    timeline_steps: List[dict]
