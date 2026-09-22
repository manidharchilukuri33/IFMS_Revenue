from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability
from app.schemas.masters import (
    AgencyBankCreate,
    BankBranchCreate,
    DeptPortalCreate,
    RevenueSourceCreate,
    SLARuleCreate,
    LocalBodyCreate,
)
from app.schemas.devolution import DevolutionRuleCreate
from app.services.master_service import MasterService

router = APIRouter(prefix="/api/masters", tags=["Masters & Configuration"])

@router.get("/banks", dependencies=[Depends(require_capability("nav.masters"))])
async def list_banks(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_banks(db, is_active)

@router.post("/banks", dependencies=[Depends(require_capability("masters.edit"))])
async def create_bank(req: AgencyBankCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_bank(db, req)

@router.get("/branches", dependencies=[Depends(require_capability("nav.masters"))])
async def list_branches(bank_id: Optional[int] = Query(None), is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_branches(db, bank_id, is_active)

@router.post("/branches", dependencies=[Depends(require_capability("masters.edit"))])
async def create_branch(req: BankBranchCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_branch(db, req)

@router.get("/portals", dependencies=[Depends(require_capability("nav.masters"))])
async def list_portals(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_portals(db, is_active)

@router.post("/portals", dependencies=[Depends(require_capability("masters.edit"))])
async def create_portal(req: DeptPortalCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_portal(db, req)

@router.get("/sources", dependencies=[Depends(require_capability("nav.masters"))])
async def list_sources(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_sources(db, is_active)

@router.post("/sources", dependencies=[Depends(require_capability("masters.edit"))])
async def create_source(req: RevenueSourceCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_source(db, req)

@router.get("/sla-rules", dependencies=[Depends(require_capability("nav.masters"))])
async def list_sla_rules(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_sla_rules(db, is_active)

@router.post("/sla-rules", dependencies=[Depends(require_capability("masters.edit"))])
async def create_sla_rule(req: SLARuleCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_sla_rule(db, req)

@router.get("/devolution-rules", dependencies=[Depends(require_capability("nav.masters"))])
async def list_devolution_rules(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_devolution_rules(db, is_active)

@router.post("/devolution-rules", dependencies=[Depends(require_capability("masters.edit"))])
async def create_devolution_rule(req: DevolutionRuleCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_devolution_rule(db, req)

@router.get("/local-bodies", dependencies=[Depends(require_capability("nav.masters"))])
async def list_local_bodies(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_local_bodies(db, is_active)

@router.post("/local-bodies", dependencies=[Depends(require_capability("masters.edit"))])
async def create_local_body(req: LocalBodyCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_local_body(db, req)

@router.get("/chart-of-accounts", dependencies=[Depends(require_capability("nav.masters"))])
async def list_chart_of_accounts(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_chart_of_accounts(db, is_active)

@router.get("/paos", dependencies=[Depends(require_capability("nav.masters"))])
@router.get("/pao", dependencies=[Depends(require_capability("nav.masters"))])
async def list_paos(db: AsyncSession = Depends(get_db)):
    return await MasterService.get_paos(db)

@router.get("/system-config", dependencies=[Depends(require_capability("nav.masters"))])
@router.get("/config", dependencies=[Depends(require_capability("nav.masters"))])
async def get_system_config(db: AsyncSession = Depends(get_db)):
    return await MasterService.get_system_config(db)

@router.put("/system-config", dependencies=[Depends(require_capability("masters.edit"))])
@router.post("/system-config", dependencies=[Depends(require_capability("masters.edit"))])
@router.post("/config", dependencies=[Depends(require_capability("masters.edit"))])
async def update_system_config(
    req: dict,
    db: AsyncSession = Depends(get_db),
):
    return await MasterService.update_system_config(db, req)

