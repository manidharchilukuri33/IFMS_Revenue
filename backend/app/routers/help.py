from fastapi import APIRouter, Response
from app.services.upload_service import SAMPLE_CSVS

router = APIRouter(prefix="/api/help", tags=["Help & Sample Data"])

@router.get("/samples")
async def list_samples():
    return [
        {"key": "portal", "filename": "sample_portal_transactions.csv", "title": "Departmental portal / challan transactions", "note": "16 rows covering clean matches, split settlements, mismatch, portal-only and duplicate candidate."},
        {"key": "bank", "filename": "sample_agency_bank_scroll.csv", "title": "Agency bank payment scroll", "note": "19 rows across SBI / HDFC / ICICI / PNB including split settlements, duplicate line, late remittances."},
        {"key": "rbi", "filename": "sample_rbi_luggage_file.csv", "title": "RBI luggage file / Government account credit", "note": "18 confirmed credits to the Government account, including split credits and RAT credit."},
        {"key": "invalid", "filename": "sample_invalid_portal_file.csv", "title": "Invalid portal file (negative test)", "note": "4 deliberately defective rows — non-numeric amount, missing portal ID, unknown portal, invalid date."},
        {"key": "refund", "filename": "sample_refund_cases.csv", "title": "Refund cases", "note": "3 refund applications — non-judicial stamp, judicial stamp and unverified e-stamp."},
        {"key": "devolution", "filename": "sample_devolution_claims.csv", "title": "Devolution claims", "note": "2 local body revenue-share claims for stamp and transport collections."},
    ]

@router.get("/samples/{key}/download")
async def download_sample_file(key: str):
    csv_text = SAMPLE_CSVS.get(key)
    if not csv_text:
        return Response(status_code=404, content="Sample not found")

    filename = f"sample_{key}.csv"
    return Response(
        content=csv_text.strip(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
