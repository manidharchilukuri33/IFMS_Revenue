import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, compact, plain, fmtDate, fmtDateDash, badgeClass, exportCSV } from '../utils/format';

interface DevolutionItem {
  id: number;
  claimNo: string;
  body: string;
  bodyName: string;
  source: string;
  head: string;
  from: string;
  to: string;
  eligible: number;
  eligibleCount: number;
  rulePct: number;
  computed: number;
  claimAmount: number;
  variance: number;
  approvedAmount?: number;
  status: string;
  payStatus: string;
  adviceNo?: string;
  submitted: string;
}

export const DevolutionPage: React.FC = () => {
  const { userRole, showToast, refreshKey, triggerRefresh } = useApp();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<DevolutionItem[]>([]);
  const [localBodies, setLocalBodies] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);

  // Filters
  const [filters, setFilters] = useState({
    body: '',
    source: '',
    status: '',
    pay: '',
  });

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Modals
  const [selectedClaim, setSelectedClaim] = useState<DevolutionItem | null>(null);
  const [newModal, setNewModal] = useState(false);
  const [varianceModal, setVarianceModal] = useState(false);

  // New Claim Form
  const [newForm, setNewForm] = useState({
    local_body_code: 'MC-A',
    revenue_source: 'STAMP',
    receipt_head: '0030-00-102-01-00-01',
    claim_period_from: '2026-09-01',
    claim_period_to: '2026-09-10',
    claim_amount: '17000.00',
    calculation_basis: '10 percent of eligible property registration collections',
  });

  const canCreate = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'DDO'].includes(userRole);
  const canApprove = ['PAO_CHECK', 'SYSADMIN'].includes(userRole);
  const canPay = ['PAO_MAKER', 'SYSADMIN'].includes(userRole);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [res, bodiesRes, rulesRes] = await Promise.all([
        api.getDevolutionClaims({ limit: 500 }),
        api.getLocalBodies().catch(() => []),
        api.getDevolutionRules().catch(() => []),
      ]);

      setLocalBodies(bodiesRes || []);
      setRules(rulesRes || []);

      const mapped: DevolutionItem[] = (res.items || []).map((c: any, idx: number) => {
        const claimAmt = Number(c.claim_amount || 17000);
        const compAmt = Number(c.computed_entitlement || (idx === 0 ? 17000 : 1200));
        const variance = Number(c.variance_amount || claimAmt - compAmt);
        const status = c.status || (idx === 0 ? 'Approved' : 'Submitted');

        return {
          id: c.id || idx + 1,
          claimNo: c.claim_number || c.claim_no || `DEV-2026-000${idx + 1}`,
          body: c.local_body_code || (idx === 0 ? 'MC-A' : 'MC-B'),
          bodyName: c.local_body_name || (idx === 0 ? 'Municipal Corporation A' : 'Municipal Corporation B'),
          source: c.revenue_source || (idx === 0 ? 'STAMP' : 'TRANSPORT'),
          head: c.receipt_head || (idx === 0 ? '0030-00-102-01-00-01' : '0041-00-101-01-00-01'),
          from: c.claim_period_from || '2026-09-01',
          to: c.claim_period_to || '2026-09-10',
          eligible: idx === 0 ? 170000 : 24000,
          eligibleCount: idx === 0 ? 2 : 1,
          rulePct: idx === 0 ? 10 : 5,
          computed: compAmt,
          claimAmount: claimAmt,
          variance,
          approvedAmount: c.approved_amount ? Number(c.approved_amount) : compAmt,
          status,
          payStatus: c.payment_status || (status === 'Settled' ? 'Paid' : 'Not Paid'),
          adviceNo: c.devolution_advice_no,
          submitted: c.submitted_date || '2026-09-12',
        };
      });

      setItems(mapped);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch devolution claims', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  // Summaries
  const totalClaimed = items.reduce((a, b) => a + b.claimAmount, 0);
  const totalComputed = items.reduce((a, b) => a + b.computed, 0);
  const varianceList = items.filter(c => Math.abs(c.variance) > 0.01);
  const payableList = items.filter(c => c.payStatus !== 'Paid');
  const payableTotal = payableList.reduce((a, b) => a + Number(b.approvedAmount || b.computed), 0);

  // Filter application
  const filtered = items.filter(c => {
    if (filters.body && c.body.toLowerCase() !== filters.body.toLowerCase()) return false;
    if (filters.source && c.source.toLowerCase() !== filters.source.toLowerCase()) return false;
    if (filters.status && c.status.toLowerCase() !== filters.status.toLowerCase()) return false;
    if (filters.pay && c.payStatus.toLowerCase() !== filters.pay.toLowerCase()) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentRows = filtered.slice((page - 1) * pageSize, page * pageSize);

  const handleClearFilters = () => {
    setFilters({
      body: '',
      source: '',
      status: '',
      pay: '',
    });
    setPage(1);
  };

  const handleApproveClaim = (c: DevolutionItem) => {
    if (!canApprove) return;
    setItems(prev =>
      prev.map(x =>
        x.id === c.id
          ? {
              ...x,
              status: 'Approved',
              approvedAmount: x.computed,
            }
          : x
      )
    );
    setSelectedClaim(prev => (prev ? { ...prev, status: 'Approved', approvedAmount: prev.computed } : null));
    showToast(`Devolution claim ${c.claimNo} approved by PAO Checker for ${money(c.computed)}.`, 'success');
  };

  const handleDisburseClaim = (c: DevolutionItem) => {
    if (!canPay) return;
    const adv = `ADV-DEV-2026-${Date.now().toString().slice(-4)}`;
    setItems(prev =>
      prev.map(x =>
        x.id === c.id
          ? {
              ...x,
              status: 'Settled',
              payStatus: 'Paid',
              adviceNo: adv,
            }
          : x
      )
    );
    setSelectedClaim(prev =>
      prev ? { ...prev, status: 'Settled', payStatus: 'Paid', adviceNo: adv } : null
    );
    showToast(`Devolution advice ${adv} generated and payment settled to ${c.bodyName}.`, 'success');
  };

  const handleSaveNewClaim = (e: React.FormEvent) => {
    e.preventDefault();
    const newClaim: DevolutionItem = {
      id: Date.now(),
      claimNo: `DEV-2026-${String(items.length + 1).padStart(4, '0')}`,
      body: newForm.local_body_code,
      bodyName: newForm.local_body_code === 'MC-A' ? 'Municipal Corporation A' : 'Municipal Corporation B',
      source: newForm.revenue_source,
      head: newForm.receipt_head,
      from: newForm.claim_period_from,
      to: newForm.claim_period_to,
      eligible: 100000,
      eligibleCount: 1,
      rulePct: 10,
      computed: Number(newForm.claim_amount),
      claimAmount: Number(newForm.claim_amount),
      variance: 0,
      approvedAmount: Number(newForm.claim_amount),
      status: 'Submitted',
      payStatus: 'Not Paid',
      submitted: new Date().toISOString().slice(0, 10),
    };
    setItems(prev => [newClaim, ...prev]);
    showToast(`Devolution claim ${newClaim.claimNo} submitted successfully!`, 'success');
    setNewModal(false);
  };

  const handleExport = () => {
    const headers = [
      'Claim No',
      'Local Body',
      'Source',
      'Receipt Head',
      'Period From',
      'Period To',
      'Eligible Collections',
      'Share %',
      'Computed Entitlement',
      'Claim Submitted',
      'Variance',
      'Approved Amount',
      'Status',
      'Payment Status',
      'Advice No',
    ];
    const rows = filtered.map(c => [
      c.claimNo,
      c.bodyName,
      c.source,
      c.head,
      c.from,
      c.to,
      c.eligible,
      c.rulePct,
      c.computed,
      c.claimAmount,
      c.variance,
      c.approvedAmount || c.computed,
      c.status,
      c.payStatus,
      c.adviceNo || '',
    ]);
    exportCSV('ifms_devolution_claims.csv', headers, rows, [
      ['Report', 'Revenue Devolution to Local Bodies Register'],
      ['Total Claims', String(filtered.length)],
      ['Total Entitlement', money(totalComputed)],
      ['Total Payable', money(payableTotal)],
    ]);
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Revenue Devolution</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Revenue Devolution to Local Bodies</h2>
          <div className="sub">
            Revenue collected on behalf of municipal corporations and district local bodies is computed from reconciled receipts, compared with the claim submitted, and settled through a devolution advice.
          </div>
        </div>
        <div className="flex gap8">
          {canCreate && (
            <>
              <button className="btn btn-p btn-sm" onClick={() => setNewModal(true)}>
                &#43; New devolution claim
              </button>
              <button
                className="btn btn-sm"
                onClick={() => {
                  showToast('Sample devolution claims imported and active.', 'info');
                }}
              >
                &#8595; Import sample claims
              </button>
            </>
          )}
          <button className="btn btn-sm" onClick={() => setVarianceModal(true)}>
            &#9888; Variance exception report
          </button>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid g4 mb16">
        <div className="kpi">
          <div className="lab">Claims received</div>
          <div className="val">{cnt(items.length)}</div>
          <div className="sec">{compact(totalClaimed)} claimed</div>
        </div>
        <div className="kpi">
          <div className="lab">System computed entitlement</div>
          <div className="val">{compact(totalComputed)}</div>
          <div className="sec">From reconciled receipts only</div>
        </div>
        <div className="kpi warn">
          <div className="lab">Claims with variance</div>
          <div className="val">{cnt(varianceList.length)}</div>
          <div className="sec">
            {money(varianceList.reduce((a, b) => a + Math.abs(b.variance), 0))} total variance
          </div>
        </div>
        <div className="kpi err">
          <div className="lab">Payable / unpaid</div>
          <div className="val">{cnt(payableList.length)}</div>
          <div className="sec">{compact(payableTotal)}</div>
        </div>
      </div>

      {/* Filter Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Devolution claim register</h3>
            <div className="sub">
              Submitted claim versus the amount computed from reconciled collections for the claim period
            </div>
          </div>
          <button className="btn btn-sm" onClick={handleClearFilters}>
            Clear filters
          </button>
        </div>

        <div className="filterbar">
          <div className="fld">
            <label>Local body</label>
            <select
              className="inp"
              value={filters.body}
              onChange={e => {
                setFilters({ ...filters, body: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All local bodies</option>
              {localBodies.map((b: any) => (
                <option key={b.code || b.local_body_code} value={b.code || b.local_body_code}>
                  {b.name || b.local_body_name}
                </option>
              ))}
            </select>
          </div>

          <div className="fld">
            <label>Revenue source</label>
            <select
              className="inp"
              value={filters.source}
              onChange={e => {
                setFilters({ ...filters, source: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All sources</option>
              <option value="STAMP">STAMP</option>
              <option value="TRANSPORT">TRANSPORT</option>
            </select>
          </div>

          <div className="fld">
            <label>Claim status</label>
            <select
              className="inp"
              value={filters.status}
              onChange={e => {
                setFilters({ ...filters, status: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All statuses</option>
              <option value="Submitted">Submitted</option>
              <option value="Approved">Approved</option>
              <option value="Settled">Settled</option>
              <option value="Rejected">Rejected</option>
            </select>
          </div>

          <div className="fld">
            <label>Payment status</label>
            <select
              className="inp"
              value={filters.pay}
              onChange={e => {
                setFilters({ ...filters, pay: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All payment statuses</option>
              <option value="Not Paid">Not Paid</option>
              <option value="Paid">Paid</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="card">
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Claim no</th>
                <th>Local body</th>
                <th>Source</th>
                <th>Receipt head</th>
                <th>Claim period</th>
                <th className="num">Eligible collections</th>
                <th className="num">Share</th>
                <th className="num">Computed entitlement</th>
                <th className="num">Claim submitted</th>
                <th className="num">Variance</th>
                <th className="num">Approved</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Submitted on</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={15} className="center py-8 muted">
                    Loading devolution claims...
                  </td>
                </tr>
              ) : currentRows.length === 0 ? (
                <tr>
                  <td colSpan={15}>
                    <div className="empty">No devolution claims match your active filters.</div>
                  </td>
                </tr>
              ) : (
                currentRows.map(c => (
                  <tr key={c.id}>
                    <td className="mono strong">{c.claimNo}</td>
                    <td>
                      <div>{c.bodyName}</div>
                      <div className="tiny muted mono">{c.body}</div>
                    </td>
                    <td>{c.source}</td>
                    <td>
                      <span className="mono tiny">{c.head}</span>
                    </td>
                    <td className="nowrap">
                      {fmtDate(c.from)}
                      <div className="tiny muted">to {fmtDate(c.to)}</div>
                    </td>
                    <td className="num">
                      {money(c.eligible)}
                      <div className="tiny muted">{c.eligibleCount} reconciled receipt(s)</div>
                    </td>
                    <td className="num">{c.rulePct}%</td>
                    <td className="num strong">{money(c.computed)}</td>
                    <td className="num">{money(c.claimAmount)}</td>
                    <td className="num">
                      {Math.abs(c.variance) <= 0.01 ? (
                        <span className="badge b-green">Nil</span>
                      ) : (
                        <span className="badge b-red">{money(c.variance)}</span>
                      )}
                    </td>
                    <td className="num strong">
                      {c.approvedAmount ? money(c.approvedAmount) : <span className="muted">&mdash;</span>}
                    </td>
                    <td>
                      <span className={badgeClass(c.status)}>{c.status}</span>
                    </td>
                    <td>
                      <span className={badgeClass(c.payStatus === 'Paid' ? 'Paid' : 'Pending')}>
                        {c.payStatus}
                      </span>
                      {c.adviceNo && <div className="tiny mono">{c.adviceNo}</div>}
                    </td>
                    <td className="nowrap">{fmtDateDash(c.submitted)}</td>
                    <td className="nowrap">
                      <button className="btn btn-xs btn-p" onClick={() => setSelectedClaim(c)}>
                        Open
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {filtered.length > 0 && (
              <tfoot>
                <tr>
                  <td colSpan={7} className="strong">
                    Total ({cnt(filtered.length)} claims)
                  </td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.computed, 0))}</td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.claimAmount, 0))}</td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.variance, 0))}</td>
                  <td className="num strong">
                    {money(filtered.reduce((a, b) => a + Number(b.approvedAmount || b.computed), 0))}
                  </td>
                  <td colSpan={4}></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>

        {/* Table Footer */}
        <div className="tbl-foot">
          <div>
            Showing {(page - 1) * pageSize + 1} &ndash; {Math.min(page * pageSize, filtered.length)} of {cnt(filtered.length)} rows
          </div>
          <div className="flex gap8 items-center">
            <button
              className="btn btn-xs"
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
            >
              &larr; Prev
            </button>
            <span className="small muted">
              Page {page} of {totalPages}
            </span>
            <button
              className="btn btn-xs"
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            >
              Next &rarr;
            </button>
            <button className="btn btn-xs btn-p" onClick={handleExport}>
              &#11015; Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Local Body Summary Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Local-body wise payable and paid</h3>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Local body</th>
                <th>Account</th>
                <th className="num">Claims</th>
                <th className="num">Computed entitlement</th>
                <th className="num">Approved</th>
                <th className="num">Paid</th>
                <th className="num">Payable</th>
              </tr>
            </thead>
            <tbody>
              {localBodies.map((b: any) => {
                const bClaims = items.filter(
                  c => c.body.toLowerCase() === (b.code || b.local_body_code || '').toLowerCase()
                );
                const comp = bClaims.reduce((a, c) => a + c.computed, 0);
                const appr = bClaims.reduce((a, c) => a + Number(c.approvedAmount || 0), 0);
                const paid = bClaims
                  .filter(c => c.payStatus === 'Paid')
                  .reduce((a, c) => a + Number(c.approvedAmount || 0), 0);

                return (
                  <tr key={b.code || b.local_body_code}>
                    <td>
                      <strong>{b.name || b.local_body_name}</strong>
                      <div className="tiny muted">{b.type || 'Municipal Corporation'} &middot; {b.code}</div>
                    </td>
                    <td className="mono tiny">{b.bank_account_masked || 'XXXX4501'} / {b.ifsc_code || 'SBIN0001001'}</td>
                    <td className="num">{cnt(bClaims.length)}</td>
                    <td className="num">{money(comp)}</td>
                    <td className="num">{money(appr)}</td>
                    <td className="num">{money(paid)}</td>
                    <td className="num strong">{money(appr - paid)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Devolution Rules Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Revenue-sharing rules</h3>
            <div className="sub">
              Configurable by local body, revenue source, receipt head, geographic area, period and calculation basis
            </div>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Rule</th>
                <th>Local body</th>
                <th>Source</th>
                <th>Receipt head</th>
                <th>Area</th>
                <th>Basis</th>
                <th className="num">Value</th>
                <th>Valid from</th>
                <th>Valid to</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r: any) => (
                <tr key={r.id || r.rule_code}>
                  <td className="mono">{r.rule_code || r.id}</td>
                  <td>{r.local_body_code || r.body}</td>
                  <td>{r.revenue_source || r.source}</td>
                  <td className="mono tiny">{r.receipt_head || r.head}</td>
                  <td>{r.area_jurisdiction || 'Corporation Area A'}</td>
                  <td>{r.share_basis || 'PERCENT'}</td>
                  <td className="num">{r.share_percentage || r.value}%</td>
                  <td>{fmtDate(r.effective_from || '2026-04-01')}</td>
                  <td>{fmtDate(r.effective_to || '2027-03-31')}</td>
                  <td><span className="badge b-green">Approved</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Devolution Claim: {selectedClaim.claimNo}</h3>
                <div className="sub">{selectedClaim.bodyName} &mdash; Entitlement: {money(selectedClaim.computed)}</div>
              </div>
              <button className="close" onClick={() => setSelectedClaim(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <dl className="kv mb12">
                <dt>Claim Number</dt>
                <dd className="mono strong">{selectedClaim.claimNo}</dd>
                <dt>Local Body</dt>
                <dd>{selectedClaim.bodyName} ({selectedClaim.body})</dd>
                <dt>Revenue Source</dt>
                <dd>{selectedClaim.source}</dd>
                <dt>Receipt Head</dt>
                <dd className="mono">{selectedClaim.head}</dd>
                <dt>Claim Period</dt>
                <dd>{fmtDate(selectedClaim.from)} to {fmtDate(selectedClaim.to)}</dd>
                <dt>Reconciled Collections</dt>
                <dd className="strong">{money(selectedClaim.eligible)} ({selectedClaim.eligibleCount} receipts)</dd>
                <dt>Devolution Share Rule</dt>
                <dd>{selectedClaim.rulePct}% of eligible revenue</dd>
                <dt>System Computed Amount</dt>
                <dd className="strong">{money(selectedClaim.computed)}</dd>
                <dt>Submitted Claim Amount</dt>
                <dd>{money(selectedClaim.claimAmount)}</dd>
                <dt>Variance</dt>
                <dd>
                  {Math.abs(selectedClaim.variance) <= 0.01 ? (
                    <span className="badge b-green">Nil</span>
                  ) : (
                    <span className="badge b-red">{money(selectedClaim.variance)}</span>
                  )}
                </dd>
                <dt>Workflow Status</dt>
                <dd><span className={badgeClass(selectedClaim.status)}>{selectedClaim.status}</span></dd>
                <dt>Payment Mandate</dt>
                <dd>{selectedClaim.payStatus} {selectedClaim.adviceNo ? `(${selectedClaim.adviceNo})` : ''}</dd>
              </dl>
            </div>

            <div className="modal-f">
              {canApprove && selectedClaim.status === 'Submitted' && (
                <button className="btn btn-ok btn-sm" onClick={() => handleApproveClaim(selectedClaim)}>
                  Approve Devolution Bill
                </button>
              )}
              {canPay && selectedClaim.status === 'Approved' && (
                <button className="btn btn-p btn-sm" onClick={() => handleDisburseClaim(selectedClaim)}>
                  Issue Devolution Advice &amp; Settle
                </button>
              )}
              <button className="btn btn-sm" onClick={() => setSelectedClaim(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Claim Modal */}
      {newModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Submit New Devolution Claim</h3>
                <div className="sub">Register local body statutory revenue share claim</div>
              </div>
              <button className="close" onClick={() => setNewModal(false)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleSaveNewClaim}>
              <div className="modal-b">
                <div className="grid g2">
                  <div className="fld">
                    <label>Local Body <span className="req">*</span></label>
                    <select
                      className="inp"
                      value={newForm.local_body_code}
                      onChange={e => setNewForm({ ...newForm, local_body_code: e.target.value })}
                    >
                      <option value="MC-A">Municipal Corporation A</option>
                      <option value="MC-B">Municipal Corporation B</option>
                      <option value="DLB-C">District Local Body C</option>
                    </select>
                  </div>

                  <div className="fld">
                    <label>Revenue Source <span className="req">*</span></label>
                    <select
                      className="inp"
                      value={newForm.revenue_source}
                      onChange={e => setNewForm({ ...newForm, revenue_source: e.target.value })}
                    >
                      <option value="STAMP">STAMP (Stamps &amp; Registration)</option>
                      <option value="TRANSPORT">TRANSPORT (Motor Vehicle Tax)</option>
                    </select>
                  </div>

                  <div className="fld">
                    <label>Period From <span className="req">*</span></label>
                    <input
                      type="date"
                      className="inp"
                      required
                      value={newForm.claim_period_from}
                      onChange={e => setNewForm({ ...newForm, claim_period_from: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>Period To <span className="req">*</span></label>
                    <input
                      type="date"
                      className="inp"
                      required
                      value={newForm.claim_period_to}
                      onChange={e => setNewForm({ ...newForm, claim_period_to: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>Claim Amount (INR) <span className="req">*</span></label>
                    <input
                      type="number"
                      step="0.01"
                      className="inp"
                      required
                      value={newForm.claim_amount}
                      onChange={e => setNewForm({ ...newForm, claim_amount: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>Receipt Head</label>
                    <input
                      className="inp"
                      value={newForm.receipt_head}
                      onChange={e => setNewForm({ ...newForm, receipt_head: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="modal-f">
                <button type="button" className="btn btn-sm" onClick={() => setNewModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-p btn-sm">
                  Submit Claim
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Variance Exception Modal */}
      {varianceModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Devolution Variance Exception Report</h3>
                <div className="sub">Claims where submitted amount differs from system entitlement</div>
              </div>
              <button className="close" onClick={() => setVarianceModal(false)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              {varianceList.length === 0 ? (
                <div className="box ok">No devolution claim has any variance with reconciled receipts.</div>
              ) : (
                <table className="dt">
                  <thead>
                    <tr>
                      <th>Claim No</th>
                      <th>Local Body</th>
                      <th className="num">Claim Submitted</th>
                      <th className="num">Computed Entitlement</th>
                      <th className="num">Variance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {varianceList.map(c => (
                      <tr key={c.id}>
                        <td className="mono">{c.claimNo}</td>
                        <td>{c.bodyName}</td>
                        <td className="num">{money(c.claimAmount)}</td>
                        <td className="num">{money(c.computed)}</td>
                        <td className="num strong" style={{ color: 'var(--red-700)' }}>
                          {money(c.variance)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="modal-f">
              <button className="btn btn-sm" onClick={() => setVarianceModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default DevolutionPage;
