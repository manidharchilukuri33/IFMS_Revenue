import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, fmtDate, fmtDateDash, fmtStamp, badgeClass, exportCSV } from '../utils/format';

interface VoucherItem {
  id: number;
  srNo?: number;
  no: string;
  kind: string;
  date: string;
  period: string;
  pao: string;
  dept: string;
  reconId?: string;
  debit: string;
  credit: string;
  amount: number;
  penalInterest?: number;
  slaDelay?: number;
  status: string;
  maker: string;
  makerAt: string;
  checker?: string;
  checkerAt?: string;
  narration: string;
}

export const AccountingPage: React.FC = () => {
  const { userRole, showToast, refreshKey, triggerRefresh } = useApp();
  const [loading, setLoading] = useState(true);
  const [readyList, setReadyList] = useState<any[]>([]);
  const [bookedList, setBookedList] = useState<any[]>([]);
  const [blockedList, setBlockedList] = useState<any[]>([]);
  const [vouchers, setVouchers] = useState<VoucherItem[]>([]);
  const [sysConfig, setSysConfig] = useState<any>(null);

  // Filters for Receipts Awaiting Booking
  const [searchReady, setSearchReady] = useState('');
  const [sourceFilterReady, setSourceFilterReady] = useState('');
  const [paoFilterReady, setPaoFilterReady] = useState('');
  const [delayFilterReady, setDelayFilterReady] = useState('ALL');
  const [dateFromReady, setDateFromReady] = useState('');
  const [dateToReady, setDateToReady] = useState('');
  const [minAmountReady, setMinAmountReady] = useState('');
  const [maxAmountReady, setMaxAmountReady] = useState('');

  // Filters for Voucher Register
  const [searchVch, setSearchVch] = useState('');
  const [statusFilterVch, setStatusFilterVch] = useState('ALL');
  const [kindFilterVch, setKindFilterVch] = useState('ALL');
  const [dateFromVch, setDateFromVch] = useState('');
  const [dateToVch, setDateToVch] = useState('');
  const [minAmountVch, setMinAmountVch] = useState('');
  const [maxAmountVch, setMaxAmountVch] = useState('');

  // Filters for Suspense Position
  const [searchSusp, setSearchSusp] = useState('');
  const [statusFilterSusp, setStatusFilterSusp] = useState('ALL');

  // Single Create Voucher Modal State
  const [createVchRow, setCreateVchRow] = useState<any | null>(null);
  const [vchNo, setVchNo] = useState('');
  const [vchDate, setVchDate] = useState('');
  const [vchPeriod, setVchPeriod] = useState('');
  const [debitAccount, setDebitAccount] = useState('8658-00-102-01-00-01 — Suspense Remittance in Transit / Bank Clearing');
  const [creditAccount, setCreditAccount] = useState('');
  const [vchNarration, setVchNarration] = useState('');

  // Bulk Create Voucher Modal State
  const [showBulkModal, setShowBulkModal] = useState(false);

  // View Voucher Modal
  const [selectedVoucher, setSelectedVoucher] = useState<VoucherItem | null>(null);

  const canCreate = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'].includes(userRole);
  const canApprove = ['SYSADMIN', 'TRE_ADMIN', 'PAO_CHECK'].includes(userRole);

  const calculateFy = (d: Date = new Date()) => {
    const year = d.getFullYear();
    const month = d.getMonth() + 1;
    return month >= 4 ? `${year}-${String(year + 1).slice(-2)}` : `${year - 1}-${String(year).slice(-2)}`;
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const [reconRes, vchRes, suspRes, headsRes, sourcesRes, configRes] = await Promise.all([
        api.getReconciliationResults({ limit: 500 }),
        api.getReceiptVouchers().catch(() => ({ total: 0, items: [] })),
        api.getSuspenseItems().catch(() => ({ total: 0, items: [] })),
        api.getReceiptHeads().catch(() => []),
        api.getRevenueSources().catch(() => []),
        api.getSystemConfig().catch(() => null),
      ]);

      if (configRes) {
        setSysConfig(configRes);
      }

      const headMap = new Map<string, string>();
      if (Array.isArray(headsRes)) {
        headsRes.forEach((h: any) => {
          if (h.code) headMap.set(h.code, h.desc || h.head_name || h.name || h.major_head_description);
        });
      }

      const sourceMap = new Map<string, string>();
      if (Array.isArray(sourcesRes)) {
        sourcesRes.forEach((s: any) => {
          if (s.source_code) sourceMap.set(s.source_code, s.source_name || s.name);
        });
      }

      const items = reconRes?.items || [];
      const ready: any[] = [];
      const booked: any[] = [];
      const blocked: any[] = [];

      items.forEach((r: any, idx: number) => {
        const penalAmt = Number(r.penal_interest_amount ?? r.penal_interest ?? 0);
        const slaDays = Number(r.sla_delay_days || 0);
        const sourceName = sourceMap.get(r.revenue_source) || r.revenue_source || '—';
        const headDescription = r.receipt_head_name || headMap.get(r.receipt_head) || (r.revenue_source ? `${r.revenue_source} Receipts` : 'Revenue Receipt Head');

        const item = {
          id: r.recon_id || r.id || idx + 1,
          revId: r.rev_transaction_id || (r.recon_id ? `REV-2026-${String(r.recon_id).padStart(6, '0')}` : `REV-2026-${String(idx + 1).padStart(6, '0')}`),
          challan: r.challan_no || '—',
          payer: r.payer_name || '—',
          source: sourceName,
          rawSource: r.revenue_source,
          pao: r.pao_code || '—',
          head: r.receipt_head || '—',
          headDesc: headDescription,
          rbiAmt: Number(r.rbi_total || r.portal_total || r.bank_total || 0),
          penalInterest: penalAmt,
          slaDelay: slaDays,
          rbiDate: r.rbi_date || r.rbi_credit_date || r.bank_date || r.portal_date || (r.created_at ? String(r.created_at).substring(0, 10) : ''),
          status: r.status || 'Matched',
          booking: r.booking_status || (r.status === 'Matched' ? 'Ready for Booking' : 'Blocked'),
        };

        if (item.status === 'Matched') {
          if (item.booking === 'Booked' || item.booking === 'BOOKED') {
            booked.push(item);
          } else if (item.booking === 'DRAFT_VOUCHER' || item.booking === 'DRAFT_VOUCHER_CREATED' || item.booking === 'Draft') {
            // Already drafted, awaiting PAO Checker approval
          } else {
            ready.push(item);
          }
        } else {
          blocked.push(item);
        }
      });

      setReadyList(ready);
      setBookedList(booked);
      setBlockedList(blocked);

      const vchItems = Array.isArray(vchRes) ? vchRes : vchRes?.items || [];
      const mappedVch: VoucherItem[] = vchItems.map((v: any, idx: number) => {
        const drText = v.debit_coa_code
          ? `${v.debit_coa_code}${v.debit_coa_name ? ` — ${v.debit_coa_name}` : ''}`
          : (v.debit_account || '8658-00-102-01-00-01 — Suspense Remittance in Transit');

        const crText = v.credit_coa_code
          ? `${v.credit_coa_code}${v.credit_coa_name ? ` — ${v.credit_coa_name}` : ''}`
          : (v.credit_account || '—');

        return {
          id: v.voucher_id || v.id || idx + 1,
          srNo: v.sr_no || v.voucher_id || idx + 1,
          no: v.voucher_no || '—',
          kind: v.voucher_type || 'REVENUE_RECEIPT',
          date: v.voucher_date ? String(v.voucher_date).substring(0, 10) : (v.created_at ? String(v.created_at).substring(0, 10) : ''),
          period: v.financial_year || '—',
          pao: v.pao_code || '—',
          dept: v.department_name || v.department_code || '—',
          reconId: v.recon_id ? `REV-TXN-${v.recon_id}` : (v.bill_no ? `CH-${v.bill_no}` : '—'),
          debit: drText,
          credit: crText,
          amount: Number(v.amount ?? 0),
          penalInterest: Number(v.penal_interest_amount ?? 0),
          slaDelay: Number(v.sla_delay_days ?? 0),
          status: v.status || 'Draft',
          maker: v.created_by_name || (v.prepared_by ? `User #${v.prepared_by}` : 'System'),
          makerAt: v.created_at ? fmtStamp(v.created_at) : (v.prepared_at ? fmtStamp(v.prepared_at) : '—'),
          checker: v.approved_by_name || (v.checker_user_id ? `User #${v.checker_user_id}` : undefined),
          checkerAt: v.approved_at ? fmtStamp(v.approved_at) : undefined,
          narration: v.narration || '',
        };
      });

      setVouchers(mappedVch);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch accounting data', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  const draftVouchers = vouchers.filter(v => v.status === 'Draft' || v.status === 'DRAFT');

  // Open Single Create Voucher Modal matching prototype HTML
  const handleCreateVoucher = (r: any) => {
    setCreateVchRow(r);
    const today = new Date();
    const todayIso = today.toISOString().substring(0, 10);
    const nextVchNumber = `RV-${today.getFullYear()}-${String(r.id).padStart(5, '0')}`;
    const fy = calculateFy(today);

    setVchNo(nextVchNumber);
    setVchDate(todayIso);
    setVchPeriod(fy);
    setDebitAccount(sysConfig?.suspenseHead || '8658-00-102-01-00-01 — Suspense Remittance in Transit / Bank Clearing');
    setCreditAccount(`${r.head} — ${r.headDesc}`);

    const penalSuffix = r.penalInterest > 0 
      ? ` [Penal Interest: ₹${r.penalInterest.toFixed(2)} for ${r.slaDelay} days delay]`
      : '';
    setVchNarration(`Revenue receipt booked on three-way reconciliation of challan ${r.challan} — ${r.payer} — reconciliation ${r.revId}${penalSuffix}.`);
  };

  const handleConfirmCreateVoucher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createVchRow) return;

    try {
      setLoading(true);
      await api.createSingleVoucher({
        recon_id: createVchRow.id,
        narration: vchNarration,
        voucher_date: vchDate,
        voucher_no: vchNo,
      });
      showToast(`Draft voucher ${vchNo} created and routed to the checker.`, 'success');
      setCreateVchRow(null);
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to create voucher', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Open Bulk Modal matching prototype HTML
  const handleOpenBulkModal = () => {
    if (!readyList.length) {
      showToast('No matched receipt is awaiting a voucher.', 'warning');
      return;
    }
    setShowBulkModal(true);
  };

  const handleConfirmBulkVouchers = async () => {
    try {
      setLoading(true);
      setShowBulkModal(false);
      const pao = readyList[0]?.pao !== '—' ? readyList[0]?.pao : undefined;
      const res = await api.generateVouchersBulk(pao);
      showToast(`${res.draft_vouchers_count || res.vouchers_created || readyList.length} draft voucher(s) created.`, 'success');
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Bulk voucher creation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveVoucher = async (v: VoucherItem) => {
    if (!canApprove) return;
    try {
      setLoading(true);
      await api.approveSingleVoucher(v.id, `Approved voucher ${v.no} — receipt booked.`);
      showToast(`Voucher ${v.no} approved — receipt booked.`, 'success');
      setSelectedVoucher(null);
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Approval failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAll = async () => {
    if (!draftVouchers.length) {
      showToast('There are no draft vouchers awaiting approval.', 'info');
      return;
    }
    try {
      setLoading(true);
      const res = await api.approveVouchersBulk('Verified and approved all draft booking vouchers');
      showToast(`${res.approved_vouchers_count || res.vouchers_approved || draftVouchers.length} voucher(s) approved.`, 'success');
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Bulk voucher approval failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const filteredReady = readyList.filter(r => {
    if (searchReady) {
      const q = searchReady.toLowerCase();
      const matches = (
        r.revId?.toLowerCase().includes(q) ||
        r.challan?.toLowerCase().includes(q) ||
        r.payer?.toLowerCase().includes(q) ||
        r.source?.toLowerCase().includes(q) ||
        r.pao?.toLowerCase().includes(q) ||
        r.head?.toLowerCase().includes(q)
      );
      if (!matches) return false;
    }
    if (sourceFilterReady && r.rawSource !== sourceFilterReady && r.source !== sourceFilterReady) {
      return false;
    }
    if (paoFilterReady && r.pao !== paoFilterReady) {
      return false;
    }
    if (delayFilterReady === 'WITH_PENAL' && (!r.penalInterest || r.penalInterest <= 0)) {
      return false;
    }
    if (delayFilterReady === 'ON_TIME' && r.penalInterest && r.penalInterest > 0) {
      return false;
    }
    // Amount range filter (from min to max)
    if (minAmountReady !== '' && !isNaN(Number(minAmountReady))) {
      if (r.rbiAmt < Number(minAmountReady)) return false;
    }
    if (maxAmountReady !== '' && !isNaN(Number(maxAmountReady))) {
      if (r.rbiAmt > Number(maxAmountReady)) return false;
    }
    // Date range filter
    if (dateFromReady && r.rbiDate && r.rbiDate < dateFromReady) {
      return false;
    }
    if (dateToReady && r.rbiDate && r.rbiDate > dateToReady) {
      return false;
    }
    return true;
  });

  const filteredVouchers = vouchers.filter(v => {
    if (searchVch) {
      const q = searchVch.toLowerCase();
      const matches = (
        v.no?.toLowerCase().includes(q) ||
        v.reconId?.toLowerCase().includes(q) ||
        v.debit?.toLowerCase().includes(q) ||
        v.credit?.toLowerCase().includes(q) ||
        v.maker?.toLowerCase().includes(q) ||
        v.checker?.toLowerCase().includes(q) ||
        v.dept?.toLowerCase().includes(q) ||
        v.pao?.toLowerCase().includes(q)
      );
      if (!matches) return false;
    }
    if (statusFilterVch !== 'ALL' && v.status !== statusFilterVch) {
      return false;
    }
    if (kindFilterVch !== 'ALL' && v.kind !== kindFilterVch) {
      return false;
    }
    if (minAmountVch !== '' && !isNaN(Number(minAmountVch))) {
      if (v.amount < Number(minAmountVch)) return false;
    }
    if (maxAmountVch !== '' && !isNaN(Number(maxAmountVch))) {
      if (v.amount > Number(maxAmountVch)) return false;
    }
    if (dateFromVch && v.date && v.date < dateFromVch) {
      return false;
    }
    if (dateToVch && v.date && v.date > dateToVch) {
      return false;
    }
    return true;
  });

  const filteredBlocked = blockedList.filter(b => {
    if (searchSusp) {
      const q = searchSusp.toLowerCase();
      const matches = (
        b.revId?.toLowerCase().includes(q) ||
        b.challan?.toLowerCase().includes(q) ||
        b.payer?.toLowerCase().includes(q) ||
        b.source?.toLowerCase().includes(q)
      );
      if (!matches) return false;
    }
    if (statusFilterSusp !== 'ALL' && b.status !== statusFilterSusp) {
      return false;
    }
    return true;
  });

  const handleExportReadyCSV = () => {
    const headers = [
      'IFMS Revenue Txn ID',
      'Challan',
      'Payer',
      'Source',
      'PAO',
      'Receipt Head',
      'Head Description',
      'Gross Amount',
      'Penal Interest',
      'SLA Delay (Days)',
      'RBI Credit Date',
      'Booking Status',
    ];
    const rows = filteredReady.map(r => [
      r.revId,
      r.challan,
      r.payer,
      r.source,
      r.pao,
      r.head,
      r.headDesc,
      r.rbiAmt,
      r.penalInterest,
      r.slaDelay,
      r.rbiDate,
      r.booking,
    ]);
    exportCSV('receipts_awaiting_booking.csv', headers, rows, [
      ['Report', 'Receipts Awaiting Booking'],
      ['Total Records', String(filteredReady.length)],
      ['Total Value', money(filteredReady.reduce((a, b) => a + b.rbiAmt, 0))],
    ]);
  };

  const handleExportVouchers = () => {
    const headers = [
      'Sr No',
      'Voucher No',
      'Type',
      'Voucher Date',
      'Period',
      'PAO',
      'Dept',
      'Linked Reference',
      'Debit Account',
      'Credit Account',
      'Gross Amount',
      'Penal Interest',
      'SLA Delay (Days)',
      'Status',
      'Maker',
      'Checker',
    ];
    const rows = vouchers.map((v, idx) => [
      v.srNo || idx + 1,
      v.no,
      v.kind,
      v.date,
      v.period,
      v.pao,
      v.dept,
      v.reconId || '',
      v.debit,
      v.credit,
      v.amount,
      v.penalInterest || 0,
      v.slaDelay || 0,
      v.status,
      v.maker,
      v.checker || '',
    ]);
    exportCSV('ifms_voucher_register.csv', headers, rows, [
      ['Report', 'Receipt Voucher Register'],
      ['Total Vouchers', String(vouchers.length)],
      ['Total Value', money(vouchers.reduce((a, b) => a + b.amount, 0))],
      ['Total Penal Interest', money(vouchers.reduce((a, b) => a + (b.penalInterest || 0), 0))],
    ]);
  };

  const totalReadyAmt = readyList.reduce((a, b) => a + (b.rbiAmt || 0), 0);
  const totalReadyPenal = readyList.reduce((a, b) => a + (b.penalInterest || 0), 0);

  return (
    <div>
      {/* Breadcrumb matching prototype */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Accounting &amp; Receipt Booking</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Accounting &amp; Receipt Booking</h2>
          <div className="sub">
            Only fully reconciled receipts are booked to the revenue receipt head. Suspend, RAT, Mismatch and Duplicate records are presented as provisional suspense items and cannot be final booked.
          </div>
        </div>
        <div className="btn-group no-print">
          {canCreate && (
            <button className="btn btn-p btn-sm" onClick={handleOpenBulkModal}>
              &#43; Create vouchers for all ready receipts
            </button>
          )}
          {canApprove && draftVouchers.length > 0 && (
            <button className="btn btn-ok btn-sm" onClick={handleApproveAll}>
              &#10003; Approve all draft vouchers ({draftVouchers.length})
            </button>
          )}
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid g4 mb16">
        <div className="kpi ok">
          <div className="lab">Ready for booking</div>
          <div className="val">{cnt(readyList.length)}</div>
          <div className="sec">{money(readyList.reduce((a, b) => a + (b.rbiAmt || 0), 0))}</div>
        </div>
        <div className="kpi">
          <div className="lab">Booked receipts</div>
          <div className="val">{cnt(bookedList.length)}</div>
          <div className="sec">{money(bookedList.reduce((a, b) => a + (b.rbiAmt || 0), 0))}</div>
        </div>
        <div className="kpi warn">
          <div className="lab">Draft vouchers awaiting approval</div>
          <div className="val">{cnt(draftVouchers.length)}</div>
          <div className="sec">{money(draftVouchers.reduce((a, b) => a + (b.amount || 0), 0))}</div>
        </div>
        <div className="kpi err">
          <div className="lab">Blocked from booking</div>
          <div className="val">{cnt(blockedList.length)}</div>
          <div className="sec">{money(blockedList.reduce((a, b) => a + (b.rbiAmt || 0), 0))} in suspense</div>
        </div>
      </div>

      {/* Suspense Notice Banner matching prototype */}
      <div className="warnbar">
        <span>&#9888;</span>
        <div>
          <strong>Suspense treatment.</strong> Unreconciled credits are shown against 8658-00-102-01-00-01 &mdash; Suspense Account (Civil) / Bank Clearing and unidentified credits against 8658-00-110-01-00-01 &mdash; Receipt Awaiting Transfer (RAT) Suspense as draft / provisional entries only, in accordance with the configurable prototype rule.
        </div>
      </div>

      {/* Card 1: Receipts Ready for Booking (Image 2 style) */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Receipts awaiting booking</h3>
            <div className="sub">
              Matched receipts with three-way confirmation &mdash; PAO Maker creates the voucher, PAO Checker approves it
            </div>
          </div>
        </div>
        
        {/* Advanced Filters Toolbar */}
        <div className="p12" style={{ borderBottom: '1px solid var(--grey-200)', background: 'var(--grey-050)' }}>
          <div className="grid g4 gap8 mb8">
            <div className="fld">
              <label className="tiny muted">SEARCH CHALLAN / PAYER / HEAD</label>
              <input
                type="text"
                className="inp sm"
                placeholder="Search in ready receipts..."
                value={searchReady}
                onChange={e => setSearchReady(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">REVENUE SOURCE</label>
              <select
                className="inp sm"
                value={sourceFilterReady}
                onChange={e => setSourceFilterReady(e.target.value)}
              >
                <option value="">All Sources ({readyList.length})</option>
                <option value="GST">GST (Trade &amp; Taxes)</option>
                <option value="DVAT">DVAT (Trade &amp; Taxes)</option>
                <option value="EXCISE">State Excise</option>
                <option value="STAMP">Stamps &amp; Registration</option>
                <option value="TRANSPORT">Transport</option>
                <option value="NONTAX">Non-Tax Revenue</option>
              </select>
            </div>
            <div className="fld">
              <label className="tiny muted">PAY &amp; ACCOUNTS OFFICE</label>
              <select
                className="inp sm"
                value={paoFilterReady}
                onChange={e => setPaoFilterReady(e.target.value)}
              >
                <option value="">All PAOs</option>
                <option value="PAO21">PAO21 (Trade &amp; Taxes)</option>
                <option value="PAO06">PAO06 (DVAT)</option>
                <option value="PAO10">PAO10 (Excise)</option>
                <option value="PAO11">PAO11 (Transport)</option>
                <option value="PAO12">PAO12 (Stamps)</option>
                <option value="PAO15">PAO15 (Non-Tax)</option>
              </select>
            </div>
            <div className="fld">
              <label className="tiny muted">SLA / PENAL INTEREST</label>
              <select
                className="inp sm"
                value={delayFilterReady}
                onChange={e => setDelayFilterReady(e.target.value)}
              >
                <option value="ALL">All Receipts</option>
                <option value="WITH_PENAL">With Accrued Penal Interest</option>
                <option value="ON_TIME">On-Time Remittance (No Penal)</option>
              </select>
            </div>
          </div>

          {/* Row 2: Date Range and Amount Range (₹ 0 to ₹ 99 Crores) */}
          <div className="grid g4 gap8 mb8">
            <div className="fld">
              <label className="tiny muted">DATE FROM</label>
              <input
                type="date"
                className="inp sm"
                value={dateFromReady}
                onChange={e => setDateFromReady(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">DATE TO</label>
              <input
                type="date"
                className="inp sm"
                value={dateToReady}
                onChange={e => setDateToReady(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">FROM AMOUNT (₹)</label>
              <input
                type="number"
                min="0"
                step="1"
                className="inp sm"
                placeholder="₹ 0"
                value={minAmountReady}
                onChange={e => setMinAmountReady(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">TO AMOUNT (₹)</label>
              <input
                type="number"
                min="0"
                max="990000000"
                step="1"
                className="inp sm"
                placeholder="₹ 99,00,00,000 (99 Cr)"
                value={maxAmountReady}
                onChange={e => setMaxAmountReady(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-between items-center mt4">
            <div className="small">
              Showing <strong>{filteredReady.length}</strong> of {readyList.length} ready receipts &middot; Total Gross: <strong className="text-green">{money(filteredReady.reduce((a, b) => a + (b.rbiAmt || 0), 0))}</strong>
              {filteredReady.some(r => r.penalInterest > 0) && (
                <> &middot; Accrued Penal Interest: <strong className="text-amber">{money(filteredReady.reduce((a, b) => a + (b.penalInterest || 0), 0))}</strong></>
              )}
            </div>
            <div className="flex gap8 items-center">
              {(searchReady || sourceFilterReady || paoFilterReady || delayFilterReady !== 'ALL' || dateFromReady || dateToReady || minAmountReady || maxAmountReady) && (
                <button
                  className="btn btn-xs"
                  onClick={() => {
                    setSearchReady('');
                    setSourceFilterReady('');
                    setPaoFilterReady('');
                    setDelayFilterReady('ALL');
                    setDateFromReady('');
                    setDateToReady('');
                    setMinAmountReady('');
                    setMaxAmountReady('');
                  }}
                >
                  Clear Filters
                </button>
              )}
              <button className="btn btn-xs btn-p" onClick={handleExportReadyCSV}>
                &#11015; Export CSV
              </button>
            </div>
          </div>
        </div>

        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>IFMS REVENUE TXN ID</th>
                <th>CHALLAN</th>
                <th>PAYER</th>
                <th>SOURCE</th>
                <th>PAO</th>
                <th>RECEIPT HEAD</th>
                <th className="num">AMOUNT</th>
                <th>RBI CREDIT DATE</th>
                <th>BOOKING STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {filteredReady.length === 0 ? (
                <tr>
                  <td colSpan={10}>
                    <div className="empty">No matched receipt matches the selected filters.</div>
                  </td>
                </tr>
              ) : (
                filteredReady.map(r => (
                  <tr key={r.id}>
                    <td className="mono">{r.revId}</td>
                    <td className="mono">{r.challan}</td>
                    <td>{r.payer}</td>
                    <td>{r.source}</td>
                    <td>{r.pao}</td>
                    <td>
                      <span className="mono tiny" title={r.head}>{r.head}</span>
                      <div className="tiny muted">{r.headDesc}</div>
                    </td>
                    <td className="num strong">{money(r.rbiAmt)}</td>
                    <td className="nowrap">{r.rbiDate ? fmtDateDash(r.rbiDate) : '—'}</td>
                    <td><span className="badge b-amber">{r.booking}</span></td>
                    <td className="nowrap">
                      {canCreate ? (
                        <button className="btn btn-xs btn-p" onClick={() => handleCreateVoucher(r)}>
                          Create voucher
                        </button>
                      ) : (
                        <span className="muted small">PAO Maker only</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Card 2: Receipt Voucher Register */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Receipt voucher register</h3>
            <div className="sub">Receipt, refund and devolution vouchers with maker-checker information</div>
          </div>
        </div>

        {/* Voucher Register Filter Toolbar */}
        <div className="p12" style={{ borderBottom: '1px solid var(--grey-200)', background: 'var(--grey-050)' }}>
          <div className="grid g3 gap8 mb8">
            <div className="fld">
              <label className="tiny muted">SEARCH VOUCHER NO / REFERENCE / USER</label>
              <input
                type="text"
                className="inp sm"
                placeholder="Search voucher register..."
                value={searchVch}
                onChange={e => setSearchVch(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">VOUCHER STATUS</label>
              <select
                className="inp sm"
                value={statusFilterVch}
                onChange={e => setStatusFilterVch(e.target.value)}
              >
                <option value="ALL">All Statuses ({vouchers.length})</option>
                <option value="Draft">Draft (Awaiting Approval)</option>
                <option value="Approved">Approved / Posted</option>
              </select>
            </div>
            <div className="fld">
              <label className="tiny muted">VOUCHER TYPE</label>
              <select
                className="inp sm"
                value={kindFilterVch}
                onChange={e => setKindFilterVch(e.target.value)}
              >
                <option value="ALL">All Voucher Types</option>
                <option value="REVENUE_RECEIPT">Revenue Receipt</option>
                <option value="REFUND">Refund Voucher</option>
                <option value="DEVOLUTION">Devolution Voucher</option>
              </select>
            </div>
          </div>

          {/* Row 2: Date Range and Amount Range (₹ 0 to ₹ 99 Crores) */}
          <div className="grid g4 gap8 mb8">
            <div className="fld">
              <label className="tiny muted">VOUCHER DATE FROM</label>
              <input
                type="date"
                className="inp sm"
                value={dateFromVch}
                onChange={e => setDateFromVch(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">VOUCHER DATE TO</label>
              <input
                type="date"
                className="inp sm"
                value={dateToVch}
                onChange={e => setDateToVch(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">FROM AMOUNT (₹)</label>
              <input
                type="number"
                min="0"
                step="1"
                className="inp sm"
                placeholder="₹ 0"
                value={minAmountVch}
                onChange={e => setMinAmountVch(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">TO AMOUNT (₹)</label>
              <input
                type="number"
                min="0"
                max="990000000"
                step="1"
                className="inp sm"
                placeholder="₹ 99,00,00,000 (99 Cr)"
                value={maxAmountVch}
                onChange={e => setMaxAmountVch(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-between items-center mt4">
            <div className="small">
              Showing <strong>{filteredVouchers.length}</strong> of {vouchers.length} vouchers &middot; Total Value: <strong className="text-green">{money(filteredVouchers.reduce((a, b) => a + (b.amount || 0), 0))}</strong>
            </div>
            <div className="flex gap8 items-center">
              {(searchVch || statusFilterVch !== 'ALL' || kindFilterVch !== 'ALL' || dateFromVch || dateToVch || minAmountVch || maxAmountVch) && (
                <button
                  className="btn btn-xs"
                  onClick={() => {
                    setSearchVch('');
                    setStatusFilterVch('ALL');
                    setKindFilterVch('ALL');
                    setDateFromVch('');
                    setDateToVch('');
                    setMinAmountVch('');
                    setMaxAmountVch('');
                  }}
                >
                  Clear Filters
                </button>
              )}
              <button className="btn btn-xs btn-p" onClick={handleExportVouchers}>
                &#11015; Export Voucher Register
              </button>
            </div>
          </div>
        </div>

        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Sr No</th>
                <th>Voucher no</th>
                <th>Type</th>
                <th>Voucher date</th>
                <th>Period</th>
                <th>PAO</th>
                <th>Dept</th>
                <th>Linked reference</th>
                <th>Debit account</th>
                <th>Credit account</th>
                <th className="num">Gross Amount</th>
                <th className="num">Penal Interest</th>
                <th>Status</th>
                <th>Maker</th>
                <th>Checker</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredVouchers.length === 0 ? (
                <tr>
                  <td colSpan={16}>
                    <div className="empty">No vouchers match the selected filters.</div>
                  </td>
                </tr>
              ) : (
                filteredVouchers.map((v, idx) => (
                  <tr key={v.id}>
                    <td className="mono muted">{v.srNo || idx + 1}</td>
                    <td className="mono strong">{v.no}</td>
                    <td>
                      <span
                        className={`badge ${
                          v.kind === 'RECEIPT' || v.kind === 'REVENUE_RECEIPT'
                            ? 'b-green'
                            : v.kind === 'REFUND'
                            ? 'b-amber'
                            : 'b-violet'
                        }`}
                      >
                        {v.kind}
                      </span>
                    </td>
                    <td className="nowrap">{v.date ? fmtDateDash(v.date) : '—'}</td>
                    <td>{v.period}</td>
                    <td>{v.pao}</td>
                    <td>{v.dept}</td>
                    <td className="mono tiny">{v.reconId || '—'}</td>
                    <td>
                      <div className="small">{v.debit}</div>
                    </td>
                    <td>
                      <div className="small">{v.credit}</div>
                    </td>
                    <td className="num strong">{money(v.amount)}</td>
                    <td className="num">
                      {v.penalInterest && v.penalInterest > 0 ? (
                        <div>
                          <span className="badge b-amber small">{money(v.penalInterest)}</span>
                          {v.slaDelay ? <div className="tiny muted">{v.slaDelay}d delay</div> : null}
                        </div>
                      ) : (
                        <span className="muted">&mdash;</span>
                      )}
                    </td>
                    <td>
                      <span className={badgeClass(v.status)}>{v.status}</span>
                    </td>
                    <td>
                      <div>{v.maker}</div>
                      <div className="tiny muted">{v.makerAt}</div>
                    </td>
                    <td>
                      {v.checker ? (
                        <div>
                          {v.checker}
                          <div className="tiny muted">{v.checkerAt}</div>
                        </div>
                      ) : (
                        <span className="muted">&mdash;</span>
                      )}
                    </td>
                    <td className="nowrap">
                      <button className="btn btn-xs" onClick={() => setSelectedVoucher(v)}>
                        View
                      </button>{' '}
                      {v.status === 'Draft' && canApprove && (
                        <button className="btn btn-xs btn-ok" onClick={() => handleApproveVoucher(v)}>
                          Approve
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Card 3: Suspense / Provisional Position */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Suspense / provisional position</h3>
            <div className="sub">Records blocked from final booking, shown with their provisional treatment</div>
          </div>
        </div>

        {/* Suspense Filter Toolbar */}
        <div className="p12" style={{ borderBottom: '1px solid var(--grey-200)', background: 'var(--grey-050)' }}>
          <div className="grid g2 gap8 mb8">
            <div className="fld">
              <label className="tiny muted">SEARCH RECON ID / CHALLAN / PAYER</label>
              <input
                type="text"
                className="inp sm"
                placeholder="Search suspense items..."
                value={searchSusp}
                onChange={e => setSearchSusp(e.target.value)}
              />
            </div>
            <div className="fld">
              <label className="tiny muted">SUSPENSE TREATMENT TYPE</label>
              <select
                className="inp sm"
                value={statusFilterSusp}
                onChange={e => setStatusFilterSusp(e.target.value)}
              >
                <option value="ALL">All Suspense ({blockedList.length})</option>
                <option value="Suspend">Suspend (Treasury / Civil Suspense 8658-00-102)</option>
                <option value="RAT">RAT (Receipt Awaiting Transfer Suspense 8658-00-110)</option>
              </select>
            </div>
          </div>
          <div className="flex justify-between items-center mt4">
            <div className="small">
              Showing <strong>{filteredBlocked.length}</strong> of {blockedList.length} suspense records &middot; Held Amount: <strong className="text-amber">{money(filteredBlocked.reduce((a, b) => a + (b.rbiAmt || 0), 0))}</strong>
            </div>
            {(searchSusp || statusFilterSusp !== 'ALL') && (
              <button
                className="btn btn-xs"
                onClick={() => {
                  setSearchSusp('');
                  setStatusFilterSusp('ALL');
                }}
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Reconciliation ID</th>
                <th>Challan</th>
                <th>Payer</th>
                <th>Source</th>
                <th>Status</th>
                <th className="num">Amount</th>
                <th>Provisional treatment</th>
              </tr>
            </thead>
            <tbody>
              {filteredBlocked.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty">No record matches the selected suspense filters.</div>
                  </td>
                </tr>
              ) : (
                filteredBlocked.map(r => (
                  <tr key={r.id}>
                    <td className="mono">{r.revId}</td>
                    <td className="mono">{r.challan}</td>
                    <td>{r.payer}</td>
                    <td>{r.source}</td>
                    <td>
                      <span className={badgeClass(r.status)}>{r.status}</span>
                    </td>
                    <td className="num">{money(r.rbiAmt)}</td>
                    <td className="small muted">
                      {r.status === 'RAT'
                        ? 'Cr: 8658-00-110-01-00-01 — Receipt Awaiting Transfer (RAT) Suspense — awaiting identification'
                        : 'Cr: 8658-00-102-01-00-01 — Suspense Account (Civil) / Treasury Suspense — booking to revenue head blocked'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* View Voucher Modal (Image 5 style, preserved as user requested) */}
      {selectedVoucher && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Receipt Voucher: {selectedVoucher.no}</h3>
                <div className="sub">
                  Accounting Journal Entry &mdash; Gross: {money(selectedVoucher.amount)}
                  {selectedVoucher.penalInterest && selectedVoucher.penalInterest > 0
                    ? ` + Penal Int: ${money(selectedVoucher.penalInterest)}`
                    : ''}
                </div>
              </div>
              <button className="modal-x" onClick={() => setSelectedVoucher(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              {/* Financial KPI Summary Cards */}
              <div className="grid g3 mb16">
                <div className="box p12">
                  <div className="lab muted small">Gross Amount</div>
                  <div className="val h3 strong">{money(selectedVoucher.amount)}</div>
                </div>
                <div className={`box p12 ${selectedVoucher.penalInterest && selectedVoucher.penalInterest > 0 ? 'warn' : ''}`}>
                  <div className="lab muted small">Accrued Penal Interest</div>
                  <div className="val h3 strong text-amber">
                    {selectedVoucher.penalInterest && selectedVoucher.penalInterest > 0
                      ? money(selectedVoucher.penalInterest)
                      : '₹ 0.00'}
                  </div>
                  <div className="tiny muted">{selectedVoucher.slaDelay ? `${selectedVoucher.slaDelay} days delay` : 'No delay'}</div>
                </div>
                <div className="box ok p12">
                  <div className="lab muted small">Net Settled Total</div>
                  <div className="val h3 strong text-green">
                    {money(selectedVoucher.amount + (selectedVoucher.penalInterest || 0))}
                  </div>
                </div>
              </div>

              <dl className="kv mb12">
                <dt>Serial Number (Sr No)</dt>
                <dd className="mono">{selectedVoucher.srNo || selectedVoucher.id}</dd>
                <dt>Voucher Number</dt>
                <dd className="mono strong">{selectedVoucher.no}</dd>
                <dt>Voucher Type</dt>
                <dd>{selectedVoucher.kind} Voucher</dd>
                <dt>Voucher Date</dt>
                <dd>{selectedVoucher.date ? fmtDate(selectedVoucher.date) : '—'}</dd>
                <dt>Accounting Period</dt>
                <dd>{selectedVoucher.period}</dd>
                <dt>Department / PAO</dt>
                <dd>{selectedVoucher.dept} &middot; {selectedVoucher.pao}</dd>
                <dt>Linked Reference</dt>
                <dd className="mono">{selectedVoucher.reconId || '—'}</dd>
                <dt>Status</dt>
                <dd><span className={badgeClass(selectedVoucher.status)}>{selectedVoucher.status}</span></dd>
                <dt>Maker</dt>
                <dd>{selectedVoucher.maker} &middot; {selectedVoucher.makerAt}</dd>
                <dt>Checker</dt>
                <dd>{selectedVoucher.checker ? `${selectedVoucher.checker} · ${selectedVoucher.checkerAt}` : 'Awaiting approval'}</dd>
                <dt>Narration</dt>
                <dd>{selectedVoucher.narration}</dd>
              </dl>

              <table className="dt">
                <thead>
                  <tr>
                    <th>ACCOUNT</th>
                    <th className="num">DEBIT</th>
                    <th className="num">CREDIT</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedVoucher.penalInterest && selectedVoucher.penalInterest > 0 ? (
                    <>
                      <tr>
                        <td>{selectedVoucher.debit}</td>
                        <td className="num">{money(selectedVoucher.amount)}</td>
                        <td className="num">&mdash;</td>
                      </tr>
                      <tr>
                        <td>{selectedVoucher.credit}</td>
                        <td className="num">&mdash;</td>
                        <td className="num">{money(selectedVoucher.amount + selectedVoucher.penalInterest)}</td>
                      </tr>
                      <tr>
                        <td>{sysConfig?.penalInterestHead || '8658-00-102-01-00-02 — Accrued Penal Interest — Bank SLA Delay Recoverable'}</td>
                        <td className="num">{money(selectedVoucher.penalInterest)}</td>
                        <td className="num">&mdash;</td>
                      </tr>
                    </>
                  ) : (
                    <>
                      <tr>
                        <td>{selectedVoucher.debit}</td>
                        <td className="num">{money(selectedVoucher.amount)}</td>
                        <td className="num">&mdash;</td>
                      </tr>
                      <tr>
                        <td>{selectedVoucher.credit}</td>
                        <td className="num">&mdash;</td>
                        <td className="num">{money(selectedVoucher.amount)}</td>
                      </tr>
                    </>
                  )}
                </tbody>
                <tfoot>
                  <tr>
                    <td>Total</td>
                    <td className="num strong">{money(selectedVoucher.amount + (selectedVoucher.penalInterest || 0))}</td>
                    <td className="num strong">{money(selectedVoucher.amount + (selectedVoucher.penalInterest || 0))}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div className="modal-f">
              {selectedVoucher.status === 'Draft' && canApprove && (
                <button
                  className="btn btn-ok btn-sm"
                  onClick={() => handleApproveVoucher(selectedVoucher)}
                >
                  Approve Voucher
                </button>
              )}
              <button className="btn btn-sm" onClick={() => setSelectedVoucher(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Single Receipt Voucher Modal (Image 3 HTML prototype layout + Penal Interest) */}
      {createVchRow && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Create receipt voucher</h3>
                <div className="sub">
                  {createVchRow.challan} &mdash; {money(createVchRow.rbiAmt)}
                  {createVchRow.penalInterest > 0 ? ` (+ ${money(createVchRow.penalInterest)} Penal Interest)` : ''}
                </div>
              </div>
              <button className="modal-x" onClick={() => setCreateVchRow(null)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleConfirmCreateVoucher}>
              <div className="modal-b">
                <div className="box info mb12 small">
                  Debit the Suspense / bank clearing account and credit the applicable revenue receipt head.
                </div>

                <div className="grid g2 mb12">
                  <div className="fld">
                    <label>VOUCHER NUMBER</label>
                    <input className="inp" value={vchNo} onChange={e => setVchNo(e.target.value)} readOnly />
                  </div>
                  <div className="fld">
                    <label>VOUCHER DATE</label>
                    <input
                      type="date"
                      className="inp"
                      value={vchDate}
                      onChange={e => setVchDate(e.target.value)}
                      required
                    />
                  </div>
                  <div className="fld">
                    <label>ACCOUNTING PERIOD</label>
                    <input className="inp" value={vchPeriod} readOnly />
                  </div>
                  <div className="fld">
                    <label>AMOUNT (INR)</label>
                    <input className="inp" value={createVchRow.rbiAmt} readOnly />
                  </div>
                </div>

                {/* Penal Interest & Net Settled Total Breakdown Fields */}
                <div className="grid g2 mb12">
                  <div className="fld">
                    <label>PENAL INTEREST ACCRUED (INR)</label>
                    <input
                      className={`inp ${createVchRow.penalInterest > 0 ? 'text-amber strong' : 'muted'}`}
                      value={createVchRow.penalInterest > 0 ? `${money(createVchRow.penalInterest)} (${createVchRow.slaDelay} days delay at Bank Rate + 2%)` : '₹ 0.00 (On-time remittance)'}
                      readOnly
                    />
                  </div>
                  <div className="fld">
                    <label>NET SETTLED TOTAL (INR)</label>
                    <input
                      className="inp text-green strong"
                      value={money(createVchRow.rbiAmt + (createVchRow.penalInterest || 0))}
                      readOnly
                    />
                  </div>
                </div>

                <div className="fld mb12">
                  <label>DEBIT ACCOUNT</label>
                  <input
                    className="inp"
                    value={debitAccount}
                    onChange={e => setDebitAccount(e.target.value)}
                    required
                  />
                </div>

                <div className="fld mb12">
                  <label>CREDIT ACCOUNT</label>
                  <input
                    className="inp"
                    value={creditAccount}
                    onChange={e => setCreditAccount(e.target.value)}
                    required
                  />
                </div>

                {/* Journal Entry Preview Table */}
                <div className="mb12">
                  <div className="sub mb8" style={{ fontWeight: 600, color: 'var(--text-sec)', fontSize: '0.8rem' }}>
                    ACCOUNTING JOURNAL ENTRY PREVIEW (DOUBLE ENTRY)
                  </div>
                  <table className="dt">
                    <thead>
                      <tr>
                        <th>ACCOUNT</th>
                        <th className="num">DEBIT</th>
                        <th className="num">CREDIT</th>
                      </tr>
                    </thead>
                    <tbody>
                      {createVchRow.penalInterest > 0 ? (
                        <>
                          <tr>
                            <td>{debitAccount}</td>
                            <td className="num">{money(createVchRow.rbiAmt)}</td>
                            <td className="num">&mdash;</td>
                          </tr>
                          <tr>
                            <td>{creditAccount}</td>
                            <td className="num">&mdash;</td>
                            <td className="num">{money(createVchRow.rbiAmt + createVchRow.penalInterest)}</td>
                          </tr>
                          <tr>
                            <td>{sysConfig?.penalInterestHead || '8658-00-102-01-00-02 — Accrued Penal Interest — Bank SLA Delay Recoverable'}</td>
                            <td className="num">{money(createVchRow.penalInterest)}</td>
                            <td className="num">&mdash;</td>
                          </tr>
                        </>
                      ) : (
                        <>
                          <tr>
                            <td>{debitAccount}</td>
                            <td className="num">{money(createVchRow.rbiAmt)}</td>
                            <td className="num">&mdash;</td>
                          </tr>
                          <tr>
                            <td>{creditAccount}</td>
                            <td className="num">&mdash;</td>
                            <td className="num">{money(createVchRow.rbiAmt)}</td>
                          </tr>
                        </>
                      )}
                    </tbody>
                    <tfoot>
                      <tr>
                        <td>Total</td>
                        <td className="num strong">{money(createVchRow.rbiAmt + (createVchRow.penalInterest || 0))}</td>
                        <td className="num strong">{money(createVchRow.rbiAmt + (createVchRow.penalInterest || 0))}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                <div className="fld">
                  <label>NARRATION</label>
                  <textarea
                    className="inp"
                    rows={2}
                    value={vchNarration}
                    onChange={e => setVchNarration(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="modal-f">
                <button type="button" className="btn btn-sm" onClick={() => setCreateVchRow(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-p btn-sm">
                  Create draft &amp; route to checker
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Bulk Receipt Vouchers Modal (Image 4 HTML prototype layout) */}
      {showBulkModal && (
        <div className="ovl">
          <div className="modal" style={{ maxWidth: '550px' }}>
            <div className="modal-h">
              <div>
                <h3>Create receipt vouchers</h3>
              </div>
              <button className="modal-x" onClick={() => setShowBulkModal(false)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <div className="box warn mb12 small">
                Draft receipt vouchers will be created for <strong>{readyList.length}</strong> fully reconciled receipt(s) totalling <strong>{money(totalReadyAmt)}</strong>
                {totalReadyPenal > 0 ? ` (plus ${money(totalReadyPenal)} penal interest)` : ''}. Each voucher requires PAO Checker approval before it is treated as booked.
              </div>
            </div>

            <div className="modal-f">
              <button type="button" className="btn btn-sm" onClick={() => setShowBulkModal(false)}>
                Cancel
              </button>
              <button type="button" className="btn btn-p btn-sm" onClick={handleConfirmBulkVouchers}>
                Create vouchers
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default AccountingPage;
