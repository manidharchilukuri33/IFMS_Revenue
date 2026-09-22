from fastapi import APIRouter, Depends, Query, Header, UploadFile, File, Form
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rbac import require_capability, get_current_user, CurrentUser
from app.schemas.upload import BatchApproveRequest, SampleLoadRequest, CsvUploadPayload
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/upload", tags=["Upload & Staging"])

@router.get("/batches", dependencies=[Depends(require_capability("nav.upload"))])
async def list_batches(
    batch_type: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    st = batch_type or source_type
    res = await UploadService.get_batches(db, st, status, limit, offset)
    return res["items"]

@router.get("/batches/{batch_id}", dependencies=[Depends(require_capability("nav.upload"))])
async def get_batch_details(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
):
    res = await UploadService.get_batch_items(db, batch_id, limit=200)
    batch = res["batch"]
    portal_items = res["items"] if batch.batch_type == "PORTAL" else []
    bank_items = res["items"] if batch.batch_type == "BANK_SCROLL" else []
    rbi_items = res["items"] if batch.batch_type == "RBI_LUGGAGE" else []
    return {
        "batch": batch,
        "portal_items": portal_items,
        "bank_items": bank_items,
        "rbi_items": rbi_items,
        "rejections": res["rejections"]
    }

@router.post("/portal", dependencies=[Depends(require_capability("upload.portal"))])
async def upload_portal_json(
    payload: CsvUploadPayload,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UploadService.process_csv_upload(
        db=db,
        source_type="PORTAL",
        file_name=payload.filename,
        csv_text=payload.csv_content,
        user_id=user.user_id,
        auto_approve=False
    )

@router.post("/bank-scroll", dependencies=[Depends(require_capability("upload.bank"))])
async def upload_bank_json(
    payload: CsvUploadPayload,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UploadService.process_csv_upload(
        db=db,
        source_type="BANK_SCROLL",
        file_name=payload.filename,
        csv_text=payload.csv_content,
        user_id=user.user_id,
        auto_approve=False
    )

@router.post("/rbi-luggage", dependencies=[Depends(require_capability("upload.rbi"))])
async def upload_rbi_json(
    payload: CsvUploadPayload,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UploadService.process_csv_upload(
        db=db,
        source_type="RBI_LUGGAGE",
        file_name=payload.filename,
        csv_text=payload.csv_content,
        user_id=user.user_id,
        auto_approve=False
    )

@router.post("/file")
async def upload_csv_file(
    source_type: str = Form(...),
    file: UploadFile = File(...),
    auto_approve: bool = Form(False),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content_bytes = await file.read()
    csv_text = content_bytes.decode("utf-8", errors="replace")
    return await UploadService.process_csv_upload(
        db=db,
        source_type=source_type,
        file_name=file.filename or "uploaded.csv",
        csv_text=csv_text,
        user_id=user.user_id,
        auto_approve=auto_approve
    )

@router.post("/load-sample")
async def load_sample_dataset(
    req: SampleLoadRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UploadService.load_sample_dataset(
        db=db,
        sample_key=req.sample_key,
        auto_approve=req.auto_approve,
        user_id=user.user_id
    )

@router.post("/batches/{batch_id}/approve", dependencies=[Depends(require_capability("batch.approve"))])
async def approve_batch(
    batch_id: int,
    req: BatchApproveRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UploadService.approve_batch(
        db=db,
        batch_id=batch_id,
        checker_id=user.user_id,
        remarks=req.remarks or "Approved via UI"
    )

@router.delete("/batches/{batch_id}", dependencies=[Depends(require_capability("upload.portal"))])
async def delete_batch(
    batch_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await UploadService.delete_batch(
        db=db,
        batch_id=batch_id,
        user_id=user.user_id
    )

