import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, fmtDate, fmtDateDash, fmtStamp, badgeClass, exportCSV } from '../utils/format';

interface VoucherItem {
  id: number;
  srNo?: number;
  no: string;
  kind: 'RECEIPT' | 'REFUND' | 'DEVOLUTION';
  date: string;
  period: string;
  pao: string;
  dept: string;
  reconId?: string;
  debit: string;
  credit: string;
  amount: number;
  status: 'Draft' | 'Approved' | 'Rejected' | 'DRAFT' | 'APPROVED' | 'REJECTED' | string;
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

  // Modals
  const [selectedVoucher, setSelectedVoucher] = useState<VoucherItem | null>(null);
  const [createVchRow, setCreateVchRow] = useState<any | null>(null);
  const [vchNarration, setVchNarration] = useState('Receipt booked on three-way reconciliation completion');

  const canCreate = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'].includes(userRole);
  const canApprove = ['SYSADMIN', 'TRE_ADMIN', 'PAO_CHECK'].includes(userRole);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [reconRes, vchRes, suspRes] = await Promise.all([
        api.getReconciliationResults({ limit: 500 }),
        api.getReceiptVouchers().catch(() => ({ total: 0, items: [] })),
        api.getSuspenseItems().catch(() => ({ total: 0, items: [] })),
      ]);

      const items = reconRes?.items || [];
      const ready: any[] = [];
      const booked: any[] = [];
      const blocked: any[] = [];

      items.forEach((r: any, idx: number) => {
        const item = {
          id: r.id || r.recon_id || idx + 1,
          revId: r.rev_transaction_id || r.rev_id || `REV-TXN-${String(r.id || idx + 1).padStart(5, '0')}`,
          challan: r.challan_no || `CH-GST-1000${idx + 1}`,
          payer: r.payer_name || 'Commercial Entity',
          source: r.revenue_source || 'GST',
          pao: r.pao_code || 'PAO21',
          head: r.receipt_head || '0040-00-102-01-00-01',
          headDesc: 'SGST Collections & Receipts',
          rbiAmt: Number(r.rbi_total || r.portal_total || r.amount || 125000),
          rbiDate: r.rbi_credit_date || r.payment_date || '2026-09-10',
          status: r.status || 'Matched',
          booking: r.booking_status || (r.status === 'Matched' ? 'Ready' : 'Blocked'),
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
      const mappedVch: VoucherItem[] = vchItems.map((v: any, idx: number) => ({
        id: v.voucher_id || v.id || idx + 1,
        srNo: v.sr_no || v.voucher_id || idx + 1,
        no: v.voucher_no || v.voucher_number || v.no || `VCH-2026-${String(idx + 1).padStart(5, '0')}`,
        kind: v.voucher_type || (idx === 0 ? 'RECEIPT' : idx === 1 ? 'REFUND' : 'DEVOLUTION'),
        date: v.voucher_date || '2026-09-12',
        period: v.financial_year || v.period || '2026-09',
        pao: v.pao_code || 'PAO21',
        dept: v.department_name || v.department_code || 'Finance',
        reconId: v.recon_id ? `REV-TXN-${v.recon_id}` : `REC-2026-0000${idx + 1}`,
        debit: v.debit_coa_code ? `${v.debit_coa_code} (${v.debit_coa_name || ''})` : (v.debit_account || '8658-00-102-01-00-01 (Treasury Suspense)'),
        credit: v.credit_coa_code ? `${v.credit_coa_code} (${v.credit_coa_name || ''})` : (v.credit_account || '0040-00-102-01-00-01 (SGST Receipts)'),
        amount: Number(v.amount ?? v.total_amount ?? 125000),
        status: v.status || (idx === 0 ? 'Approved' : 'Draft'),
        maker: v.created_by_name || 'pao21.maker',
        makerAt: v.created_at ? fmtStamp(v.created_at) : '2026-09-12 11:30:00',
        checker: v.approved_by_name,
        checkerAt: v.approved_at ? fmtStamp(v.approved_at) : undefined,
        narration: v.narration || 'Receipt voucher booked on 3-way reconciliation completion',
      }));

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

  const handleCreateVoucher = (r: any) => {
    setCreateVchRow(r);
    setVchNarration(`Receipt booked on three-way reconciliation completion for challan ${r.challan}`);
  };

  const handleConfirmCreateVoucher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createVchRow) return;

    try {
      setLoading(true);
      await api.createSingleVoucher(createVchRow.id, vchNarration);
      showToast(`Receipt voucher created as Draft for ${createVchRow.challan}! Awaiting PAO Checker approval.`, 'success');
      setCreateVchRow(null);
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to create voucher', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkVouchers = async () => {
    if (!readyList.length) {
      showToast('No matched receipts are awaiting voucher creation.', 'warning');
      return;
    }
    try {
      setLoading(true);
      const res = await api.generateVouchersBulk('PAO21');
      showToast(`Booking vouchers generated successfully! (${res.draft_vouchers_count || res.vouchers_created || readyList.length} created)`, 'success');
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
      await api.approveSingleVoucher(v.id, `Approved voucher ${v.no}`);
      showToast(`Receipt voucher ${v.no} approved and posted to General Ledger!`, 'success');
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
      showToast('No draft vouchers awaiting approval.', 'info');
      return;
    }
    try {
      setLoading(true);
      const res = await api.approveVouchersBulk('All draft booking vouchers approved via UI');
      showToast(`Approved and posted all ${res.approved_vouchers_count || res.vouchers_approved || draftVouchers.length} draft vouchers successfully!`, 'success');
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Bulk voucher approval failed', 'error');
    } finally {
      setLoading(false);
    }
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
      'Amount',
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
      v.status,
      v.maker,
      v.checker || '',
    ]);
    exportCSV('ifms_voucher_register.csv', headers, rows, [
      ['Report', 'Receipt Voucher Register'],
      ['Total Vouchers', String(vouchers.length)],
      ['Total Value', money(vouchers.reduce((a, b) => a + b.amount, 0))],
    ]);
  };

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
            <button className="btn btn-p btn-sm" onClick={handleBulkVouchers}>
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

