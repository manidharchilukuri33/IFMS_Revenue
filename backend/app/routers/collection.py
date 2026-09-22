from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.collection import ManualCollectionCreate, DepartmentalValidationRequest
from app.services.collection_service import CollectionService

router = APIRouter(prefix="/api/collection", tags=["Revenue Collection Register"])

@router.get("/transactions", dependencies=[Depends(require_capability("nav.collection"))])
async def list_transactions(
    source: Optional[str] = Query(None),
    dept: Optional[str] = Query(None),
    pao: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    page: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = CollectionService(db)
    actual_page = page if page else (offset // limit + 1)
    items, total = await svc.list_transactions(source, dept, pao, from_date, to_date, search, actual_page, limit)
    return {"total": total, "items": items}

@router.get("/transactions/{portal_item_id}", dependencies=[Depends(require_capability("nav.collection"))])
async def get_transaction_detail(
    portal_item_id: int,
    db: AsyncSession = Depends(get_db),
):
    svc = CollectionService(db)
    return await svc.get_transaction_detail(portal_item_id)

@router.post("/transactions", dependencies=[Depends(require_capability("collection.create"))])
@router.post("/manual-receipt", dependencies=[Depends(require_capability("collection.create"))])
async def create_manual_transaction(
    req: ManualCollectionCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CollectionService(db)
    return await svc.create_manual_receipt(req, user.user_id)

@router.post("/transactions/validate-departmental", dependencies=[Depends(require_capability("dept.validate"))])
async def validate_departmental(
    req: DepartmentalValidationRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = CollectionService(db)
    count = await svc.validate_departmental(req.item_ids, user.user_id)
    return {"status": "SUCCESS", "validated_count": count}

