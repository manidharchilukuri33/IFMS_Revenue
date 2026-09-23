import csv
import io
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, desc, text
from app.models.staging import (
    RevUploadBatch, RevPortalTransactionStaging, RevAgencyBankScrollStaging,
    RevRbiLuggageStaging, RevUploadRejectedRow
)
from app.models.masters import RevAgencyBank, RevRevenueSource
from app.core.exceptions import NotFoundException, BusinessValidationException, InvalidStateTransitionException

SAMPLE_CSVS = {
    "portal": """portal_name,revenue_source,department_code,pao_code,ddo_code,portal_transaction_id,challan_no,cpin,cin,payer_id,payer_name,payment_date,service_date,payment_mode,amount,receipt_head,service_description,penalty_amount,portal_status
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-20260910-0001,CH-GST-10001,CPIN-10001,CIN-10001,GSTIN27ABCDE1234F1Z5,ABC Traders,2026-09-10,2026-09-10,NETBANKING,125000.00,0040-00-102-01-00-01,GST tax payment,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-20260910-0002,CH-GST-10002,CPIN-10002,CIN-10002,GSTIN27PQRSX6789K1Z2,Metro Supplies,2026-09-10,2026-09-10,UPI,78500.00,0040-00-102-01-00-01,GST tax payment,0.00,PAID
ESCIMS,EXCISE,EXCISE,PAO10,DDO-SE-001,EX-20260910-0001,CH-EX-20001,,,EXC-LIC-1001,Royal Beverages Pvt Ltd,2026-09-10,2026-09-10,NETBANKING,250000.00,0039-00-105-01-00-01,Excise licence fee,5000.00,PAID
PARIVAHAN,TRANSPORT,TRANSPORT,PAO11,DDO-TR-001,PV-20260910-0001,CH-TR-30001,,,DL-9876543210,Ramesh Kumar,2026-09-10,2026-09-10,CARD,4500.00,0041-00-101-01-00-01,Vehicle registration fee,0.00,PAID
SHCIL,STAMP,STAMPREG,PAO12,DDO-SR-001,SH-20260910-0001,CH-ST-40001,,,PAN-AABCA1111A,Anita Sharma,2026-09-10,2026-09-10,NETBANKING,60000.00,0030-00-102-01-00-01,E-stamp purchase,0.00,PAID
DVAT,DVAT,DVAT,PAO06,DDO-DV-001,DV-20260910-0001,CH-DV-50001,,CIN-DV-50001,TIN-07123456789,Classic Enterprises,2026-09-10,2026-09-10,CHEQUE,94000.00,0040-00-101-01-00-01,DVAT monthly payment,0.00,PAID
NONTAX-PORTAL,NONTAX,GAD,PAO15,DDO-NT-001,NT-20260910-0001,CH-NT-60001,,,CIT-0001,Sunita Patil,2026-09-10,2026-09-10,CASH,1200.00,0070-60-800-01-00-01,Certificate service fee,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-20260911-0003,CH-GST-10003,CPIN-10003,CIN-10003,GSTIN27LMNOP4567Q1Z8,Delta Manufacturing,2026-09-11,2026-09-11,NETBANKING,150000.00,0040-00-102-01-00-01,GST tax payment,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-20260911-0004,CH-GST-10004,CPIN-10004,CIN-10004,GSTIN27UVWXY9876R1Z1,Zenith Industries,2026-09-11,2026-09-11,NETBANKING,82000.00,0040-00-102-01-00-01,GST tax payment,0.00,PAID
ESCIMS,EXCISE,EXCISE,PAO10,DDO-SE-001,EX-20260911-0002,CH-EX-20002,,,EXC-LIC-1002,Sunrise Hotels Ltd,2026-09-11,2026-09-11,CASH,35000.00,0039-00-105-01-00-01,Excise permit fee,0.00,PAID
PARIVAHAN,TRANSPORT,TRANSPORT,PAO11,DDO-TR-001,PV-20260911-0002,CH-TR-30002,,,MH31AB1234,Vikram Motors,2026-09-11,2026-09-11,UPI,8500.00,0041-00-101-01-00-01,Fitness certificate fee,0.00,PAID
SHCIL,STAMP,STAMPREG,PAO12,DDO-SR-001,SH-20260911-0002,CH-ST-40002,,,PAN-BBCPS2222B,Sanjay Verma,2026-09-11,2026-09-11,NETBANKING,110000.00,0030-00-102-01-00-01,Registration stamp duty,0.00,PAID
NONTAX-PORTAL,NONTAX,PWD,PAO15,DDO-NT-002,NT-20260911-0002,CH-NT-60002,,,CIT-0002,Meera Joshi,2026-09-11,2026-09-11,NETBANKING,25000.00,0070-60-800-01-00-01,Building plan scrutiny fee,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-20260912-0005,CH-GST-10005,CPIN-10005,CIN-10005,GSTIN27AAAAA0000A1Z5,Portal Only Enterprises,2026-09-12,2026-09-12,NETBANKING,47000.00,0040-00-102-01-00-01,GST payment awaiting remittance,0.00,PAID
PARIVAHAN,TRANSPORT,TRANSPORT,PAO11,DDO-TR-001,PV-20260912-0003,CH-TR-30003,,,MH49XY7890,Partial Settlement Transport,2026-09-12,2026-09-12,NETBANKING,20000.00,0041-00-101-01-00-01,Permit fee partial settlement example,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-20260912-0006,CH-GST-10006,CPIN-10006,CIN-10006,GSTIN27DUPLI1111D1Z1,Duplicate Demo Pvt Ltd,2026-09-12,2026-09-12,UPI,15000.00,0040-00-102-01-00-01,Duplicate test transaction,0.00,PAID""",

    "bank": """scroll_no,scroll_date,bank_code,branch_code,revenue_source,department_code,pao_code,challan_no,cpin,cin,bank_reference_no,utr_no,payer_id,payer_name,payment_mode,payment_received_date,instrument_realization_date,bank_remittance_date,amount,receipt_head,bank_status
SBI-20260910-001,2026-09-10,SBI,SBI-NAG-001,GST,TT,PAO21,CH-GST-10001,CPIN-10001,CIN-10001,BRN-10001,UTR-10001,GSTIN27ABCDE1234F1Z5,ABC Traders,NETBANKING,2026-09-10,,2026-09-10,125000.00,0040-00-102-01-00-01,REMITTED
SBI-20260910-001,2026-09-10,SBI,SBI-NAG-001,GST,TT,PAO21,CH-GST-10002,CPIN-10002,CIN-10002,BRN-10002,UTR-10002,GSTIN27PQRSX6789K1Z2,Metro Supplies,UPI,2026-09-10,,2026-09-10,78500.00,0040-00-102-01-00-01,REMITTED
HDFC-20260910-001,2026-09-10,HDFC,HDFC-DEL-002,EXCISE,EXCISE,PAO10,CH-EX-20001,,,BRN-20001,UTR-20001,EXC-LIC-1001,Royal Beverages Pvt Ltd,NETBANKING,2026-09-10,,2026-09-11,250000.00,0039-00-105-01-00-01,REMITTED
ICICI-20260910-001,2026-09-10,ICICI,ICICI-DEL-003,TRANSPORT,TRANSPORT,PAO11,CH-TR-30001,,,BRN-30001,UTR-30001,DL-9876543210,Ramesh Kumar,CARD,2026-09-10,,2026-09-10,4500.00,0041-00-101-01-00-01,REMITTED
SBI-20260910-002,2026-09-10,SBI,SBI-DEL-010,STAMP,STAMPREG,PAO12,CH-ST-40001,,,BRN-40001,UTR-40001,PAN-AABCA1111A,Anita Sharma,NETBANKING,2026-09-10,,2026-09-10,60000.00,0030-00-102-01-00-01,REMITTED
PNB-20260910-001,2026-09-10,PNB,PNB-DEL-005,DVAT,DVAT,PAO06,CH-DV-50001,,CIN-DV-50001,BRN-50001,UTR-50001,TIN-07123456789,Classic Enterprises,CHEQUE,2026-09-10,2026-09-12,2026-09-13,94000.00,0040-00-101-01-00-01,REMITTED
SBI-20260910-003,2026-09-10,SBI,SBI-NAG-001,NONTAX,GAD,PAO15,CH-NT-60001,,,BRN-60001,UTR-60001,CIT-0001,Sunita Patil,CASH,2026-09-10,,2026-09-12,1200.00,0070-60-800-01-00-01,REMITTED
SBI-20260911-001,2026-09-11,SBI,SBI-NAG-001,GST,TT,PAO21,CH-GST-10003,CPIN-10003,CIN-10003,BRN-10003-A,UTR-10003-A,GSTIN27LMNOP4567Q1Z8,Delta Manufacturing,NETBANKING,2026-09-11,,2026-09-11,100000.00,0040-00-102-01-00-01,REMITTED
SBI-20260911-002,2026-09-11,SBI,SBI-NAG-001,GST,TT,PAO21,CH-GST-10003,CPIN-10003,CIN-10003,BRN-10003-B,UTR-10003-B,GSTIN27LMNOP4567Q1Z8,Delta Manufacturing,NETBANKING,2026-09-11,,2026-09-12,50000.00,0040-00-102-01-00-01,REMITTED
HDFC-20260911-001,2026-09-11,HDFC,HDFC-DEL-002,GST,TT,PAO21,CH-GST-10004,CPIN-10004,CIN-10004,BRN-10004,UTR-10004,GSTIN27UVWXY9876R1Z1,Zenith Industries,NETBANKING,2026-09-11,,2026-09-11,80000.00,0040-00-102-01-00-01,REMITTED
HDFC-20260911-002,2026-09-11,HDFC,HDFC-DEL-002,EXCISE,EXCISE,PAO10,CH-EX-20002,,,BRN-20002,UTR-20002,EXC-LIC-1002,Sunrise Hotels Ltd,CASH,2026-09-11,,2026-09-14,35000.00,0039-00-105-01-00-01,REMITTED
ICICI-20260911-001,2026-09-11,ICICI,ICICI-DEL-003,TRANSPORT,TRANSPORT,PAO11,CH-TR-30002,,,BRN-30002,UTR-30002,MH31AB1234,Vikram Motors,UPI,2026-09-11,,2026-09-11,8500.00,0041-00-101-01-00-01,REMITTED
SBI-20260911-003,2026-09-11,SBI,SBI-DEL-010,STAMP,STAMPREG,PAO12,CH-ST-40002,,,BRN-40002,UTR-40002,PAN-BBCPS2222B,Sanjay Verma,NETBANKING,2026-09-11,,2026-09-11,110000.00,0030-00-102-01-00-01,REMITTED
ICICI-20260911-002,2026-09-11,ICICI,ICICI-NAG-004,NONTAX,PWD,PAO15,CH-NT-60002,,,BRN-60002,UTR-60002,CIT-0002,Meera Joshi,NETBANKING,2026-09-11,,2026-09-11,25000.00,0070-60-800-01-00-01,REMITTED
SBI-20260912-001,2026-09-12,SBI,SBI-NAG-001,TRANSPORT,TRANSPORT,PAO11,CH-TR-30003,,,BRN-30003-A,UTR-30003-A,MH49XY7890,Partial Settlement Transport,NETBANKING,2026-09-12,,2026-09-12,12000.00,0041-00-101-01-00-01,REMITTED
SBI-20260912-002,2026-09-12,SBI,SBI-NAG-001,TRANSPORT,TRANSPORT,PAO11,CH-TR-30003,,,BRN-30003-B,UTR-30003-B,MH49XY7890,Partial Settlement Transport,NETBANKING,2026-09-12,,2026-09-13,8000.00,0041-00-101-01-00-01,REMITTED
SBI-20260912-003,2026-09-12,SBI,SBI-NAG-001,GST,TT,PAO21,CH-GST-10006,CPIN-10006,CIN-10006,BRN-10006,UTR-10006,GSTIN27DUPLI1111D1Z1,Duplicate Demo Pvt Ltd,UPI,2026-09-12,,2026-09-12,15000.00,0040-00-102-01-00-01,REMITTED
SBI-20260912-004,2026-09-12,SBI,SBI-NAG-001,GST,TT,PAO21,CH-GST-10006,CPIN-10006,CIN-10006,BRN-10006-DUP,UTR-10006-DUP,GSTIN27DUPLI1111D1Z1,Duplicate Demo Pvt Ltd,UPI,2026-09-12,,2026-09-12,15000.00,0040-00-102-01-00-01,REMITTED
HDFC-20260912-001,2026-09-12,HDFC,HDFC-DEL-002,GST,TT,PAO21,CH-GST-99999,CPIN-99999,CIN-99999,BRN-99999,UTR-99999,GSTIN27RAT0000R1Z1,RBI Only Candidate,NETBANKING,2026-09-12,,2026-09-12,32000.00,0040-00-102-01-00-01,REMITTED""",

    "rbi": """rbi_file_no,rbi_file_date,rbi_reference_no,bank_code,revenue_source,department_code,pao_code,challan_no,cin,bank_reference_no,utr_no,rbi_credit_date,amount,receipt_head,government_account,rbi_status
RBI-LUG-20260910,2026-09-10,RBIREF-10001,SBI,GST,TT,PAO21,CH-GST-10001,CIN-10001,BRN-10001,UTR-10001,2026-09-10,125000.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260910,2026-09-10,RBIREF-10002,SBI,GST,TT,PAO21,CH-GST-10002,CIN-10002,BRN-10002,UTR-10002,2026-09-10,78500.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260911,2026-09-11,RBIREF-20001,HDFC,EXCISE,EXCISE,PAO10,CH-EX-20001,,BRN-20001,UTR-20001,2026-09-11,250000.00,0039-00-105-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260910,2026-09-10,RBIREF-30001,ICICI,TRANSPORT,TRANSPORT,PAO11,CH-TR-30001,,BRN-30001,UTR-30001,2026-09-10,4500.00,0041-00-101-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260910,2026-09-10,RBIREF-40001,SBI,STAMP,STAMPREG,PAO12,CH-ST-40001,,BRN-40001,UTR-40001,2026-09-10,60000.00,0030-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260913,2026-09-13,RBIREF-50001,PNB,DVAT,DVAT,PAO06,CH-DV-50001,CIN-DV-50001,BRN-50001,UTR-50001,2026-09-13,94000.00,0040-00-101-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260912,2026-09-12,RBIREF-60001,SBI,NONTAX,GAD,PAO15,CH-NT-60001,,BRN-60001,UTR-60001,2026-09-12,1200.00,0070-60-800-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260911,2026-09-11,RBIREF-10003A,SBI,GST,TT,PAO21,CH-GST-10003,CIN-10003,BRN-10003-A,UTR-10003-A,2026-09-11,100000.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260912,2026-09-12,RBIREF-10003B,SBI,GST,TT,PAO21,CH-GST-10003,CIN-10003,BRN-10003-B,UTR-10003-B,2026-09-12,50000.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260911,2026-09-11,RBIREF-10004,HDFC,GST,TT,PAO21,CH-GST-10004,CIN-10004,BRN-10004,UTR-10004,2026-09-11,80000.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260914,2026-09-14,RBIREF-20002,HDFC,EXCISE,EXCISE,PAO10,CH-EX-20002,,BRN-20002,UTR-20002,2026-09-14,35000.00,0039-00-105-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260911,2026-09-11,RBIREF-30002,ICICI,TRANSPORT,TRANSPORT,PAO11,CH-TR-30002,,BRN-30002,UTR-30002,2026-09-11,8500.00,0041-00-101-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260911,2026-09-11,RBIREF-40002,SBI,STAMP,STAMPREG,PAO12,CH-ST-40002,,BRN-40002,UTR-40002,2026-09-11,110000.00,0030-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260911,2026-09-11,RBIREF-60002,ICICI,NONTAX,PWD,PAO15,CH-NT-60002,,BRN-60002,UTR-60002,2026-09-11,25000.00,0070-60-800-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260912,2026-09-12,RBIREF-30003A,SBI,TRANSPORT,TRANSPORT,PAO11,CH-TR-30003,,BRN-30003-A,UTR-30003-A,2026-09-12,12000.00,0041-00-101-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260913,2026-09-13,RBIREF-30003B,SBI,TRANSPORT,TRANSPORT,PAO11,CH-TR-30003,,BRN-30003-B,UTR-30003-B,2026-09-13,8000.00,0041-00-101-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260912,2026-09-12,RBIREF-10006,SBI,GST,TT,PAO21,CH-GST-10006,CIN-10006,BRN-10006,UTR-10006,2026-09-12,15000.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED
RBI-LUG-20260912,2026-09-12,RBIREF-99999,HDFC,GST,TT,PAO21,CH-GST-99999,CIN-99999,BRN-99999,UTR-99999,2026-09-12,32000.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED""",

    "invalid": """portal_name,revenue_source,department_code,pao_code,ddo_code,portal_transaction_id,challan_no,cpin,cin,payer_id,payer_name,payment_date,service_date,payment_mode,amount,receipt_head,service_description,penalty_amount,portal_status
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-001,CH-GST-BAD-001,CPIN-BAD-001,CIN-BAD-001,GSTIN27BAD0001B1Z1,Invalid Amount Pvt Ltd,2026-09-12,2026-09-12,NETBANKING,ABC,0040-00-102-01-00-01,Invalid amount test,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,,CH-GST-BAD-002,CPIN-BAD-002,CIN-BAD-002,GSTIN27BAD0002B1Z1,Missing Portal Transaction,2026-09-12,2026-09-12,UPI,1000.00,0040-00-102-01-00-01,Missing ID test,0.00,PAID
UNKNOWN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-003,CH-GST-BAD-003,CPIN-BAD-003,CIN-BAD-003,GSTIN27BAD0003B1Z1,Unknown Portal,2026-09-12,2026-09-12,NETBANKING,2000.00,0040-00-102-01-00-01,Invalid portal test,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-004,CH-GST-BAD-004,CPIN-BAD-004,CIN-BAD-004,GSTIN27BAD0004B1Z1,Invalid Date,2026-99-99,2026-09-12,NETBANKING,3000.00,0040-00-102-01-00-01,Invalid date test,0.00,PAID"""
}

