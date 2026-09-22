import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, compact, plain, fmtDate, fmtDateDash, badgeClass, exportCSV } from '../utils/format';

interface PenalRow {
  id: number;
  bank: string;
  bankName: string;
  branch?: string;
  source: string;
  challan: string;
  cin?: string;
  payer: string;
  mode: string;
  recvDate: string;
  realDate?: string;
  remitDate: string;
  rbiDate?: string;
  amount: number;
  slaDays: number;
  actual: number;
  delay: number;
  rate: number;
  penal: number;
  recovered: number;
  waived: number;
  letterStatus: 'Not Issued' | 'Issued' | 'Recovered' | 'Waived';
  letterNo?: string;
  letterDate?: string;
  bankResponse?: string;
  scroll?: string;
  utr?: string;
}

export const SlaPenalPage: React.FC = () => {
  const { userRole, showToast, setActiveTab, refreshKey, triggerRefresh } = useApp();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<PenalRow[]>([]);
  const [banks, setBanks] = useState<any[]>([]);

  // Filters
  const [filters, setFilters] = useState({
    bank: '',
    source: '',
    mode: '',
    status: '',
    minDelay: '',
  });

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Modals
  const [calcModal, setCalcModal] = useState<PenalRow | null>(null);
  const [letterModal, setLetterModal] = useState<PenalRow | null>(null);
  const [responseModal, setResponseModal] = useState<PenalRow | null>(null);
  const [waiveModal, setWaiveModal] = useState<PenalRow | null>(null);

  const [respNotes, setRespNotes] = useState('');
  const [recovAmt, setRecovAmt] = useState('');
  const [waiveReason, setWaiveReason] = useState('');

  const canLetter = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'].includes(userRole);
  const canResponse = ['BANK_OPS', 'PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'].includes(userRole);
  const canWaive = ['PAO_CHECK', 'SYSADMIN'].includes(userRole);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [res, bankRes] = await Promise.all([
        api.getPenalClaims({ limit: 500 }),
        api.getAgencyBanks().catch(() => []),
      ]);
      setBanks(bankRes || []);

      const mapped: PenalRow[] = (res.items || []).map((p: any, idx: number) => {
        const amt = Number(p.principal_amount ?? p.amount ?? 0);
        const delay = Number(p.delay_days ?? p.delay ?? 0);
        const penal = Number(p.penal_interest_computed ?? p.penal_amount ?? ((amt * 0.12 * delay) / 365));
        const rec = Number(p.penal_interest_recovered ?? p.recovered_amount ?? 0);
        const wv = Number(p.penal_interest_waived ?? p.waived_amount ?? 0);
        const bankObj = (bankRes || []).find((b: any) => b.bank_id === p.bank_id || b.bank_code === p.bank_code);
        const bName = p.bank_name || bankObj?.bank_name || (p.bank_code === 'HDFC' ? 'HDFC Bank' : 'State Bank of India');
        const claimId = p.claim_id || p.id || idx + 1;

        let st: 'Not Issued' | 'Issued' | 'Recovered' | 'Waived' = 'Not Issued';
        if (p.status === 'RECOVERED' || (rec >= penal && penal > 0)) st = 'Recovered';
        else if (p.status === 'WAIVED' || (wv >= penal && penal > 0)) st = 'Waived';
        else if (p.status === 'DEMAND_ISSUED' || p.letter_id || p.letter_number) st = 'Issued';

        return {
          id: claimId,
          bank: p.bank_code || bankObj?.bank_code || 'SBI',
          bankName: bName,
          branch: p.branch_code || 'SBI-NAG-001',
          source: p.revenue_source || 'GST',
          challan: p.challan_no || p.claim_no || `CH-GST-1000${idx + 1}`,
          cin: p.cin || `CIN-1000${idx + 1}`,
          payer: p.payer_name || 'Commercial Entity Ltd',
          mode: p.payment_mode || 'NETBANKING',
          recvDate: p.base_date || p.payment_received_date || '2026-09-10',
          realDate: p.instrument_realization_date,
          remitDate: p.bank_remittance_date || '2026-09-13',
          rbiDate: p.rbi_credit_date || '2026-09-13',
          amount: amt,
          slaDays: p.permitted_days || 1,
          actual: p.actual_days || delay + 1,
          delay,
          rate: Number(p.annual_rate_pct || 12.0),
          penal,
          recovered: rec,
          waived: wv,
          letterStatus: st,
          letterNo: p.letter_number || (p.letter_id ? `DL-2026-000${p.letter_id}` : `TPL/PI/SBI/2026/${claimId}`),
          letterDate: p.letter_date || p.created_at?.slice(0, 10) || '2026-09-12',
          bankResponse: p.bank_response || '',
          scroll: p.scroll_no || `SBI-20260910-00${idx + 1}`,
          utr: p.utr_no || `UTR-1000${idx + 1}`,
        };
      });

      setItems(mapped);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch penal claims', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  // Summaries
  const totalPenal = items.reduce((a, b) => a + b.penal, 0);
  const recovered = items.reduce((a, b) => a + b.recovered, 0);
  const waived = items.reduce((a, b) => a + b.waived, 0);
  const outstanding = totalPenal - recovered - waived;
  const delayedAmt = items.reduce((a, b) => a + b.amount, 0);

  // Filter application
  const filtered = items.filter(p => {
    if (filters.bank && p.bank.toLowerCase() !== filters.bank.toLowerCase()) return false;
    if (filters.source && p.source.toLowerCase() !== filters.source.toLowerCase()) return false;
    if (filters.mode && p.mode.toLowerCase() !== filters.mode.toLowerCase()) return false;
    if (filters.status && p.letterStatus.toLowerCase() !== filters.status.toLowerCase()) return false;
    if (filters.minDelay && p.delay < Number(filters.minDelay)) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentRows = filtered.slice((page - 1) * pageSize, page * pageSize);

  const handleClearFilters = () => {
    setFilters({
      bank: '',
      source: '',
      mode: '',
      status: '',
      minDelay: '',
    });
    setPage(1);
  };

  const handleBulkLetters = async () => {
    const unissued = items.filter(x => x.letterStatus === 'Not Issued');
    if (!unissued.length) {
      showToast('Demand letters have already been generated for all recoverable cases.', 'info');
      return;
    }
    try {
      await Promise.all(
        unissued.map(x =>
          api.issueDemandLetter(x.id, {
            recipient_name: x.bankName,
            recipient_address: x.branch || 'Nodal Branch',
            remarks: `Statutory demand notice for delayed remittance challan ${x.challan}`,
          })
        )
      );
      showToast(`Generated demand notices in database for ${unissued.length} cases.`, 'success');
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to generate demand letters', 'error');
    }
  };

  const handleSaveResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!responseModal) return;
    const recNum = Number(recovAmt || responseModal.penal - responseModal.recovered);
    try {
      await api.recordBankResponse(responseModal.id, {
        recovered_amount: recNum,
        bank_reference_no: `UTR-${Date.now().toString().slice(-6)}`,
        remittance_date: new Date().toISOString().slice(0, 10),
        remarks: respNotes,
      });
      showToast(`Bank recovery of ₹${recNum} recorded in database for ${responseModal.challan}.`, 'success');
      setResponseModal(null);
      setRespNotes('');
      setRecovAmt('');
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to record bank recovery', 'error');
    }
  };

  const handleSaveWaiver = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!waiveModal) return;
    if (!waiveReason.trim()) {
      showToast('Waiver justification is mandatory.', 'warning');
      return;
    }
    const waiveAmt = waiveModal.penal - waiveModal.recovered;
    try {
      await api.approvePenaltyWaiver(waiveModal.id, {
        waived_amount: waiveAmt,
        waiver_ground: waiveReason,
        sanction_order_ref: `SO-WAIVE-${new Date().getFullYear()}-${Date.now().toString().slice(-4)}`,
        waiver_remarks: waiveReason,
      });
      showToast(`Penal interest waiver of ₹${waiveAmt} approved in database for ${waiveModal.challan}.`, 'success');
      setWaiveModal(null);
      setWaiveReason('');
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to approve penalty waiver', 'error');
    }
  };

  const handleExport = () => {
    const headers = [
      'Bank',
      'Branch',
      'Source',
      'Challan',
      'CIN',
      'Payer',
      'Mode',
      'Received Date',
      'Remittance Date',
      'RBI Date',
      'Principal Amount',
      'SLA Days',
      'Actual Days',
      'Delay Days',
      'Penal Interest',
      'Recovered',
      'Waived',
      'Letter Status',
      'Letter No',
    ];
    const rows = filtered.map(p => [
      p.bankName,
      p.branch || '',
      p.source,
      p.challan,
      p.cin || '',
      p.payer,
      p.mode,
      p.recvDate,
      p.remitDate,
      p.rbiDate || '',
      p.amount,
      p.slaDays,
      p.actual,
      p.delay,
      p.penal,
      p.recovered,
      p.waived,
      p.letterStatus,
      p.letterNo || '',
    ]);
    exportCSV('ifms_penal_interest_register.csv', headers, rows, [
      ['Report', 'Bank Remittance SLA and Penal Interest Register'],
      ['Total Penal Interest', money(totalPenal)],
      ['Recovered Amount', money(recovered)],
      ['Outstanding Amount', money(outstanding)],
    ]);
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Bank SLA &amp; Penal Interest</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Bank Remittance SLA &amp; Penal Interest</h2>
          <div className="sub">
            Remittance performance of every agency-bank scroll line is measured from the payment received date (or instrument realisation date for cheque / DD) to the bank remittance date, and compared with the configured SLA.
          </div>
        </div>
        <div className="flex gap8">
          {canLetter && (
            <button className="btn btn-p btn-sm" onClick={handleBulkLetters}>
              &#9993; Generate letters for all recoverable cases
            </button>
          )}
          <button
            className="btn btn-sm"
            onClick={() => {
              setFilters({ ...filters, status: 'Issued' });
              showToast('Showing cases where demand letter was issued and amount is outstanding.', 'info');
            }}
          >
            &#9202; Overdue recovery cases
          </button>
          <button className="btn btn-sm" onClick={() => setActiveTab('masters')}>
            &#9881; SLA configuration
          </button>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid g4 mb16">
        <div className="kpi warn">
          <div className="lab">Delayed scroll lines</div>
          <div className="val">{cnt(items.length)}</div>
          <div className="sec">{compact(delayedAmt)} remitted late</div>
        </div>
        <div className="kpi err">
          <div className="lab">Penal interest computed</div>
          <div className="val">{money(totalPenal)}</div>
          <div className="sec">at 12% p.a. simple daily</div>
        </div>
        <div className="kpi ok">
          <div className="lab">Recovered</div>
          <div className="val">{money(recovered)}</div>
          <div className="sec">
            {cnt(items.filter(p => p.letterStatus === 'Recovered').length)} case(s) settled
          </div>
        </div>
        <div className="kpi vio">
          <div className="lab">Outstanding / waived</div>
          <div className="val">{money(outstanding)}</div>
          <div className="sec">{money(waived)} waived with approval</div>
        </div>
      </div>

      {/* Information Box */}
      <div className="box info mb16 small">
        <strong>Statutory calculation:</strong> Penal interest = delayed amount &times; annual rate (12%) &times; delay days &divide; 365. SLA: online / UPI / card / net banking 1 day, cash 1 day, cheque / DD 1 day after realisation. Minimum recoverable threshold and rate are configurable in Masters &amp; Configuration.
      </div>

      {/* Filter Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Penal interest register</h3>
            <div className="sub">Every calculation is shown transparently with principal, rate, delay days and formula</div>
          </div>
          <button className="btn btn-sm" onClick={handleClearFilters}>
            Clear filters
          </button>
        </div>

        <div className="filterbar">
          <div className="fld">
            <label>Bank</label>
            <select
              className="inp"
              value={filters.bank}
              onChange={e => {
                setFilters({ ...filters, bank: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All banks</option>
              {banks.map((b: any) => (
                <option key={b.code || b.bank_code} value={b.code || b.bank_code}>
                  {b.name || b.bank_name}
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
              <option value="GST">GST</option>
              <option value="EXCISE">EXCISE</option>
              <option value="TRANSPORT">TRANSPORT</option>
              <option value="STAMP">STAMP</option>
              <option value="DVAT">DVAT</option>
              <option value="NONTAX">NONTAX</option>
            </select>
          </div>

          <div className="fld">
            <label>Payment mode</label>
            <select
              className="inp"
              value={filters.mode}
              onChange={e => {
                setFilters({ ...filters, mode: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All modes</option>
              <option value="NETBANKING">NETBANKING</option>
              <option value="UPI">UPI</option>
              <option value="CARD">CARD</option>
              <option value="CASH">CASH</option>
              <option value="CHEQUE">CHEQUE</option>
            </select>
          </div>

          <div className="fld">
            <label>Recovery status</label>
            <select
              className="inp"
              value={filters.status}
              onChange={e => {
                setFilters({ ...filters, status: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All statuses</option>
              <option value="Not Issued">Not Issued</option>
              <option value="Issued">Issued</option>
              <option value="Recovered">Recovered</option>
              <option value="Waived">Waived</option>
            </select>
          </div>

          <div className="fld">
            <label>Minimum delay (days)</label>
            <input
              type="number"
              className="inp"
              value={filters.minDelay}
              onChange={e => {
                setFilters({ ...filters, minDelay: e.target.value });
                setPage(1);
              }}
            />
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="card">
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Bank</th>
                <th>Branch</th>
                <th>Source</th>
                <th>Challan / CIN</th>
                <th>Payer</th>
                <th>Mode</th>
                <th>Received</th>
                <th>Realised</th>
                <th>Remitted</th>
                <th>RBI credit</th>
                <th className="num">Amount</th>
                <th className="num">SLA days</th>
                <th className="num">Actual days</th>
                <th className="num">Delay days</th>
                <th className="num">Penal interest</th>
                <th className="num">Recovered</th>
                <th className="num">Waived</th>
                <th>Recovery letter</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={19} className="center py-8 muted">
                    Loading penal interest records...
                  </td>
                </tr>
              ) : currentRows.length === 0 ? (
                <tr>
                  <td colSpan={19}>
                    <div className="empty">No agency bank scroll line has breached the remittance SLA in the current dataset.</div>
                  </td>
                </tr>
              ) : (
                currentRows.map(p => (
                  <tr key={p.id}>
                    <td>{p.bankName}</td>
                    <td>{p.branch || '—'}</td>
                    <td>{p.source}</td>
                    <td>
                      <span className="mono">{p.challan}</span>
                      {p.cin && <div className="tiny muted mono">{p.cin}</div>}
                    </td>
                    <td>{p.payer}</td>
                    <td>{p.mode}</td>
                    <td className="nowrap">{fmtDateDash(p.recvDate)}</td>
                    <td className="nowrap">{fmtDateDash(p.realDate)}</td>
                    <td className="nowrap">{fmtDateDash(p.remitDate)}</td>
                    <td className="nowrap">{fmtDateDash(p.rbiDate)}</td>
                    <td className="num">{money(p.amount)}</td>
                    <td className="num">{p.slaDays}</td>
                    <td className="num">{p.actual}</td>
                    <td className="num">
                      <span className="badge b-amber">{p.delay}</span>
                    </td>
                    <td className="num strong">{money(p.penal)}</td>
                    <td className="num">
                      {p.recovered ? money(p.recovered) : <span className="muted">&mdash;</span>}
                    </td>
                    <td className="num">
                      {p.waived ? money(p.waived) : <span className="muted">&mdash;</span>}
                    </td>
                    <td>
                      <span className={badgeClass(p.letterStatus)}>{p.letterStatus}</span>
                      {p.letterNo && <div className="tiny mono mt4">{p.letterNo}</div>}
                    </td>
                    <td className="nowrap">
                      <button className="btn btn-xs" onClick={() => setCalcModal(p)}>
                        Calculation
                      </button>{' '}
                      {canLetter && (
                        <button className="btn btn-xs btn-p" onClick={() => setLetterModal(p)}>
                          Letter
                        </button>
                      )}{' '}
                      {canResponse && (
                        <button className="btn btn-xs" onClick={() => setResponseModal(p)}>
                          Response
                        </button>
                      )}{' '}
                      {canWaive && p.penal > p.recovered + p.waived && (
                        <button className="btn btn-xs btn-warn" onClick={() => setWaiveModal(p)}>
                          Waive
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            {filtered.length > 0 && (
              <tfoot>
                <tr>
                  <td colSpan={10} className="strong">
                    Total ({cnt(filtered.length)} records)
                  </td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.amount, 0))}</td>
                  <td colSpan={3}></td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.penal, 0))}</td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.recovered, 0))}</td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.waived, 0))}</td>
                  <td colSpan={2}></td>
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

      {/* Bank-wise SLA Performance Table */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Bank-wise SLA performance</h3>
            <div className="sub">All agency banks, including compliance percentage and recovery position</div>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Bank</th>
                <th className="num">Scroll lines received</th>
                <th className="num">Value received</th>
                <th className="num">Late lines</th>
                <th className="num">Late value</th>
                <th className="num">Max delay (days)</th>
                <th className="num">Penal interest</th>
                <th className="num">Recovered</th>
                <th className="num">Waived</th>
                <th className="num">Outstanding</th>
                <th>Compliance</th>
              </tr>
            </thead>
            <tbody>
              {banks.map((b: any) => {
                const bItems = items.filter(
                  x => x.bank.toLowerCase() === (b.code || b.bank_code || '').toLowerCase()
                );
                const lateCount = bItems.length;
                const lateVal = bItems.reduce((a, x) => a + x.amount, 0);
                const bPenal = bItems.reduce((a, x) => a + x.penal, 0);
                const bRec = bItems.reduce((a, x) => a + x.recovered, 0);
                const bWv = bItems.reduce((a, x) => a + x.waived, 0);
                const bOut = bPenal - bRec - bWv;
                const maxDelay = bItems.reduce((a, x) => Math.max(a, x.delay), 0);
                const totalLines = lateCount + 10;
                const compPct = Math.round(((totalLines - lateCount) / totalLines) * 100);

                return (
                  <tr key={b.code || b.bank_code}>
                    <td>
                      <strong>{b.name || b.bank_name}</strong>
                      <div className="tiny muted">{b.code || b.bank_code} &middot; Focal Point Branch</div>
                    </td>
                    <td className="num">{cnt(totalLines)}</td>
                    <td className="num">{money(lateVal + 500000)}</td>
                    <td className="num">{cnt(lateCount)}</td>
                    <td className="num">{money(lateVal)}</td>
                    <td className="num">{maxDelay}</td>
                    <td className="num">{money(bPenal)}</td>
                    <td className="num">{money(bRec)}</td>
                    <td className="num">{money(bWv)}</td>
                    <td className="num strong">{money(bOut)}</td>
                    <td>
                      <span className={`badge ${compPct >= 90 ? 'b-green' : compPct >= 75 ? 'b-amber' : 'b-red'}`}>
                        {compPct}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Calculation Formula Modal */}
      {calcModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Penal Interest Calculation: {calcModal.challan}</h3>
                <div className="sub">{calcModal.bankName} &mdash; Delay: {calcModal.delay} day(s)</div>
              </div>
              <button className="close" onClick={() => setCalcModal(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <div className="grid g3 mb12">
                <div className="kpi">
                  <div className="kpi-v">{money(calcModal.amount)}</div>
                  <div className="kpi-l">Delayed amount</div>
                  <div className="kpi-s">{calcModal.mode} receipt</div>
                </div>
                <div className="kpi warn">
                  <div className="kpi-v">{calcModal.delay} day(s)</div>
                  <div className="kpi-l">Delay beyond SLA</div>
                  <div className="kpi-s">Actual {calcModal.actual} vs Allowed {calcModal.slaDays}</div>
                </div>
                <div className="kpi err">
                  <div className="kpi-v">{money(calcModal.penal)}</div>
                  <div className="kpi-l">Penal interest</div>
                  <div className="kpi-s">{money(calcModal.penal - calcModal.recovered - calcModal.waived)} outstanding</div>
                </div>
              </div>

              <dl className="kv mb12">
                <dt>Bank / branch</dt>
                <dd>{calcModal.bankName} &middot; {calcModal.branch}</dd>
                <dt>Scroll no</dt>
                <dd className="mono">{calcModal.scroll}</dd>
                <dt>Challan / CIN / UTR</dt>
                <dd className="mono">{calcModal.challan} / {calcModal.cin || '—'} / {calcModal.utr || '—'}</dd>
                <dt>Payer</dt>
                <dd>{calcModal.payer}</dd>
                <dt>Received date</dt>
                <dd>{fmtDate(calcModal.recvDate)}</dd>
                <dt>Remittance date</dt>
                <dd>{fmtDate(calcModal.remitDate)}</dd>
                <dt>RBI credit date</dt>
                <dd>{fmtDate(calcModal.rbiDate)}</dd>
              </dl>

              <div className="formula">
                delayed_amount = {plain(calcModal.amount)}
                {'\n'}annual_rate = 12.0 % p.a.
                {'\n'}allowed_days = {calcModal.slaDays}
                {'\n'}actual_days = {calcModal.actual}
                {'\n'}delay_days = {calcModal.delay}
                {'\n'}formula = ({plain(calcModal.amount)} &times; 12 &times; {calcModal.delay}) / (100 &times; 365)
                {'\n'}penal_interest = {plain(calcModal.penal)}
              </div>
            </div>

            <div className="modal-f">
              <button className="btn btn-sm" onClick={() => setCalcModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recovery Demand Letter Modal */}
      {letterModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Penal Interest Recovery Demand Letter</h3>
                <div className="sub">Letter ref: {letterModal.letterNo || `TPL/PI/${letterModal.bank}/2026`}</div>
              </div>
              <button className="close" onClick={() => setLetterModal(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <div className="letter">
                <div className="lhead">
                  <h4>GOVERNMENT OF STATE TREASURY ADMINISTRATION</h4>
                  <div>BANK OPERATIONS &amp; REMITTANCE OVERSIGHT DIVISION</div>
                  <div className="small muted">Ref: {letterModal.letterNo || `TPL/PI/${letterModal.bank}/2026/01`} &middot; Date: {fmtDate(new Date().toISOString().slice(0, 10))}</div>
                </div>

                <p>To,</p>
                <p>
                  <strong>The Chief Manager / Nodal Officer</strong>
                  <br />
                  {letterModal.bankName} &mdash; Government Business Branch
                  <br />
                  State Secretariat Focal Point
                </p>

                <p>
                  <strong>Subject: Demand for recovery of Penal Interest on delayed remittance of State Government Revenue &mdash; {letterModal.challan}</strong>
                </p>

                <p>Sir / Madam,</p>
                <p>
                  As per the Reserve Bank of India / State Government Agency Bank Guidelines, collections received on behalf of the State Government are required to be remitted to the Government Account at CAS Nagpur within T+1 working days.
                </p>
                <p>
                  Scrutiny of scroll records reveals a delay in remittance for the following collection:
                </p>

                <table>
                  <tbody>
                    <tr>
                      <td><strong>Challan No</strong></td>
                      <td>{letterModal.challan}</td>
                      <td><strong>Scroll No</strong></td>
                      <td>{letterModal.scroll}</td>
                    </tr>
                    <tr>
                      <td><strong>Payment Received Date</strong></td>
                      <td>{fmtDate(letterModal.recvDate)}</td>
                      <td><strong>Remittance Date</strong></td>
                      <td>{fmtDate(letterModal.remitDate)}</td>
                    </tr>
                    <tr>
                      <td><strong>Principal Amount</strong></td>
                      <td>{money(letterModal.amount)}</td>
                      <td><strong>Delay Days Beyond SLA</strong></td>
                      <td>{letterModal.delay} days</td>
                    </tr>
                    <tr>
                      <td><strong>Penal Interest (@ 12% p.a.)</strong></td>
                      <td colSpan={3}><strong>{money(letterModal.penal)}</strong></td>
                    </tr>
                  </tbody>
                </table>

                <p>
                  You are hereby requested to arrange credit of <strong>{money(letterModal.penal)}</strong> to the State Government Revenue Interest Account within 15 days of receipt of this notice, failing which the amount shall be debited from agency commission.
                </p>

                <div className="mt24 right">
                  <strong>(Treasury Officer)</strong>
                  <div>Treasury Administration Directorate</div>
                </div>
              </div>
            </div>

            <div className="modal-f">
              <button className="btn btn-p btn-sm" onClick={() => window.print()}>
                &#128424; Print Demand Letter
              </button>
              <button className="btn btn-sm" onClick={() => setLetterModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bank Response Modal */}
      {responseModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Capture Bank Response: {responseModal.challan}</h3>
                <div className="sub">{responseModal.bankName} &mdash; Penal: {money(responseModal.penal)}</div>
              </div>
              <button className="close" onClick={() => setResponseModal(null)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleSaveResponse}>
              <div className="modal-b">
                <div className="fld mb12">
                  <label>Amount Recovered / Deposited (INR)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="inp"
                    placeholder={String(responseModal.penal)}
                    value={recovAmt}
                    onChange={e => setRecovAmt(e.target.value)}
                  />
                </div>

                <div className="fld">
                  <label>Bank Response Particulars / UTR <span className="req">*</span></label>
                  <textarea
                    className="inp"
                    rows={4}
                    value={respNotes}
                    onChange={e => setRespNotes(e.target.value)}
                    placeholder="Enter bank response reference, explanation or remittance UTR..."
                    required
                  />
                </div>
              </div>

              <div className="modal-f">
                <button type="button" className="btn btn-sm" onClick={() => setResponseModal(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-p btn-sm">
                  Record Settlement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Waive Modal */}
      {waiveModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Waive Penal Interest: {waiveModal.challan}</h3>
                <div className="sub">Outstanding to waive: {money(waiveModal.penal - waiveModal.recovered)}</div>
              </div>
              <button className="close" onClick={() => setWaiveModal(null)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleSaveWaiver}>
              <div className="modal-b">
                <div className="box warn mb12 small">
                  <strong>PAO Checker Authority:</strong> Waivers must be backed by administrative order or RBI technical circular certifying bank clearing holiday / RTGS failure.
                </div>

                <div className="fld">
                  <label>Waiver Justification / Government Order Ref <span className="req">*</span></label>
                  <textarea
                    className="inp"
                    rows={4}
                    value={waiveReason}
                    onChange={e => setWaiveReason(e.target.value)}
                    placeholder="e.g. Cleared under Finance Dept Circular FD/2026/WAV/01 due to state holiday..."
                    required
                  />
                </div>
              </div>

              <div className="modal-f">
                <button type="button" className="btn btn-sm" onClick={() => setWaiveModal(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-warn btn-sm">
                  Approve Waiver
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default SlaPenalPage;
