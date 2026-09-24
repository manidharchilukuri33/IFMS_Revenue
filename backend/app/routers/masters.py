from fastapi import APIRouter, Depends, Query, Path
from typing import Optional, List, Any
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
    DepartmentCreate,
    DepartmentUpdate,
    DdoCreate,
    DdoUpdate,
    TreasuryCreate,
    TreasuryUpdate,
    PaoCreate,
    PaoUpdate,
    ReconRuleCreate,
    ReconRuleUpdate,
)
from app.schemas.devolution import DevolutionRuleCreate
from app.services.master_service import MasterService

router = APIRouter(prefix="/api/masters", tags=["Masters & Configuration"])

# =============================================================================
# 1. DEPARTMENTS
# =============================================================================
@router.get("/departments", dependencies=[Depends(require_capability("nav.masters"))])
async def list_departments(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_departments(db, is_active)

@router.post("/departments", dependencies=[Depends(require_capability("masters.edit"))])
async def create_department(req: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_department(db, req)

@router.put("/departments/{dept_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_department(dept_id: int, req: DepartmentUpdate, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_department(db, dept_id, req)

# =============================================================================
# 2. PAOS
# =============================================================================
@router.get("/paos", dependencies=[Depends(require_capability("nav.masters"))])
@router.get("/pao", dependencies=[Depends(require_capability("nav.masters"))])
async def list_paos(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_paos(db, is_active)

@router.post("/paos", dependencies=[Depends(require_capability("masters.edit"))])
async def create_pao(req: PaoCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_pao(db, req)

@router.put("/paos/{pao_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_pao(pao_id: int, req: PaoUpdate, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_pao(db, pao_id, req)

# =============================================================================
# 3. DDOS
# =============================================================================
@router.get("/ddos", dependencies=[Depends(require_capability("nav.masters"))])
async def list_ddos(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_ddos(db, is_active)

@router.post("/ddos", dependencies=[Depends(require_capability("masters.edit"))])
async def create_ddo(req: DdoCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_ddo(db, req)

@router.put("/ddos/{ddo_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_ddo(ddo_id: int, req: DdoUpdate, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_ddo(db, ddo_id, req)

# =============================================================================
# 4. TREASURIES & BRANCHES
# =============================================================================
@router.get("/treasuries", dependencies=[Depends(require_capability("nav.masters"))])
async def list_treasuries(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_treasuries(db, is_active)

@router.post("/treasuries", dependencies=[Depends(require_capability("masters.edit"))])
async def create_treasury(req: TreasuryCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_treasury(db, req)

@router.put("/treasuries/{branch_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_treasury(branch_id: int, req: TreasuryUpdate, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_treasury(db, branch_id, req)

# =============================================================================
# 5. BANKS & BRANCHES
# =============================================================================
@router.get("/banks", dependencies=[Depends(require_capability("nav.masters"))])
async def list_banks(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_banks(db, is_active)

@router.post("/banks", dependencies=[Depends(require_capability("masters.edit"))])
async def create_bank(req: AgencyBankCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_bank(db, req)

@router.put("/banks/{bank_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_bank(bank_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_bank(db, bank_id, req)

@router.get("/branches", dependencies=[Depends(require_capability("nav.masters"))])
async def list_branches(bank_id: Optional[int] = Query(None), is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_branches(db, bank_id, is_active)

@router.post("/branches", dependencies=[Depends(require_capability("masters.edit"))])
async def create_branch(req: BankBranchCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_branch(db, req)

@router.put("/branches/{branch_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_branch(branch_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_branch(db, branch_id, req)

# =============================================================================
# 6. REVENUE PORTALS
# =============================================================================
@router.get("/portals", dependencies=[Depends(require_capability("nav.masters"))])
async def list_portals(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_portals(db, is_active)

@router.post("/portals", dependencies=[Depends(require_capability("masters.edit"))])
async def create_portal(req: DeptPortalCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_portal(db, req)

@router.put("/portals/{portal_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_portal(portal_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_portal(db, portal_id, req)

# =============================================================================
# 7. REVENUE SOURCES
# =============================================================================
@router.get("/sources", dependencies=[Depends(require_capability("nav.masters"))])
async def list_sources(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_sources(db, is_active)

@router.post("/sources", dependencies=[Depends(require_capability("masters.edit"))])
async def create_source(req: RevenueSourceCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_source(db, req)

@router.put("/sources/{source_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_source(source_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_source(db, source_id, req)

# =============================================================================
# 8. LOCAL BODIES
# =============================================================================
@router.get("/local-bodies", dependencies=[Depends(require_capability("nav.masters"))])
async def list_local_bodies(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_local_bodies(db, is_active)

@router.post("/local-bodies", dependencies=[Depends(require_capability("masters.edit"))])
async def create_local_body(req: LocalBodyCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_local_body(db, req)

@router.put("/local-bodies/{local_body_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_local_body(local_body_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_local_body(db, local_body_id, req)

# =============================================================================
# 9. CHART OF ACCOUNTS / RECEIPT HEADS
# =============================================================================
@router.get("/chart-of-accounts", dependencies=[Depends(require_capability("nav.masters"))])
@router.get("/heads", dependencies=[Depends(require_capability("nav.masters"))])
async def list_chart_of_accounts(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_chart_of_accounts(db, is_active)

@router.post("/heads", dependencies=[Depends(require_capability("masters.edit"))])
@router.post("/chart-of-accounts", dependencies=[Depends(require_capability("masters.edit"))])
async def create_chart_of_account(req: dict, db: AsyncSession = Depends(get_db)):
    class CoaPayload:
        coa_code = req.get("coa_code") or req.get("code")
        coa_name = req.get("coa_name") or req.get("name") or req.get("description")
        major_head_id = int(req.get("major_head_id") or 40)
        sub_major_head_id = int(req.get("sub_major_head_id") or 0)
        minor_head_id = int(req.get("minor_head_id") or 102)
        account_nature = req.get("account_nature") or "REVENUE"
        is_active = req.get("is_active", True)
    return await MasterService.create_chart_of_account(db, CoaPayload)

@router.put("/heads/{coa_id}", dependencies=[Depends(require_capability("masters.edit"))])
@router.put("/chart-of-accounts/{coa_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_chart_of_account(coa_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_chart_of_account(db, coa_id, req)

# =============================================================================
# 10. RECONCILIATION MATCHING RULES
# =============================================================================
@router.get("/rules", dependencies=[Depends(require_capability("nav.masters"))])
async def list_recon_rules(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_recon_rules(db, is_active)

@router.post("/rules", dependencies=[Depends(require_capability("masters.edit"))])
async def create_recon_rule(req: ReconRuleCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_recon_rule(db, req)

@router.put("/rules/{rule_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_recon_rule(rule_id: int, req: ReconRuleUpdate, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_recon_rule(db, rule_id, req)

# =============================================================================
# 11. BANK SLA & PENAL INTEREST RULES
# =============================================================================
@router.get("/sla-rules", dependencies=[Depends(require_capability("nav.masters"))])
async def list_sla_rules(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_sla_rules(db, is_active)

@router.post("/sla-rules", dependencies=[Depends(require_capability("masters.edit"))])
async def create_sla_rule(req: SLARuleCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_sla_rule(db, req)

@router.put("/sla-rules/{sla_rule_id}", dependencies=[Depends(require_capability("masters.edit"))])
async def update_sla_rule(sla_rule_id: int, req: dict, db: AsyncSession = Depends(get_db)):
    return await MasterService.update_sla_rule(db, sla_rule_id, req)

# =============================================================================
# 12. DEVOLUTION RULES
# =============================================================================
@router.get("/devolution-rules", dependencies=[Depends(require_capability("nav.masters"))])
async def list_devolution_rules(is_active: Optional[bool] = Query(None), db: AsyncSession = Depends(get_db)):
    return await MasterService.get_devolution_rules(db, is_active)

@router.post("/devolution-rules", dependencies=[Depends(require_capability("masters.edit"))])
async def create_devolution_rule(req: DevolutionRuleCreate, db: AsyncSession = Depends(get_db)):
    return await MasterService.create_devolution_rule(db, req)

# =============================================================================
# 13. SYSTEM CONFIGURATION
# =============================================================================
@router.get("/system-config", dependencies=[Depends(require_capability("nav.masters"))])
@router.get("/config", dependencies=[Depends(require_capability("nav.masters"))])
async def get_system_config(db: AsyncSession = Depends(get_db)):
    return await MasterService.get_system_config(db)

@router.put("/system-config", dependencies=[Depends(require_capability("masters.edit"))])
@router.put("/config", dependencies=[Depends(require_capability("masters.edit"))])
@router.post("/system-config", dependencies=[Depends(require_capability("masters.edit"))])
@router.post("/config", dependencies=[Depends(require_capability("masters.edit"))])
async def update_system_config(
    req: dict,
    db: AsyncSession = Depends(get_db),
):
    return await MasterService.update_system_config(db, req)