class UploadService:
    @staticmethod
    def _parse_date(d_str: Optional[str]) -> Optional[date]:
        if not d_str:
            return None
        try:
            return datetime.strptime(d_str.strip(), "%Y-%m-%d").date()
        except Exception:
            return None

    @classmethod
    async def get_batches(
        cls,
        db: AsyncSession,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        query = select(RevUploadBatch)
        if source_type:
            query = query.where(RevUploadBatch.batch_type == source_type)
        if status:
            query = query.where(RevUploadBatch.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(RevUploadBatch.batch_id)).limit(limit).offset(offset)
        result = await db.execute(query)
        batches = result.scalars().all()

        return {
            "total": total_count,
            "items": batches
        }

    @classmethod
    async def get_batch_items(
        cls,
        db: AsyncSession,
        batch_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        batch = await db.get(RevUploadBatch, batch_id)
        if not batch:
            raise NotFoundException(f"Batch with ID {batch_id} not found")

        items = []
        if batch.batch_type == "PORTAL":
            q = select(RevPortalTransactionStaging).where(RevPortalTransactionStaging.batch_id == batch_id).limit(limit).offset(offset)
            items = (await db.execute(q)).scalars().all()
        elif batch.batch_type == "BANK_SCROLL":
            q = select(RevAgencyBankScrollStaging).where(RevAgencyBankScrollStaging.batch_id == batch_id).limit(limit).offset(offset)
            items = (await db.execute(q)).scalars().all()
        elif batch.batch_type == "RBI_LUGGAGE":
            q = select(RevRbiLuggageStaging).where(RevRbiLuggageStaging.batch_id == batch_id).limit(limit).offset(offset)
            items = (await db.execute(q)).scalars().all()

        # Rejected rows
        rej_q = select(RevUploadRejectedRow).where(RevUploadRejectedRow.batch_id == batch_id)
        rejections = (await db.execute(rej_q)).scalars().all()

        return {
            "batch": batch,
            "items": items,
            "rejections": rejections
        }

    @classmethod
    async def process_csv_upload(
        cls,
        db: AsyncSession,
        source_type: str,
        file_name: str,
        csv_text: str,
        user_id: int,
        auto_approve: bool = False,
    ) -> RevUploadBatch:
        st_upper = source_type.upper()
        if st_upper not in ["PORTAL", "BANK_SCROLL", "RBI_LUGGAGE"]:
            raise BusinessValidationException(f"Unsupported source type '{source_type}'.")

        date_token = date.today().strftime("%Y%m%d")
        seq_res = await db.execute(
            text("SELECT ifms_budget.fn_rev_next_seq(:seq_key, :prefix, :fy)"),
            {"seq_key": "BATCH_SEQ", "prefix": f"UPB-{st_upper[:3]}", "fy": date_token}
        )
        batch_no = seq_res.scalar() or f"UPB-{st_upper[:3]}-{date_token}-{datetime.now().strftime('%H%M%S')}"

        batch = RevUploadBatch(
            batch_no=batch_no,
            batch_type=st_upper,
            source_filename=file_name,
            file_size_bytes=len(csv_text.encode("utf-8")),
            data_date=date.today(),
            status="PENDING_APPROVAL",
            uploaded_by=user_id,
            uploaded_at=datetime.now(),
        )
        db.add(batch)
        await db.flush()

        text_stream = io.StringIO(csv_text.strip())
        reader = csv.DictReader(text_stream)

        def get_f(r_dict: dict, *keys: str, default: str = "") -> str:
            for k in keys:
                if k in r_dict and r_dict[k] is not None and str(r_dict[k]).strip() != "":
                    return str(r_dict[k]).strip()
            return default

        total_rows = 0
        valid_rows = 0
        rejected_rows = 0
        duplicate_rows = 0
        control_total = Decimal("0.00")

        for row_idx, raw_row in enumerate(reader, start=1):
            total_rows += 1
            raw_line = ",".join([str(v) for v in raw_row.values() if v is not None])
            # Normalize dictionary keys to lowercase and stripped
            row = {str(k).strip().lower(): v for k, v in raw_row.items() if k is not None}

            # Extract amount with fallback across multiple possible column aliases
            amt_raw = get_f(row, "amount", "portal_amount", "bank_amount", "rbi_amount", "total_amount", "portal", "bank", "rbi", "value", default="0")
            amt_clean = amt_raw.replace(",", "").replace("₹", "").strip()

            try:
                amt = Decimal(amt_clean)
                if amt <= 0:
                    raise ValueError(f"Amount must be positive, got '{amt_raw}'")
            except Exception as e:
                rejected_rows += 1
                rej = RevUploadRejectedRow(
                    batch_id=batch.batch_id,
                    batch_type=st_upper,
                    source_filename=file_name,
                    file_row_number=row_idx,
                    raw_csv_row=raw_line,
                    failure_reasons=[f"Invalid amount: {str(e)}"]
                )
                db.add(rej)
                continue

            try:
                if st_upper == "PORTAL":
                    txn_id = get_f(row, "portal_transaction_id", "portal_txn_id", "transaction_id", "txn_id", "reconciliation_id", "recon_id", default=f"TXN-{row_idx}")
                    challan = get_f(row, "challan_no", "challan", "challan_number", default=f"CH-GST-{row_idx}")

                    item = RevPortalTransactionStaging(
                        batch_id=batch.batch_id,
                        portal_name=get_f(row, "portal_name", "portal", default="GSTN"),
                        revenue_source=get_f(row, "revenue_source", "source", default="GST"),
                        dept_code=get_f(row, "department_code", "dept_code", "dept", default="TT"),
                        pao_code=get_f(row, "pao_code", "pao", default="PAO21"),
                        ddo_code=get_f(row, "ddo_code", "ddo", default="DDO-TT-001"),
                        portal_transaction_id=txn_id,
                        challan_no=challan,
                        cpin=get_f(row, "cpin") or None,
                        cin=get_f(row, "cin") or None,
                        payer_id=get_f(row, "payer_id", "payer_gstin", "gstin") or None,
                        payer_name=get_f(row, "payer_name", "payer", default="Taxpayer Entity"),
                        payment_date=cls._parse_date(get_f(row, "payment_date", "date")) or date.today(),
                        service_date=cls._parse_date(get_f(row, "service_date")) or date.today(),
                        payment_mode=get_f(row, "payment_mode", "mode", default="NETBANKING").upper(),
                        amount=amt,
                        receipt_head=get_f(row, "receipt_head", "head", default="0040-00-102-01-00-01"),
                        service_description=get_f(row, "service_description", "description") or None,
                        penalty_amount=Decimal(str(get_f(row, "penalty_amount", "penalty", default="0.00")).replace(",", "")),
                        portal_status=get_f(row, "portal_status", "status", default="PAID"),
                        is_valid=True
                    )
                    db.add(item)

                elif st_upper == "BANK_SCROLL":
                    scroll_no = get_f(row, "scroll_no", "scroll", default="SCROLL-01")
                    bank_code = get_f(row, "bank_code", "bank", default="SBI").upper()
                    bank_ref = get_f(row, "bank_reference_no", "bank_ref_no", "reference_no", "brn", default=f"BRN-{row_idx}")
                    challan = get_f(row, "challan_no", "challan", "challan_number", default=f"CH-GST-{row_idx}")

                    item = RevAgencyBankScrollStaging(
                        batch_id=batch.batch_id,
                        scroll_no=scroll_no,
                        scroll_date=cls._parse_date(get_f(row, "scroll_date", "date")) or date.today(),
                        bank_code=bank_code,
                        branch_code=get_f(row, "branch_code", "branch", default="SBI-NAG-001"),
                        revenue_source=get_f(row, "revenue_source", "source", default="GST"),
                        dept_code=get_f(row, "department_code", "dept_code", "dept", default="TT"),
                        pao_code=get_f(row, "pao_code", "pao", default="PAO21"),
                        challan_no=challan,
                        cpin=get_f(row, "cpin") or None,
                        cin=get_f(row, "cin") or None,
                        bank_reference_no=bank_ref,
                        utr_no=get_f(row, "utr_no", "utr") or None,
                        payer_id=get_f(row, "payer_id") or None,
                        payer_name=get_f(row, "payer_name", "payer", default="Taxpayer Entity"),
                        payment_mode=get_f(row, "payment_mode", "mode", default="NETBANKING").upper(),
                        payment_received_date=cls._parse_date(get_f(row, "payment_received_date", "payment_date", "recv_date")) or date.today(),
                        instrument_realization_date=cls._parse_date(get_f(row, "instrument_realization_date")),
                        bank_remittance_date=cls._parse_date(get_f(row, "bank_remittance_date", "remittance_date", "remit_date")) or date.today(),
                        amount=amt,
                        receipt_head=get_f(row, "receipt_head", "head", default="0040-00-102-01-00-01"),
                        bank_status=get_f(row, "bank_status", "status", default="REMITTED"),
                        is_valid=True
                    )
                    db.add(item)

                elif st_upper == "RBI_LUGGAGE":
                    rbi_ref = get_f(row, "rbi_reference_no", "rbi_ref_no", "rbi_ref", "reference_no", default=f"RBIREF-{row_idx}")
                    challan = get_f(row, "challan_no", "challan", "challan_number") or None
                    bank_code = get_f(row, "bank_code", "bank", default="SBI").upper()

                    item = RevRbiLuggageStaging(
                        batch_id=batch.batch_id,
                        file_reference_no=get_f(row, "rbi_file_no", "file_no", default="RBI-01"),
                        luggage_date=cls._parse_date(get_f(row, "rbi_file_date", "luggage_date", "file_date")) or date.today(),
                        rbi_reference_no=rbi_ref,
                        bank_code=bank_code,
                        govt_account_no=get_f(row, "government_account", "govt_account", "account_no", default="GOVT-RBI-RECEIPTS"),
                        rbi_credit_date=cls._parse_date(get_f(row, "rbi_credit_date", "credit_date", "date")) or date.today(),
                        amount=amt,
                        receipt_head=get_f(row, "receipt_head", "head", default="0040-00-102-01-00-01"),
                        challan_no=challan,
                        cpin=get_f(row, "cpin") or None,
                        cin=get_f(row, "cin") or None,
                        utr_no=get_f(row, "utr_no", "utr") or None,
                        rbi_status=get_f(row, "rbi_status", "status", default="CONFIRMED"),
                        is_valid=True
                    )
                    db.add(item)

                valid_rows += 1
                control_total += amt

            except Exception as e:
                rejected_rows += 1
                rej = RevUploadRejectedRow(
                    batch_id=batch.batch_id,
                    batch_type=st_upper,
                    source_filename=file_name,
                    file_row_number=row_idx,
                    raw_csv_row=raw_line,
                    failure_reasons=[str(e)]
                )
                db.add(rej)

        batch.total_records = total_rows
        batch.valid_records = valid_rows
        batch.invalid_records = rejected_rows
        batch.duplicate_records = duplicate_rows
        batch.control_total = control_total

        await db.commit()
        await db.refresh(batch)

        if auto_approve and valid_rows > 0:
            await cls.approve_batch(db, batch.batch_id, checker_id=user_id, remarks="Auto-approved sample batch")
            await db.refresh(batch)

        return batch

    @classmethod
    async def load_sample_dataset(
        cls,
        db: AsyncSession,
        sample_key: str,
        auto_approve: bool = True,
        user_id: int = 1,
    ) -> RevUploadBatch:
        key = sample_key.lower()
        csv_text = SAMPLE_CSVS.get(key)
        if not csv_text:
            raise NotFoundException(f"Sample dataset with key '{sample_key}' not found.")

        type_map = {
            "portal": "PORTAL",
            "bank": "BANK_SCROLL",
            "rbi": "RBI_LUGGAGE",
            "invalid": "PORTAL",
        }
        source_type = type_map.get(key, "PORTAL")
        filename = f"sample_{key}.csv"

        return await cls.process_csv_upload(
            db=db,
            source_type=source_type,
            file_name=filename,
            csv_text=csv_text,
            user_id=user_id,
            auto_approve=auto_approve
        )

    @classmethod
    async def approve_batch(
        cls,
        db: AsyncSession,
        batch_id: int,
        checker_id: int,
        remarks: str = "Verified and approved by PAO Checker.",
    ) -> RevUploadBatch:
        batch = await db.get(RevUploadBatch, batch_id)
        if not batch:
            raise NotFoundException(f"Batch with ID {batch_id} not found")

        # Invoke procedure sp_rev_approve_upload_batch
        await db.execute(
            text("CALL ifms_budget.sp_rev_approve_upload_batch(:batch_id, :checker_id, :remarks)"),
            {"batch_id": batch_id, "checker_id": checker_id, "remarks": remarks}
        )
        await db.commit()
        await db.refresh(batch)
        return batch

    @classmethod
    async def delete_batch(
        cls,
        db: AsyncSession,
        batch_id: int,
        user_id: int = 1,
    ) -> Dict[str, Any]:
        batch = await db.get(RevUploadBatch, batch_id)
        if not batch:
            raise NotFoundException(f"Batch with ID {batch_id} not found")

        # Delete staged rows in corresponding table
        if batch.batch_type == "PORTAL":
            await db.execute(delete(RevPortalTransactionStaging).where(RevPortalTransactionStaging.batch_id == batch_id))
        elif batch.batch_type == "BANK_SCROLL":
            await db.execute(delete(RevAgencyBankScrollStaging).where(RevAgencyBankScrollStaging.batch_id == batch_id))
        elif batch.batch_type == "RBI_LUGGAGE":
            await db.execute(delete(RevRbiLuggageStaging).where(RevRbiLuggageStaging.batch_id == batch_id))

        await db.execute(delete(RevUploadRejectedRow).where(RevUploadRejectedRow.batch_id == batch_id))
        await db.delete(batch)
        await db.commit()

        return {"status": "SUCCESS", "message": f"Batch {batch.batch_no} and its staging records deleted successfully."}