      {/* Suspense Notice Banner */}
      <div className="warnbar">
        <span>&#9888;</span>
        <div>
          <strong>Suspense treatment.</strong> Unreconciled credits are shown against 8658-00-102-00-00-00 (Treasury Suspense) and unidentified credits against 8658-00-101-00-00-00 (RAT Suspense) as draft / provisional entries only.
        </div>
      </div>

      {/* Card 1: Receipts Ready for Booking */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Receipts awaiting booking</h3>
            <div className="sub">
              Matched receipts with three-way confirmation &mdash; PAO Maker creates the voucher, PAO Checker approves it
            </div>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>IFMS Revenue Txn ID</th>
                <th>Challan</th>
                <th>Payer</th>
                <th>Source</th>
                <th>PAO</th>
                <th>Receipt head</th>
                <th className="num">Amount</th>
                <th>RBI credit date</th>
                <th>Booking status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {readyList.length === 0 ? (
                <tr>
                  <td colSpan={10}>
                    <div className="empty">No matched receipt is awaiting booking.</div>
                  </td>
                </tr>
              ) : (
                readyList.map(r => (
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
                    <td className="nowrap">{fmtDateDash(r.rbiDate)}</td>
                    <td><span className="badge b-amber">Ready</span></td>
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
          <button className="btn btn-sm btn-p" onClick={handleExportVouchers}>
            &#11015; Export Voucher Register
          </button>
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
                <th className="num">Amount</th>
                <th>Status</th>
                <th>Maker</th>
                <th>Checker</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {vouchers.length === 0 ? (
                <tr>
                  <td colSpan={15}>
                    <div className="empty">No vouchers have been raised yet.</div>
                  </td>
                </tr>
              ) : (
                vouchers.map((v, idx) => (
                  <tr key={v.id}>
                    <td className="mono muted">{v.srNo || idx + 1}</td>
                    <td className="mono strong">{v.no}</td>
                    <td>
                      <span
                        className={`badge ${
                          v.kind === 'RECEIPT' ? 'b-green' : v.kind === 'REFUND' ? 'b-amber' : 'b-violet'
                        }`}
                      >
                        {v.kind}
                      </span>
                    </td>
                    <td className="nowrap">{fmtDateDash(v.date)}</td>
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
              {blockedList.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty">No record is held in suspense.</div>
                  </td>
                </tr>
              ) : (
                blockedList.map(r => (
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
                        ? 'Cr: 8658-00-101-00-00-00 (RAT Suspense Head) — awaiting identification'
                        : 'Cr: 8658-00-102-00-00-00 (Treasury Suspense) — booking to revenue head blocked'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Voucher Detail Modal */}
      {selectedVoucher && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Receipt Voucher: {selectedVoucher.no}</h3>
                <div className="sub">Accounting Journal Entry &mdash; {money(selectedVoucher.amount)}</div>
              </div>
              <button className="modal-x" onClick={() => setSelectedVoucher(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <dl className="kv mb12">
                <dt>Serial Number (Sr No)</dt>
                <dd className="mono">{selectedVoucher.srNo || selectedVoucher.id}</dd>
                <dt>Voucher Number</dt>
                <dd className="mono strong">{selectedVoucher.no}</dd>
                <dt>Voucher Type</dt>
                <dd>{selectedVoucher.kind} Voucher</dd>
                <dt>Voucher Date</dt>
                <dd>{fmtDate(selectedVoucher.date)}</dd>
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
                    <th>Account</th>
                    <th className="num">Debit</th>
                    <th className="num">Credit</th>
                  </tr>
                </thead>
                <tbody>
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
                </tbody>
                <tfoot>
                  <tr>
                    <td>Total</td>
                    <td className="num strong">{money(selectedVoucher.amount)}</td>
                    <td className="num strong">{money(selectedVoucher.amount)}</td>
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

      {/* Create Voucher Dialog */}
      {createVchRow && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Create Receipt Voucher</h3>
                <div className="sub">Challan: {createVchRow.challan} &mdash; Amount: {money(createVchRow.rbiAmt)}</div>
              </div>
              <button className="modal-x" onClick={() => setCreateVchRow(null)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleConfirmCreateVoucher}>
              <div className="modal-b">
                <div className="box ok mb12 small">
                  <strong>Three-Way Confirmation Verified:</strong> Reconciled across portal, bank scroll, and RBI CAS credit. Ready to credit revenue head.
                </div>

                <dl className="kv mb12">
                  <dt>Debit Account</dt>
                  <dd className="mono">8658-00-102-00-00-00 (Treasury Suspense Clearing)</dd>
                  <dt>Credit Account</dt>
                  <dd className="mono">{createVchRow.head}</dd>
                  <dt>Gross Amount</dt>
                  <dd className="strong">{money(createVchRow.rbiAmt)}</dd>
                </dl>

                <div className="fld">
                  <label>Voucher Narration <span className="req">*</span></label>
                  <textarea
                    className="inp"
                    rows={3}
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
                  Create Draft Voucher
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default AccountingPage;
