from fastapi import APIRouter, Depends, Query, Header
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.recon import (
    ReconRunRequest,
    ReconOverrideProposeRequest,
    ReconOverrideApproveRequest,
)
from app.services.recon_engine import ReconEngine, ReconEngineService

router = APIRouter(prefix="/api/recon", tags=["Reconciliation Engine"])

@router.post("/run", dependencies=[Depends(require_capability("recon.run"))])
async def run_reconciliation(
    req: ReconRunRequest = ReconRunRequest(),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ReconEngine.run_3way_reconciliation(
        db=db,
        source_id=req.source_id,
        business_date=req.business_date,
        user_id=user.user_id
    )

@router.get("/results", dependencies=[Depends(require_capability("nav.recon"))])
async def list_recon_results(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    source_id: Optional[int] = Query(None),
    match_rule_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await ReconEngine.get_recon_results(
        db, status, source_id, match_rule_id, search, limit, offset
    )

@router.get("/results/{recon_id}", dependencies=[Depends(require_capability("nav.recon"))])
async def get_recon_detail(
    recon_id: int,
    db: AsyncSession = Depends(get_db),
):
    svc = ReconEngineService(db)
    det = await svc.get_result_detail(recon_id)
    # Return formatted structure for frontend drawer
    return {
        "recon": det["result"],
        "linkages": det["linkages"],
        "portal_legs": [det["portal_details"]] if det["portal_details"] else [],
        "bank_legs": det["bank_details"] or [],
        "rbi_legs": det["rbi_details"] or [],
        "overrides": det["overrides"],
    }

@router.post("/override/propose", dependencies=[Depends(require_capability("override.propose"))])
async def propose_override_root(
    req: ReconOverrideProposeRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recon_id = req.recon_id or 1
    st = req.proposed_status or req.override_status or "Matched"
    reason = req.justification or req.override_reason or "Propose manual match"
    return await ReconEngine.propose_manual_override(
        db, recon_id, st, reason, user.user_id
    )

@router.post("/override/decide", dependencies=[Depends(require_capability("override.approve"))])
async def decide_override_root(
    req: ReconOverrideApproveRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = ReconEngineService(db)
    dec = req.decision or ("APPROVED" if req.approved else "REJECTED")
    return await svc.decide_override(
        recon_id=req.recon_id,
        decision=dec,
        remarks=req.remarks,
        user_id=user.user_id,
        override_id=req.override_id
    )


@router.post("/results/{recon_id}/propose-override", dependencies=[Depends(require_capability("override.propose"))])
async def propose_override(
    recon_id: int,
    req: ReconOverrideProposeRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    st = req.proposed_status or req.override_status or "Matched"
    reason = req.justification or req.override_reason or "Propose manual match"
    return await ReconEngine.propose_manual_override(
        db, recon_id, st, reason, user.user_id
    )

@router.post("/results/{recon_id}/approve-override", dependencies=[Depends(require_capability("override.approve"))])
async def approve_override(
    recon_id: int,
    req: ReconOverrideApproveRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    approved = req.approved if req.approved is not None else (req.decision == "APPROVED")
    return await ReconEngine.approve_manual_override(
        db, recon_id, approved, req.remarks, user.user_id
    )
