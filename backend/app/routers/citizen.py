from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.citizen_service import CitizenService

router = APIRouter(prefix="/api/citizen", tags=["Citizen Portal & Refund Tracking"])

@router.get("/track/{case_no}")
async def track_refund_application(
    case_no: str,
    db: AsyncSession = Depends(get_db),
):
    return await CitizenService.track_refund_case(db, case_no)
