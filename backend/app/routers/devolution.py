from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.devolution import (
    DevolutionClaimCreate,
    ApproveDevolutionRequest,
)
from app.services.devolution_service import DevolutionService

router = APIRouter(prefix="/api/devolution", tags=["Local Body Devolution"])

@router.get("/claims", dependencies=[Depends(require_capability("nav.devolution"))])
async def list_devolution_claims(
    local_body_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await DevolutionService.get_devolution_claims(
        db, local_body_id, status, search, limit, offset
    )

@router.post("/claims", dependencies=[Depends(require_capability("devolution.create"))])
async def create_devolution_claim(
    req: DevolutionClaimCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DevolutionService.create_devolution_claim(db, req, user.user_id)

@router.post("/compute", dependencies=[Depends(require_capability("devolution.create"))])
async def compute_devolution_claim(
    req: DevolutionClaimCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DevolutionService.create_devolution_claim(db, req, user.user_id)

@router.get("/claims/{claim_id}", dependencies=[Depends(require_capability("nav.devolution"))])
async def get_devolution_claim_detail(
    claim_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await DevolutionService.get_devolution_detail(db, claim_id)

@router.post("/claims/{claim_id}/approve", dependencies=[Depends(require_capability("devolution.approve"))])
@router.post("/claims/{claim_id}/issue-advice", dependencies=[Depends(require_capability("devolution.approve"))])
async def approve_devolution(
    claim_id: int,
    req: ApproveDevolutionRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DevolutionService.approve_and_generate_advice(db, claim_id, req, user.user_id)


