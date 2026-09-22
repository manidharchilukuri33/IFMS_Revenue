from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability
from app.services.test_suite_service import TestSuiteService

router = APIRouter(prefix="/api/testsuite", tags=["Verification & Test Suite"])

@router.post("/run", dependencies=[Depends(require_capability("testsuite.run"))])
async def run_test_suite(db: AsyncSession = Depends(get_db)):
    return await TestSuiteService.run_all_tests(db)
