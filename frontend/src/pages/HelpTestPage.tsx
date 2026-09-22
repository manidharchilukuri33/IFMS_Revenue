import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { downloadText } from '../utils/format';

const SAMPLE_FILES = [
  {
    key: 'portal',
    file: 'sample_portal_transactions.csv',
    title: 'Departmental portal / challan transactions',
    note: 'Core dataset — 16 rows covering clean matches, a partial settlement, a mismatch, a portal-only record and a duplicate candidate.',
    rows: 16,
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
  {
    key: 'bank',
    file: 'sample_agency_bank_scroll.csv',
    title: 'Agency bank payment scroll',
    note: '19 rows across SBI / HDFC / ICICI / PNB including split settlements, a duplicate scroll line, late remittances and a bank-only receipt.',
    rows: 19,
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
  {
    key: 'rbi',
    file: 'sample_rbi_luggage_file.csv',
    title: 'RBI luggage file / Government account credit',
    note: '18 confirmed credits to the Government account, including split credits and one credit with no portal record (RAT).',
    rows: 18,
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
  {
    key: 'invalid',
    file: 'sample_invalid_portal_file.csv',
    title: 'Invalid portal file (negative test)',
    note: '4 deliberately defective rows — non-numeric amount, missing portal transaction ID, unknown portal and an invalid date.',
    rows: 4,
    text: `portal_name,revenue_source,department_code,pao_code,ddo_code,portal_transaction_id,challan_no,cpin,cin,payer_id,payer_name,payment_date,service_date,payment_mode,amount,receipt_head,service_description,penalty_amount,portal_status
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-001,CH-GST-BAD-001,CPIN-BAD-001,CIN-BAD-001,GSTIN27BAD0001B1Z1,Invalid Amount Pvt Ltd,2026-09-12,2026-09-12,NETBANKING,ABC,0040-00-102-01-00-01,Invalid amount test,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,,CH-GST-BAD-002,CPIN-BAD-002,CIN-BAD-002,GSTIN27BAD0002B1Z1,Missing Portal Transaction,2026-09-12,2026-09-12,UPI,1000.00,0040-00-102-01-00-01,Missing ID test,0.00,PAID
UNKNOWN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-003,CH-GST-BAD-003,CPIN-BAD-003,CIN-BAD-003,GSTIN27BAD0003B1Z1,Unknown Portal,2026-09-12,2026-09-12,NETBANKING,2000.00,0040-00-102-01-00-01,Invalid portal test,0.00,PAID
GSTN,GST,TT,PAO21,DDO-TT-001,GSTN-BAD-004,CH-GST-BAD-004,CPIN-BAD-004,CIN-BAD-004,GSTIN27BAD0004B1Z1,Invalid Date,2026-99-99,2026-09-12,NETBANKING,3000.00,0040-00-102-01-00-01,Invalid date test,0.00,PAID`,
  },
];

const GLOSSARY = [
  ['CPIN', 'Common Portal Identification Number — the reference generated by a revenue portal (notably GSTN) when a challan is created, before payment is made.'],
  ['CIN', 'Challan Identification Number — generated by the collecting bank once payment succeeds. It ties the portal challan to the bank credit and is the strongest three-way reconciliation key.'],
  ['Challan', 'The instrument through which a payer deposits government revenue, carrying the receipt head, payer particulars and amount.'],
  ['Bank scroll', 'The daily statement sent by an agency bank listing every government receipt collected by its branches, with the remittance particulars.'],
  ['UTR', 'Unique Transaction Reference — the reference of the inter-bank fund transfer that carries the collection to the government account.'],
  ['RBI luggage file', 'The file sent by the RBI Central Accounts Section confirming credits to the government revenue account, used as the final leg of reconciliation.'],
  ['Suspend', 'A portal receipt that has not been confirmed by an RBI government-account credit after the permitted SLA. The portal amount exceeds the RBI amount and the receipt is held in suspense.'],
  ['RAT', 'Receipt Awaiting Transfer — a bank or RBI credit with no corresponding departmental portal record. The RBI amount exceeds the portal amount and the credit is parked in the RAT suspense head until identified.'],
  ['Receipt booking', 'The accounting entry that credits the applicable revenue receipt head on completion of three-way reconciliation, made by a PAO Maker and approved by a PAO Checker.'],
  ['Penal interest', 'Interest chargeable to an agency bank when government revenue is not remitted within the permitted period, computed on a simple daily basis.'],
  ['Refund', 'Return of stamp duty or other revenue to a payer, either on cancellation of a non-judicial stamp or under a court order in the case of judicial stamps.'],
  ['Devolution', 'The share of revenue collected by the state on behalf of municipal corporations and district local bodies, computed from reconciled collections and settled by a devolution advice.'],
];

export const HelpTestPage: React.FC = () => {
  const { userRole, showToast, triggerRefresh } = useApp();
  const [runningTests, setRunningTests] = useState(false);
  const [testResults, setTestResults] = useState<any[] | null>(null);

  const canRunTests = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'].includes(userRole);

  const handleRunTestSuite = async () => {
    if (!canRunTests) return;
    try {
      setRunningTests(true);
      const res = await api.runTestSuite();
      const mapped = (res.results || []).map((t: any) => ({
        test_id: t.test_id,
        name: t.name,
        expected: t.expected || 'Schema and business rule compliance',
        actual: t.actual || t.details || 'Verified in live database',
        pass: t.pass !== undefined ? Boolean(t.pass) : t.status === 'PASS',
        status: t.status || (t.pass ? 'PASS' : 'FAIL'),
        details: t.details || t.actual || '',
      }));
      setTestResults(mapped);
      const passedCount = res.passed ?? mapped.filter((x: any) => x.pass).length;
      const failedCount = res.failed ?? mapped.filter((x: any) => !x.pass).length;
      showToast(`Demo Test Suite Completed: ${passedCount} passed, ${failedCount} failed.`, failedCount === 0 ? 'success' : 'warn');
      triggerRefresh();
    } catch (err: any) {
      showToast(`Test suite execution failed: ${err.message || err}`, 'error');
      setTestResults(null);
    } finally {
      setRunningTests(false);
    }
  };

  const handleDownloadSingle = (fileObj: any) => {
    downloadText(fileObj.file, fileObj.text);
    showToast(`Downloaded ${fileObj.file}`, 'success');
  };

  const handleDownloadAll = () => {
    SAMPLE_FILES.forEach((f, idx) => {
      setTimeout(() => {
        downloadText(f.file, f.text);
      }, idx * 250);
    });
    showToast('Downloading all sample CSV files...', 'success');
  };

  const totalTests = testResults ? testResults.length : 0;
  const passedTests = testResults ? testResults.filter(t => t.pass).length : 0;
  const failedTests = testResults ? testResults.filter(t => !t.pass).length : 0;
  const healthRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0;

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Help &amp; Sample Formats</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Help, Sample File Formats &amp; Test Guide</h2>
          <div className="sub">
            Process flow, terminology, accepted CSV formats, testing instructions, expected results and the limitations of this prototype.
          </div>
        </div>
        <div className="flex gap8">
          {canRunTests && (
            <button
              className="btn btn-p btn-sm"
              onClick={handleRunTestSuite}
              disabled={runningTests}
            >
              {runningTests ? 'Running tests...' : '▶ Run Demo Test Suite'}
            </button>
          )}
        </div>
      </div>

      {/* Test Suite Results Display */}
      {testResults && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Demo Test Suite Execution Results</h3>
              <div className="sub">
                {passedTests} of {totalTests} test cases passed ({healthRate}%)
              </div>
            </div>
          </div>
          <div className="card-b">
            <div className="grid g3 mb12">
              <div className={`kpi ${passedTests === totalTests && totalTests > 0 ? 'ok' : ''}`}>
                <div className="lab">Passed</div>
                <div className="val">{passedTests}</div>
                <div className="sec">{healthRate}% pass rate</div>
              </div>
              <div className={`kpi ${failedTests > 0 ? 'err' : 'ok'}`}>
                <div className="lab">Failed</div>
                <div className="val">{failedTests}</div>
                <div className="sec">{failedTests > 0 ? `${failedTests} action items required` : '0 regressions'}</div>
              </div>
              <div className={`kpi ${healthRate === 100 ? 'ok' : healthRate >= 80 ? 'warn' : 'err'}`}>
                <div className="lab">Health status</div>
                <div className="val">{healthRate}%</div>
                <div className="sec">{failedTests === 0 ? 'PostgreSQL live & operational' : 'System discrepancies detected'}</div>
              </div>
            </div>

            <div className="tbl-wrap">
              <table className="dt">
                <thead>
                  <tr>
                    <th>Test Case Description</th>
                    <th>Expected Verification</th>
                    <th>Actual Outcome</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {testResults.map((t, idx) => (
                    <tr key={idx}>
                      <td><strong>{t.name}</strong></td>
                      <td className="small">{t.expected}</td>
                      <td className="small">{t.actual}</td>
                      <td>
                        {t.pass ? (
                          <span className="badge b-green">&#10003; PASS</span>
                        ) : (
                          <span className="badge b-red">&#10007; FAIL</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Card 1: Process Flow */}
      <div className="card">
        <div className="card-h">
          <h3>Reconciliation process flow</h3>
        </div>
        <div className="card-b">
          <div className="steps">
            {[
              'Portal / Challan',
              'Agency Bank',
              'RBI Government Account',
              'IFMS Reconciliation',
              'PAO Review',
              'Receipt Booking',
            ].map((s, idx) => (
              <div key={idx} className={`step ${idx === 3 ? 'cur' : 'done'}`}>
                <span className="n">Step {idx + 1}</span>
                {s}
              </div>
            ))}
          </div>
          <div className="small mt12">
            A receipt is only treated as fully reconciled when all three legs agree &mdash; the departmental portal record, the agency bank scroll line and the RBI government-account credit. The presence of a bank record alone is never sufficient for Matched status.
          </div>
        </div>
      </div>

      {/* Card 2: Sample CSV Files */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Included sample CSV files</h3>
            <div className="sub">Download, inspect and upload these through the Data Upload Centre</div>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>File</th>
                <th>Contents</th>
                <th className="num">Rows</th>
                <th>Download</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLE_FILES.map(f => (
                <tr key={f.key}>
                  <td>
                    <strong>{f.title}</strong>
                    <div className="tiny mono muted">{f.file}</div>
                  </td>
                  <td className="small">{f.note}</td>
                  <td className="num">{f.rows}</td>
                  <td>
                    <button
                      className="btn btn-xs btn-p"
                      onClick={() => handleDownloadSingle(f)}
                    >
                      &#11015; Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card-b">
          <button className="btn btn-p btn-sm" onClick={handleDownloadAll}>
            &#11015; Download all sample files
          </button>
        </div>
      </div>

      {/* Card 3: Accepted CSV Formats */}
      <div className="card">
        <div className="card-h">
          <h3>Accepted CSV formats and field definitions</h3>
        </div>
        <div className="card-b">
          <h4 className="mb4">1. Departmental Portal Transactions File</h4>
          <div className="formula mb8">
            portal_name,revenue_source,department_code,pao_code,ddo_code,portal_transaction_id,challan_no,cpin,cin,payer_id,payer_name,payment_date,service_date,payment_mode,amount,receipt_head,service_description,penalty_amount,portal_status
          </div>
          <div className="small mb16">
            <strong>Mandatory:</strong> portal_name, revenue_source, department_code, pao_code, portal_transaction_id, payment_date, payment_mode, amount, receipt_head, portal_status
          </div>

          <h4 className="mb4">2. Agency Bank Payment Scroll File</h4>
          <div className="formula mb8">
            scroll_no,scroll_date,bank_code,branch_code,revenue_source,department_code,pao_code,challan_no,cpin,cin,bank_reference_no,utr_no,payer_id,payer_name,payment_mode,payment_received_date,instrument_realization_date,bank_remittance_date,amount,receipt_head,bank_status
          </div>
          <div className="small mb16">
            <strong>Mandatory:</strong> scroll_no, scroll_date, bank_code, revenue_source, challan_no, payment_mode, payment_received_date, bank_remittance_date, amount, bank_status
          </div>

          <h4 className="mb4">3. RBI Luggage File / Government Account Credit</h4>
          <div className="formula mb8">
            rbi_file_no,rbi_file_date,rbi_reference_no,bank_code,revenue_source,department_code,pao_code,challan_no,cin,bank_reference_no,utr_no,rbi_credit_date,amount,receipt_head,government_account,rbi_status
          </div>
          <div className="small">
            <strong>Mandatory:</strong> rbi_file_no, rbi_file_date, rbi_reference_no, bank_code, rbi_credit_date, amount, government_account, rbi_status
          </div>
        </div>
      </div>

      {/* Card 4: Terminology */}
      <div className="card">
        <div className="card-h">
          <h3>Terminology &amp; Key Definitions</h3>
        </div>
        <div className="card-b">
          <dl className="kv" style={{ gridTemplateColumns: '180px 1fr' }}>
            {GLOSSARY.map(([term, def]) => (
              <React.Fragment key={term}>
                <dt>{term}</dt>
                <dd className="small">{def}</dd>
              </React.Fragment>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
};
export default HelpTestPage;
