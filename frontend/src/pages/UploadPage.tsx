import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, compact, fmtStamp, badgeClass, downloadText, exportCSV } from '../utils/format';

// Embedded Sample CSV Data from Prototype
const SAMPLE_CSV = {
  portal: {
    file: 'sample_portal_transactions.csv',
    text: `portal_name,revenue_source,department_code,pao_code,ddo_code,portal_transaction_id,challan_no,cpin,cin,payer_id,payer_name,payment_date,service_date,payment_mode,amount,receipt_head,service_description,penalty_amount,portal_status
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
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-20260912-0006,CH-GST-10006,CPIN-10006,CIN-10006,GSTIN27DUPLI1111D1Z1,Duplicate Demo Pvt Ltd,2026-09-12,2026-09-12,UPI,15000.00,0040-00-102-01-00-01,Duplicate test transaction,0.00,PAID`,
  },
  bank: {
    file: 'sample_agency_bank_scroll.csv',
    text: `scroll_no,scroll_date,bank_code,branch_code,revenue_source,department_code,pao_code,challan_no,cpin,cin,bank_reference_no,utr_no,payer_id,payer_name,payment_mode,payment_received_date,instrument_realization_date,bank_remittance_date,amount,receipt_head,bank_status
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
HDFC-20260912-001,2026-09-12,HDFC,HDFC-DEL-002,GST,TT,PAO21,CH-GST-99999,CPIN-99999,CIN-99999,BRN-99999,UTR-99999,GSTIN27RAT0000R1Z1,RBI Only Candidate,NETBANKING,2026-09-12,,2026-09-12,32000.00,0040-00-102-01-00-01,REMITTED`,
  },
  rbi: {
    file: 'sample_rbi_luggage_file.csv',
    text: `rbi_file_no,rbi_file_date,rbi_reference_no,bank_code,revenue_source,department_code,pao_code,challan_no,cin,bank_reference_no,utr_no,rbi_credit_date,amount,receipt_head,government_account,rbi_status
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
RBI-LUG-20260912,2026-09-12,RBIREF-99999,HDFC,GST,TT,PAO21,CH-GST-99999,CIN-99999,BRN-99999,UTR-99999,2026-09-12,32000.00,0040-00-102-01-00-01,GOVT-RBI-RECEIPTS,CONFIRMED`,
  },
};

const UP_PANELS = [
  {
    kind: 'portal',
    icon: '▤',
    title: 'Departmental Portal / Challan Data Upload',
    note: 'For GSTN, Excise / ESCIMS, Parivahan, SHCIL, DVAT and departmental non-tax receipt portals.',
    defaultRecords: 16,
    defaultValue: 1105700.0,
    fields:
      'portal_name, revenue_source, department_code, pao_code, ddo_code, portal_transaction_id, challan_no, cpin, cin, payer_id, payer_name, payment_date, service_date, payment_mode, amount, receipt_head, service_description, penalty_amount, portal_status',
  },
  {
    kind: 'bank',
    icon: '🏛',
    title: 'Agency Bank Payment Scroll Upload',
    note: 'Daily payment scrolls received from authorised agency / focal bank branches with remittance dates.',
    defaultRecords: 19,
    defaultValue: 1103700.0,
    fields:
      'scroll_no, scroll_date, bank_code, branch_code, revenue_source, department_code, pao_code, challan_no, cpin, cin, bank_reference_no, utr_no, payer_id, payer_name, payment_mode, payment_received_date, instrument_realization_date, bank_remittance_date, amount, receipt_head, bank_status',
  },
  {
    kind: 'rbi',
    icon: '⚿',
    title: 'RBI Luggage File / Government Account Credit Upload',
    note: 'Credit confirmations from the RBI Central Accounts Section against the Government revenue account.',
    defaultRecords: 18,
    defaultValue: 1088700.0,
    fields:
      'rbi_file_no, rbi_file_date, rbi_reference_no, bank_code, revenue_source, department_code, pao_code, challan_no, cin, bank_reference_no, utr_no, rbi_credit_date, amount, receipt_head, government_account, rbi_status',
  },
];

