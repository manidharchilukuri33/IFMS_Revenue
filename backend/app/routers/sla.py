from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.sla import (
    DemandLetterRequest,
    BankResponseRequest,
    PenaltyWaiverRequest,
)
from app.services.sla_service import SLAService

router = APIRouter(prefix="/api/sla", tags=["SLA & Penal Interest Management"])

@router.get("/claims", dependencies=[Depends(require_capability("nav.sla"))])
@router.get("/penal-claims", dependencies=[Depends(require_capability("nav.sla"))])
async def list_penal_claims(
    bank_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    min_delay_days: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await SLAService.get_penal_claims(
        db, bank_id, status, min_delay_days, search, limit, offset
    )

@router.get("/claims/{claim_id}", dependencies=[Depends(require_capability("nav.sla"))])
@router.get("/penal-claims/{claim_id}", dependencies=[Depends(require_capability("nav.sla"))])
async def get_penal_claim_detail(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await SLAService.get_penal_claim_detail(db, claim_id)

@router.post("/claims/{claim_id}/issue-demand", dependencies=[Depends(require_capability("penalty.letter"))])
@router.post("/claims/{claim_id}/demand-letter", dependencies=[Depends(require_capability("penalty.letter"))])
@router.post("/penal-claims/{claim_id}/demand-letter", dependencies=[Depends(require_capability("penalty.letter"))])
async def issue_demand_letter(
    claim_id: int,
    req: DemandLetterRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SLAService.issue_demand_letter(db, claim_id, req, user.user_id)

@router.post("/claims/{claim_id}/record-response", dependencies=[Depends(require_capability("penalty.response"))])
@router.post("/claims/{claim_id}/bank-response", dependencies=[Depends(require_capability("penalty.response"))])
@router.post("/penal-claims/{claim_id}/bank-response", dependencies=[Depends(require_capability("penalty.response"))])
async def record_bank_response(
    claim_id: int,
    req: BankResponseRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SLAService.record_bank_response(db, claim_id, req, user.user_id)

@router.post("/claims/{claim_id}/waiver", dependencies=[Depends(require_capability("penalty.waive"))])
@router.post("/penal-claims/{claim_id}/waiver", dependencies=[Depends(require_capability("penalty.waive"))])
async def approve_penalty_waiver(
    claim_id: int,
    req: PenaltyWaiverRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await SLAService.approve_penalty_waiver(db, claim_id, req, user.user_id)

