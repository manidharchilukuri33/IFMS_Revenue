from fastapi import APIRouter, Depends, Body
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.services.master_service import MasterService
from app.services.upload_service import UploadService
from app.services.recon_engine import ReconEngine
from app.services.notification_service import notify_system

router = APIRouter(prefix="/api/config", tags=["System Configuration"])

@router.get("", dependencies=[Depends(require_capability("nav.masters"))])
async def get_config(db: AsyncSession = Depends(get_db)):
    return await MasterService.get_system_config(db)

@router.post("", dependencies=[Depends(require_capability("config.edit"))])
async def update_config(payload: Dict[str, str] = Body(...), db: AsyncSession = Depends(get_db)):
    return await MasterService.update_system_config(db, payload)

@router.post("/bizdate", dependencies=[Depends(require_capability("bizdate.edit"))])
async def update_bizdate(payload: Dict[str, str] = Body(...), db: AsyncSession = Depends(get_db)):
    biz_date = payload.get("bizDate") or payload.get("biz_date")
    if not biz_date:
        biz_date = "2026-09-15"
    return await MasterService.update_system_config(db, {"bizDate": biz_date})

@router.post("/reset-demo", dependencies=[Depends(require_capability("data.reset"))])
async def reset_demo_data(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tables = [
        'rev_penal_waiver',
        'rev_penal_bank_response',
        'rev_penal_letter',
        'rev_penal_claim',
        'account_voucher',
        'rev_suspense_register',
        'rev_exception_note',
        'rev_exception_letter',
        'rev_exception',
        'rev_refund_bill',
        'rev_refund_verification',
        'rev_refund_case',
        'rev_devolution_advice',
        'rev_devolution_claim',
        'rev_recon_override',
        'rev_recon_leg_linkage',
        'rev_recon_result',
        'rev_recon_run',
        'rev_portal_transaction_staging',
        'rev_agency_bank_scroll_staging',
        'rev_rbi_luggage_staging',
        'rev_upload_rejected_row',
        'rev_upload_batch',
        'rev_system_notifications',
    ]
    for t in tables:
        await db.execute(text(f'DELETE FROM ifms_budget.{t}'))
    await db.commit()

    # Load sample batches
    await UploadService.load_sample_dataset(db, 'portal', auto_approve=True, user_id=user.user_id)
    await UploadService.load_sample_dataset(db, 'bank', auto_approve=True, user_id=user.user_id)
    await UploadService.load_sample_dataset(db, 'rbi', auto_approve=True, user_id=user.user_id)

    # Run recon
    recon_res = await ReconEngine.run_3way_reconciliation(db=db, user_id=user.user_id)
    await notify_system(
        db,
        title='Demo environment ready',
        text='16 portal, 19 bank and 18 RBI records loaded and reconciled. 6 exception(s) raised.',
        level='ok',
        target_role='ALL',
        action_module='system',
        reference_id='RESET_DEMO',
    )
    await db.commit()

    return {
        "status": "SUCCESS",
        "message": "Demo data reset, reloaded, and reconciled successfully.",
        "recon_summary": recon_res
    }