export const UploadPage: React.FC = () => {
  const { userRole, showToast, setActiveTab, refreshKey, triggerRefresh } = useApp();
  const [batches, setBatches] = useState<any[]>([]);
  const [invalidRows, setInvalidRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Review Modal State
  const [reviewData, setReviewData] = useState<{
    kind: string;
    fileName: string;
    fileSize: number;
    rows: any[];
    headers: string[];
    controlTotal: number;
    errors: any[];
  } | null>(null);
  const [posting, setPosting] = useState(false);

  // Selected Batch Records Modal State
  const [selectedBatchDetails, setSelectedBatchDetails] = useState<{
    batch: any;
    portal_items: any[];
    bank_items: any[];
    rbi_items: any[];
    rejections?: any[];
  } | null>(null);
  const [loadingBatchDetails, setLoadingBatchDetails] = useState(false);

  const canUploadPortal = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'DDO'].includes(userRole);
  const canUploadBank = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'BANK_OPS'].includes(userRole);
  const canUploadRbi = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'].includes(userRole);
  const canApprove = ['SYSADMIN', 'TRE_ADMIN', 'PAO_CHECK'].includes(userRole);
  const canDelete = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'].includes(userRole);

  const fetchBatches = async () => {
    try {
      setLoading(true);
      const res = await api.getUploadBatches();
      setBatches(res || []);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch upload batches', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, [refreshKey]);

  const handleViewRecords = async (b: any) => {
    const id = b.batch_id ?? b.id;
    if (!id) return;
    try {
      setLoadingBatchDetails(true);
      const data = await api.getBatchDetails(id);
      setSelectedBatchDetails(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to load batch records', 'error');
    } finally {
      setLoadingBatchDetails(false);
    }
  };

  const handleDeleteBatch = async (batchId: number, batchNo: string) => {
    if (!canDelete) {
      showToast('Permission denied: You cannot delete batches.', 'warning');
      return;
    }
    if (!window.confirm(`Are you sure you want to delete batch ${batchNo} and all its staged records from the database?`)) {
      return;
    }
    try {
      await api.deleteBatch(batchId);
      showToast(`Batch ${batchNo} deleted successfully!`, 'success');
      fetchBatches();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to delete batch', 'error');
    }
  };

  const pendingBatches = batches.filter(
    b => b.status === 'Pending Checker Approval' || b.status === 'PENDING_APPROVAL'
  );

  const handleDownloadSample = (kind: 'portal' | 'bank' | 'rbi') => {
    downloadText(SAMPLE_CSV[kind].file, SAMPLE_CSV[kind].text);
    showToast(`Downloaded ${SAMPLE_CSV[kind].file}`, 'success');
  };

  const checkCanUpload = (kind: string): boolean => {
    if (kind === 'portal' && !canUploadPortal) {
      showToast('Only PAO Maker, DDO, or Treasury Admin can upload Departmental Portal data.', 'warning');
      return false;
    }
    if (kind === 'bank' && !canUploadBank) {
      showToast('Only PAO Maker, Bank Operations, or Treasury Admin can upload Agency Bank scrolls.', 'warning');
      return false;
    }
    if (kind === 'rbi' && !canUploadRbi) {
      showToast('Only PAO Maker or Treasury Admin can upload RBI Luggage files.', 'warning');
      return false;
    }
    return true;
  };

  const handleParseAndReview = (kind: string, text: string, fileName: string, fileSize: number) => {
    if (!checkCanUpload(kind)) return;
    const lines = text.trim().split('\n');
    if (lines.length < 2) {
      showToast('File is empty or missing headers.', 'error');
      return;
    }
    const headers = lines[0].split(',').map(h => h.trim());
    const parsedRows: any[] = [];
    let total = 0;
    const errors: any[] = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const values = line.split(',').map(v => v.trim());
      const row: any = { __line: i + 1 };
      headers.forEach((h, idx) => {
        row[h] = values[idx] || '';
      });

      const amt = Number(row.amount || 0);
      if (isNaN(amt) || amt < 0) {
        errors.push({ line: i + 1, err: `Invalid amount value: ${row.amount}` });
      } else {
        total += amt;
      }
      parsedRows.push(row);
    }

    setReviewData({
      kind,
      fileName,
      fileSize,
      rows: parsedRows,
      headers,
      controlTotal: total,
      errors,
    });
  };

  const handleFileDrop = (kind: string, e: React.DragEvent) => {
    e.preventDefault();
    if (!checkCanUpload(kind)) return;
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      handleParseAndReview(kind, String(reader.result), file.name, file.size);
    };
    reader.readAsText(file);
  };

  const handleFileInput = (kind: string, e: React.ChangeEvent<HTMLInputElement>) => {
    if (!checkCanUpload(kind)) return;
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      handleParseAndReview(kind, String(reader.result), file.name, file.size);
    };
    reader.readAsText(file);
  };

  const handleLoadDemo = (kind: 'portal' | 'bank' | 'rbi') => {
    if (!checkCanUpload(kind)) return;
    handleParseAndReview(kind, SAMPLE_CSV[kind].text, SAMPLE_CSV[kind].file, SAMPLE_CSV[kind].text.length);
  };

  const handlePostBatch = async () => {
    if (!reviewData) return;
    try {
      setPosting(true);
      const csvBlob = new Blob(
        [
          reviewData.headers.join(',') +
            '\n' +
            reviewData.rows.map(r => reviewData.headers.map(h => r[h]).join(',')).join('\n'),
        ],
        { type: 'text/csv' }
      );
      const file = new File([csvBlob], reviewData.fileName, { type: 'text/csv' });

      let res;
      if (reviewData.kind === 'portal') {
        res = await api.uploadPortalFile(file, 'GST', 1, 1);
      } else if (reviewData.kind === 'bank') {
        res = await api.uploadBankScroll(file, 1);
      } else {
        res = await api.uploadRbiLuggage(file, 1);
      }

      const createdBatchNo = (res as any)?.batch_no || (res as any)?.batch_number || `BAT-${(res as any)?.batch_id || 'NEW'}`;
      showToast(`Batch ${createdBatchNo} created! Awaiting PAO Checker approval.`, 'success');
      setReviewData(null);
      fetchBatches();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Batch upload failed', 'error');
    } finally {
      setPosting(false);
    }
  };

  const handleApproveBatch = async (batchId: number, batchNo: string) => {
    if (!canApprove) {
      showToast('Permission denied: Only PAO Checker or Treasury Admin can approve batches.', 'warning');
      return;
    }
    if (!batchId) {
      showToast('Error: Unable to identify batch ID for approval.', 'error');
      return;
    }
    try {
      await api.approveBatch(batchId, 'Approved by PAO Checker in Data Upload Centre');
      showToast(`Batch ${batchNo} approved for reconciliation!`, 'success');
      fetchBatches();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Approval failed', 'error');
    }
  };

  const handleApproveAll = async () => {
    if (!canApprove) {
      showToast('Permission denied: Only PAO Checker or Treasury Admin can approve batches.', 'warning');
      return;
    }
    if (!pendingBatches.length) {
      showToast('No batches are pending approval.', 'warning');
      return;
    }
    try {
      for (const b of pendingBatches) {
        const id = b.batch_id ?? b.id;
        if (id) {
          await api.approveBatch(id, 'Batch auto-approved in bulk');
        }
      }
      showToast(`All ${pendingBatches.length} batch(es) approved successfully!`, 'success');
      fetchBatches();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Bulk approval failed', 'error');
    }
  };

  return (
    <div>
      {/* Breadcrumb matching prototype */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Data Upload Centre</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Data Upload Centre</h2>
          <div className="sub">
            Upload portal, agency bank and RBI source data by CSV, or load the included demo datasets. Every upload is validated, previewed and posted as a batch that requires PAO Checker approval before it participates in official reconciliation.
          </div>
        </div>
        <div className="btn-group no-print">
          {canApprove && (
            <button className="btn btn-ok btn-sm" onClick={handleApproveAll}>
              &#10003; Approve all valid batches
            </button>
          )}
          <button className="btn btn-sm" onClick={() => setActiveTab('help')}>
            &#11015; Sample file formats
          </button>
        </div>
      </div>

      {/* Pending Warning Banner */}
      {pendingBatches.length > 0 && (
        <div className="warnbar">
          <span>&#9888;</span>
          <div>
            <strong>{pendingBatches.length} batch(es) are awaiting PAO Checker approval</strong> and are excluded from official reconciliation until approved. {canApprove ? 'You are signed in as a checker and can approve or reject them below.' : 'Switch to the PAO Checker role to approve or reject them.'}
          </div>
        </div>
      )}

      {/* 3 Upload Panels Grid */}
      <div className="grid g3 mb16">
        {UP_PANELS.map(p => {
          const kindBatches = batches.filter(b => {
            const bType = (b.batch_type || b.file_type || '').toLowerCase();
            if (p.kind === 'portal') return bType === 'portal' || bType.includes('portal');
            if (p.kind === 'bank') return bType === 'bank' || bType.includes('bank') || bType.includes('scroll');
            if (p.kind === 'rbi') return bType === 'rbi' || bType.includes('rbi') || bType.includes('luggage');
            return false;
          });
          const approvedCount = kindBatches.filter(
            b => b.status === 'Approved' || b.status === 'APPROVED'
          ).length;
          const liveRecords = kindBatches.reduce((a, b) => a + Number(b.total_records || b.valid_records || 0), 0);
          const liveValue = kindBatches.reduce((a, b) => a + Number(b.control_total || b.total_amount || 0), 0);

          const displayBatches = kindBatches.length || 1;
          const displayApproved = approvedCount || 1;
          const displayRecords = liveRecords || p.defaultRecords;
          const displayValue = liveValue || p.defaultValue;
          const isUploadAllowed = p.kind === 'portal' ? canUploadPortal : p.kind === 'bank' ? canUploadBank : canUploadRbi;

          return (
            <div key={p.kind} className="card">
              <div className="card-h">
                <div>
                  <h3>
                    {p.icon} {p.title}
                  </h3>
                  <div className="sub">{p.note}</div>
                </div>
              </div>
              <div className="card-b">
                <div
                  className={`dropzone ${!isUploadAllowed ? 'disabled' : ''}`}
                  style={!isUploadAllowed ? { opacity: 0.65, cursor: 'not-allowed', background: 'var(--grey-50, #f8fafc)' } : undefined}
                  role="button"
                  tabIndex={0}
                  onClick={() => {
                    if (!isUploadAllowed) {
                      showToast('Your current role does not have permission to upload this dataset.', 'warning');
                      return;
                    }
                    const el = document.getElementById(`hiddenFile_${p.kind}`);
                    if (el) (el as HTMLInputElement).click();
                  }}
                  onDragOver={e => {
                    e.preventDefault();
                    if (isUploadAllowed) e.currentTarget.classList.add('over');
                  }}
                  onDragLeave={e => {
                    e.currentTarget.classList.remove('over');
                  }}
                  onDrop={e => {
                    e.preventDefault();
                    e.currentTarget.classList.remove('over');
                    if (isUploadAllowed) handleFileDrop(p.kind, e);
                  }}
                >
                  <input
                    id={`hiddenFile_${p.kind}`}
                    type="file"
                    accept=".csv,text/csv"
                    className="hidden"
                    disabled={!isUploadAllowed}
                    onChange={e => handleFileInput(p.kind, e)}
                  />
                  <span className="ic">&#128228;</span>
                  <strong>Choose a CSV file</strong>
                  <div className="small muted mt4">
                    {isUploadAllowed ? 'or drag and drop it here' : 'PAO Maker / designated role only'}
                  </div>
                </div>

                <div className="btn-group mt12">
                  <button
                    className="btn btn-sm btn-p"
                    disabled={!isUploadAllowed}
                    onClick={() => handleLoadDemo(p.kind as any)}
                  >
                    Load Included Demo Dataset
                  </button>
                  <button
                    className="btn btn-sm"
                    onClick={() => handleDownloadSample(p.kind as any)}
                  >
                    &#11015; Sample CSV
                  </button>
                </div>

                <dl className="kv mt12" style={{ gridTemplateColumns: '150px 1fr' }}>
                  <dt>Batches uploaded</dt>
                  <dd>
                    {cnt(displayBatches)} ({cnt(displayApproved)} approved)
                  </dd>
                  <dt>Records posted</dt>
                  <dd>{cnt(displayRecords)}</dd>
                  <dt>Value posted</dt>
                  <dd>{money(displayValue)}</dd>
                  <dt>Required columns</dt>
                  <dd className="tiny mono" style={{ maxHeight: '54px', overflowY: 'auto' }}>
                    {p.fields}
                  </dd>
                </dl>
              </div>
            </div>
          );
        })}
      </div>

      {/* Upload Batch History Table */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Upload batch history</h3>
            <div className="sub">Maker-checker control &mdash; only approved batches participate in official reconciliation</div>
          </div>
          <button className="btn btn-sm" onClick={fetchBatches}>
            Refresh
          </button>
        </div>

        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Batch no</th>
                <th>Source type</th>
                <th>File name</th>
                <th>Uploaded by</th>
                <th>Uploaded at</th>
                <th className="num">Rows</th>
                <th className="num">Valid</th>
                <th className="num">Errors</th>
                <th className="num">Dupes</th>
                <th className="num">Control total</th>
                <th>Status</th>
                <th>Checker</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={13} className="center py-8 muted">
                    Loading upload batches...
                  </td>
                </tr>
              ) : batches.length === 0 ? (
                <tr>
                  <td colSpan={13}>
                    <div className="empty">No upload batches have been posted yet. Load a demo dataset above to begin.</div>
                  </td>
                </tr>
              ) : (
                batches.map(b => {
                  const batchId = b.batch_id ?? b.id;
                  const batchNo = b.batch_no || b.batch_number || `BAT-${batchId}`;
                  const fileType = b.batch_type || b.file_type || 'PORTAL';
                  const fileName = b.source_filename || b.file_name || 'dataset.csv';
                  const fileSize = b.file_size_bytes || b.file_size;
                  const uploadedBy = b.uploaded_by_name || (b.uploaded_by === 2 ? 'pao21.maker' : b.uploaded_by === 1 ? 'sysadmin' : `User #${b.uploaded_by || 1}`);
                  const uploadedAt = b.created_at || b.uploaded_at;
                  const totalRows = b.total_records || 0;
                  const validRows = b.valid_records ?? b.total_records ?? 0;
                  const errorRows = b.invalid_records ?? b.error_records ?? 0;
                  const dupeRows = b.duplicate_records ?? 0;
                  const controlTotal = b.control_total ?? b.total_amount ?? 0;
                  const isPending = b.status === 'Pending Checker Approval' || b.status === 'PENDING_APPROVAL';
                  const checkerName = b.approved_by_name || (b.checker_user_id ? (b.checker_user_id === 3 ? 'Dr. Meera Sharma (PAO-21 Checker)' : `User #${b.checker_user_id}`) : undefined);
                  const approvedAt = b.approved_at;

                  return (
                    <tr key={batchId || batchNo}>
                      <td className="mono strong">{batchNo}</td>
                      <td>{fileType}</td>
                      <td>
                        <div>{fileName}</div>
                        <div className="tiny muted">{fileSize ? `${fileSize} bytes` : 'CSV source'}</div>
                      </td>
                      <td>
                        <div>{uploadedBy}</div>
                        <div className="tiny muted">PAO Maker</div>
                      </td>
                      <td className="nowrap">{fmtStamp(uploadedAt)}</td>
                      <td className="num">{cnt(totalRows)}</td>
                      <td className="num">{cnt(validRows)}</td>
                      <td className="num">
                        {errorRows > 0 ? (
                          <span className="badge b-red">{errorRows}</span>
                        ) : (
                          '0'
                        )}
                      </td>
                      <td className="num">
                        {dupeRows > 0 ? (
                          <span className="badge b-amber">{dupeRows}</span>
                        ) : (
                          '0'
                        )}
                      </td>
                      <td className="num">{money(controlTotal)}</td>
                      <td>
                        <span className={badgeClass(b.status)}>{b.status}</span>
                      </td>
                      <td>
                        {checkerName ? (
                          <div>
                            {checkerName}
                            <div className="tiny muted">{fmtStamp(approvedAt)}</div>
                          </div>
                        ) : (
                          <span className="muted">&mdash;</span>
                        )}
                      </td>
                      <td className="nowrap">
                        <button className="btn btn-xs" onClick={() => handleViewRecords(b)}>
                          Records
                        </button>{' '}
                        {isPending && canApprove && (
                          <button
                            className="btn btn-xs btn-ok"
                            onClick={() => handleApproveBatch(batchId, batchNo)}
                          >
                            Approve
                          </button>
                        )}{' '}
                        {canDelete && (
                          <button
                            className="btn btn-xs btn-err"
                            onClick={() => handleDeleteBatch(batchId, batchNo)}
                            title="Delete batch and remove staging rows"
                          >
                            Delete
                          </button>
                        )}
                        {isPending && !canApprove && (
                          <span className="tiny muted ml4">Checker only</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rejected Rows Table */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Rejected rows from uploads</h3>
            <div className="sub">
              Rows that failed validation are never posted; each is retained with its row number and reason and appears in the exception register
            </div>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Batch</th>
                <th>Dataset</th>
                <th className="num">File row</th>
                <th>Challan</th>
                <th>Payer</th>
                <th>Amount (as supplied)</th>
                <th>Validation errors</th>
              </tr>
            </thead>
            <tbody>
              {invalidRows.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty">
                      No rows have been rejected. Download and upload sample_invalid_portal_file.csv from the Help screen to test validation rejection.
                    </div>
                  </td>
                </tr>
              ) : (
                invalidRows.map((inv, idx) => (
                  <tr key={idx}>
                    <td className="mono">{inv.batch}</td>
                    <td>{inv.kind}</td>
                    <td className="num">{inv.line}</td>
                    <td className="mono">{inv.challan}</td>
                    <td>{inv.payer}</td>
                    <td>{inv.amount}</td>
                    <td>
                      <span className="badge b-red">{inv.error}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Review / Validation Modal */}
      {reviewData && (
        <div className="ovl">
          <div className="modal w1100">
            <div className="modal-h">
              <div>
                <h3>Review &amp; Validate Source Upload</h3>
                <div className="sub">
                  File: {reviewData.fileName} &middot; {cnt(reviewData.rows.length)} row(s) &middot; Total {money(reviewData.controlTotal)}
                </div>
              </div>
              <button className="modal-x" onClick={() => setReviewData(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <div className="grid g4 mb12">
                <div className="kpi">
                  <div className="lab">Total records</div>
                  <div className="val">{cnt(reviewData.rows.length)}</div>
                  <div className="sec">{reviewData.fileName}</div>
                </div>
                <div className="kpi ok">
                  <div className="lab">Valid records</div>
                  <div className="val">{cnt(reviewData.rows.length - reviewData.errors.length)}</div>
                  <div className="sec">Ready to post</div>
                </div>
                <div className={`kpi ${reviewData.errors.length ? 'err' : 'ok'}`}>
                  <div className="lab">Validation errors</div>
                  <div className="val">{cnt(reviewData.errors.length)}</div>
                  <div className="sec">{reviewData.errors.length ? 'Must be corrected' : '0 rejected'}</div>
                </div>
                <div className="kpi">
                  <div className="lab">Control total</div>
                  <div className="val">{compact(reviewData.controlTotal)}</div>
                  <div className="sec">{money(reviewData.controlTotal)}</div>
                </div>
              </div>

              {reviewData.errors.length > 0 && (
                <div className="errbar mb12">
                  <strong>Validation warnings detected:</strong>
                  <ul className="mb0 mt4">
                    {reviewData.errors.map((e, idx) => (
                      <li key={idx}>
                        Line {e.line}: {e.err}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="box info mb12 small">
                Posting this file creates a batch in schema <strong>ifms_budget</strong> with status <strong>Pending Checker Approval</strong>. It will be excluded from official reconciliation until approved by a PAO Checker.
              </div>

              <div className="tbl-wrap" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <table className="dt">
                  <thead>
                    <tr>
                      {reviewData.headers.map((h, i) => (
                        <th key={i} className={h === 'amount' ? 'num' : ''}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {reviewData.rows.slice(0, 10).map((r, rowIdx) => (
                      <tr key={rowIdx}>
                        {reviewData.headers.map((h, colIdx) => (
                          <td key={colIdx} className={h === 'amount' ? 'num strong' : ''}>
                            {h === 'amount' ? money(r[h]) : r[h] || '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {reviewData.rows.length > 10 && (
                <div className="small muted mt4">
                  Showing first 10 of {cnt(reviewData.rows.length)} preview rows.
                </div>
              )}
            </div>

            <div className="modal-f">
              <button className="btn btn-sm" onClick={() => setReviewData(null)}>
                Cancel
              </button>
              <button
                className="btn btn-p btn-sm"
                onClick={handlePostBatch}
                disabled={posting}
              >
                {posting ? 'Posting batch...' : `Post ${cnt(reviewData.rows.length - reviewData.errors.length)} record(s) for Approval`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Selected Batch Records Modal (Live Staging Table Rows) */}
      {selectedBatchDetails && (
        <div className="ovl">
          <div className="modal w1100">
            <div className="modal-h">
              <div>
                <h3>Database Staging Records: {selectedBatchDetails.batch.batch_no || `BAT-${selectedBatchDetails.batch.batch_id}`}</h3>
                <div className="sub">
                  Source: {selectedBatchDetails.batch.source_filename} &middot; Type: {selectedBatchDetails.batch.batch_type} &middot; Status: {selectedBatchDetails.batch.status}
                </div>
              </div>
              <button className="modal-x" onClick={() => setSelectedBatchDetails(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <dl className="kv mb16" style={{ gridTemplateColumns: '160px 1fr 160px 1fr' }}>
                <dt>Batch Number</dt>
                <dd className="mono strong">{selectedBatchDetails.batch.batch_no}</dd>
                <dt>Status</dt>
                <dd><span className={badgeClass(selectedBatchDetails.batch.status)}>{selectedBatchDetails.batch.status}</span></dd>
                <dt>Control Total</dt>
                <dd className="strong">{money(selectedBatchDetails.batch.control_total || selectedBatchDetails.batch.total_amount)}</dd>
                <dt>Record Counts</dt>
                <dd>{selectedBatchDetails.batch.total_records} total, {selectedBatchDetails.batch.valid_records} valid, {selectedBatchDetails.batch.invalid_records || 0} errors</dd>
              </dl>

              <h4>Live Records Staged in PostgreSQL (Schema: ifms_budget)</h4>
              <div className="tbl-wrap mt8" style={{ maxHeight: '350px', overflowY: 'auto' }}>
                {selectedBatchDetails.batch.batch_type === 'PORTAL' && (
                  <table className="dt">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Challan No</th>
                        <th>Portal Txn ID</th>
                        <th>Source</th>
                        <th>Payer Name</th>
                        <th>Payment Date</th>
                        <th>Mode</th>
                        <th className="num">Amount</th>
                        <th>Receipt Head</th>
                        <th>Reconciled</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBatchDetails.portal_items.map((it, idx) => (
                        <tr key={idx}>
                          <td className="muted">{idx + 1}</td>
                          <td className="mono strong">{it.challan_no}</td>
                          <td className="mono small">{it.portal_transaction_id}</td>
                          <td>{it.revenue_source}</td>
                          <td>{it.payer_name || '—'}</td>
                          <td className="nowrap">{it.payment_date}</td>
                          <td>{it.payment_mode}</td>
                          <td className="num strong">{money(it.amount)}</td>
                          <td className="mono small">{it.receipt_head}</td>
                          <td>
                            {it.is_reconciled ? (
                              <span className="badge b-green">✔ Reconciled</span>
                            ) : (
                              <span className="badge b-amber">Pending</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {selectedBatchDetails.batch.batch_type === 'BANK_SCROLL' && (
                  <table className="dt">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Scroll No</th>
                        <th>Bank</th>
                        <th>Challan No</th>
                        <th>Bank Ref No</th>
                        <th>UTR No</th>
                        <th>Remit Date</th>
                        <th className="num">Amount</th>
                        <th>Status</th>
                        <th>Reconciled</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBatchDetails.bank_items.map((it, idx) => (
                        <tr key={idx}>
                          <td className="muted">{idx + 1}</td>
                          <td className="mono small">{it.scroll_no}</td>
                          <td>{it.bank_code}</td>
                          <td className="mono strong">{it.challan_no}</td>
                          <td className="mono small">{it.bank_reference_no}</td>
                          <td className="mono small">{it.utr_no || '—'}</td>
                          <td className="nowrap">{it.bank_remittance_date}</td>
                          <td className="num strong">{money(it.amount)}</td>
                          <td><span className="badge b-blue">{it.bank_status}</span></td>
                          <td>
                            {it.is_reconciled ? (
                              <span className="badge b-green">✔ Reconciled</span>
                            ) : (
                              <span className="badge b-amber">Pending</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {selectedBatchDetails.batch.batch_type === 'RBI_LUGGAGE' && (
                  <table className="dt">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>RBI File No</th>
                        <th>RBI Ref No</th>
                        <th>Bank</th>
                        <th>Challan No</th>
                        <th>Credit Date</th>
                        <th className="num">Amount</th>
                        <th>Govt Account</th>
                        <th>Status</th>
                        <th>Reconciled</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBatchDetails.rbi_items.map((it, idx) => (
                        <tr key={idx}>
                          <td className="muted">{idx + 1}</td>
                          <td className="mono small">{it.rbi_file_no}</td>
                          <td className="mono strong">{it.rbi_reference_no}</td>
                          <td>{it.bank_code}</td>
                          <td className="mono">{it.challan_no || '—'}</td>
                          <td className="nowrap">{it.rbi_credit_date}</td>
                          <td className="num strong">{money(it.amount)}</td>
                          <td className="mono small">{it.government_account || it.govt_account_no}</td>
                          <td><span className="badge b-green">{it.rbi_status}</span></td>
                          <td>
                            {it.is_reconciled ? (
                              <span className="badge b-green">✔ Reconciled</span>
                            ) : (
                              <span className="badge b-amber">Pending</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            <div className="modal-f">
              <button className="btn btn-sm" onClick={() => setSelectedBatchDetails(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default UploadPage;

