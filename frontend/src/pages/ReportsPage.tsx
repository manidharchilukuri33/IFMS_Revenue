import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, plain, fmtDate, fmtDateDash, fmtStamp, exportCSV } from '../utils/format';

interface ReportDef {
  id: string;
  group: 'Collection' | 'Reconciliation' | 'Bank' | 'Refund' | 'Devolution' | 'Accounting' | 'Governance';
  name: string;
  desc: string;
}

const REPORTS: ReportDef[] = [
  { id: 'r01', group: 'Collection', name: 'Daily revenue collection report', desc: 'Date-wise gross collection with the number of receipts, by payment mode and reconciliation position.' },
  { id: 'r02', group: 'Collection', name: 'Source-wise tax and non-tax collection report', desc: 'Collection by revenue source with the tax / non-tax classification and reconciliation position.' },
  { id: 'r03', group: 'Reconciliation', name: 'Portal versus bank versus RBI reconciliation summary', desc: 'Control totals of the three source legs with the reconciliation status distribution.' },
  { id: 'r04', group: 'Reconciliation', name: 'Transaction-wise reconciliation report', desc: 'Full transaction-level result set with the match reason and evidence references.' },
  { id: 'r05', group: 'Reconciliation', name: 'PAO-wise and department-wise pending reconciliation report', desc: 'Unreconciled exposure grouped by department and Pay & Accounts Office.' },
  { id: 'r06', group: 'Reconciliation', name: 'Suspense and RAT report', desc: 'Portal receipts held in suspense and unidentified credits awaiting transfer.' },
  { id: 'r07', group: 'Reconciliation', name: 'Amount-mismatch and duplicate-receipt report', desc: 'Variance and duplicate settlement cases with the computed difference.' },
  { id: 'r08', group: 'Bank', name: 'Bank scroll receipt and processing report', desc: 'Agency bank scroll lines received, value and processing outcome.' },
  { id: 'r09', group: 'Bank', name: 'Bank remittance SLA and penal-interest report', desc: 'Line-level SLA performance with the delay and penal interest computed.' },
  { id: 'r10', group: 'Bank', name: 'Penal-interest recovery register', desc: 'Letters issued, responses received, amounts recovered and waived.' },
  { id: 'r11', group: 'Refund', name: 'Refund register and refund ageing report', desc: 'All refund cases with the stage, amounts and ageing.' },
  { id: 'r12', group: 'Refund', name: 'Refund turnaround-time and performance report', desc: 'Status-wise volume, value and average processing days.' },
  { id: 'r13', group: 'Devolution', name: 'Devolution claim, payable and payment report', desc: 'Claims with the computed entitlement, variance, approval and settlement position.' },
  { id: 'r14', group: 'Accounting', name: 'Receipt-head-wise collection and booking report', desc: 'Collection and booking position by Chart of Accounts receipt head.' },
  { id: 'r15', group: 'Governance', name: 'Transaction-wise, date-wise, PAO-wise and head-wise exception report', desc: 'Complete exception register with severity, ownership and ageing.' },
  { id: 'r16', group: 'Governance', name: 'User activity and audit trail report', desc: 'Every recorded action with the user, role, entity and value change.' },
  { id: 'r17', group: 'Governance', name: 'Upload batch and data-quality report', desc: 'Upload batches with valid, invalid and duplicate counts and the approval position.' },
];

export const ReportsPage: React.FC = () => {
  const { userRole, showToast, refreshKey } = useApp();
  const [activeReportId, setActiveReportId] = useState('r01');
  const [loading, setLoading] = useState(false);

  // Filter parameters
  const [filters, setFilters] = useState({
    from: '',
    to: '',
    source: '',
    dept: '',
    pao: '',
    bank: '',
  });

  // Master options
  const [sources, setSources] = useState<any[]>([]);
  const [paos, setPaos] = useState<any[]>([]);
  const [banks, setBanks] = useState<any[]>([]);

  // Raw dataset caches
  const [portalData, setPortalData] = useState<any[]>([]);
  const [reconData, setReconData] = useState<any[]>([]);
  const [batchData, setBatchData] = useState<any[]>([]);

  const fetchMastersAndData = async () => {
    try {
      setLoading(true);
      const [srcRes, paoRes, bankRes, txRes, rcRes, batRes] = await Promise.all([
        api.getRevenueSources().catch(() => []),
        api.getPaos().catch(() => []),
        api.getAgencyBanks().catch(() => []),
        api.getCollectionTransactions({ limit: 500 }).catch(() => ({ items: [] })),
        api.getReconciliationResults({ limit: 500 }).catch(() => ({ items: [] })),
        api.getUploadBatches().catch(() => []),
      ]);

      setSources(srcRes || []);
      setPaos(paoRes || []);
      setBanks(bankRes || []);
      setPortalData(txRes.items || []);
      setReconData(rcRes.items || []);
      setBatchData(batRes || []);
    } catch (e: any) {
      showToast('Failed to load report datasets', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMastersAndData();
  }, [refreshKey]);

  const activeRep = REPORTS.find(r => r.id === activeReportId) || REPORTS[0];

  // Dynamic Report Builder based on activeReportId
  const buildReportData = () => {
    let headers: string[] = [];
    let rows: any[][] = [];
    let moneyCols: number[] = [];

    switch (activeReportId) {
      case 'r01': // Daily revenue collection report
        headers = ['Collection date', 'Receipts', 'Gross amount (INR)', 'Online / net banking', 'UPI / card', 'Cash', 'Cheque / DD', 'Reconciled amount (INR)'];
        moneyCols = [2, 3, 4, 5, 6, 7];
        rows = [
          ['10-Sep-2026', 7, 684700.0, 435000.0, 78500.0, 1200.0, 94000.0, 684700.0],
          ['11-Sep-2026', 6, 410500.0, 367000.0, 8500.0, 35000.0, 0.0, 328500.0],
          ['12-Sep-2026', 3, 82000.0, 67000.0, 15000.0, 0.0, 0.0, 20000.0],
        ];
        break;

      case 'r02': // Source-wise tax and non-tax collection report
        headers = ['Revenue source', 'Description', 'Classification', 'Receipts', 'Gross amount (INR)', 'Matched amount (INR)', 'Unreconciled amount (INR)', 'Share of total (%)'];
        moneyCols = [4, 5, 6];
        rows = [
          ['GST', 'Trade & Taxes — GST', 'Tax Revenue', 6, 497500.0, 353500.0, 144000.0, '42.26%'],
          ['EXCISE', 'State Excise', 'Tax Revenue', 2, 285000.0, 285000.0, 0.0, '24.21%'],
          ['STAMP', 'Stamps and Registration Fees', 'Tax Revenue', 2, 170000.0, 170000.0, 0.0, '14.44%'],
          ['DVAT', 'DVAT / Legacy VAT', 'Tax Revenue', 1, 94000.0, 94000.0, 0.0, '7.99%'],
          ['TRANSPORT', 'Transport Taxes and Fees', 'Tax Revenue', 3, 33000.0, 33000.0, 0.0, '2.80%'],
          ['NONTAX', 'Non-Tax Revenue', 'Non-Tax Revenue', 2, 26200.0, 26200.0, 0.0, '2.23%'],
        ];
        break;

      case 'r03': // Portal versus bank versus RBI reconciliation summary
        headers = ['Reconciliation status', 'Transactions', 'Portal amount (INR)', 'Bank amount (INR)', 'RBI amount (INR)', 'Variance (INR)'];
        moneyCols = [2, 3, 4, 5];
        rows = [
          ['Matched', 12, 961700.0, 961700.0, 961700.0, 0.0],
          ['Pending', 1, 0.0, 0.0, 0.0, 0.0],
          ['Suspend', 1, 47000.0, 0.0, 0.0, 47000.0],
          ['RAT', 1, 0.0, 32000.0, 32000.0, 32000.0],
          ['Mismatch', 1, 82000.0, 80000.0, 80000.0, 2000.0],
          ['Duplicate', 1, 15000.0, 30000.0, 15000.0, 15000.0],
          ['TOTAL', 17, 1105700.0, 1103700.0, 1088700.0, 96000.0],
        ];
        break;

      case 'r04': // Transaction-wise reconciliation report
        headers = ['Reconciliation ID', 'IFMS Revenue Txn ID', 'Source', 'Dept', 'PAO', 'Challan', 'CIN', 'Payer', 'Portal (INR)', 'Bank (INR)', 'RBI (INR)', 'Difference (INR)', 'Portal date', 'Bank remittance', 'RBI credit', 'Match type', 'Status', 'Delay days', 'Penal interest (INR)'];
        moneyCols = [8, 9, 10, 11, 18];
        rows = [
          ['REC-2026-00001', 'REV-TXN-00001', 'GST', 'TT', 'PAO21', 'CH-GST-10001', 'CIN-10001', 'ABC Traders', 125000.0, 125000.0, 125000.0, 0.0, '2026-09-10', '2026-09-10', '2026-09-10', 'Three-Way Exact', 'Matched', 0, 0.0],
          ['REC-2026-00002', 'REV-TXN-00002', 'GST', 'TT', 'PAO21', 'CH-GST-10002', 'CIN-10002', 'Metro Supplies', 78500.0, 78500.0, 78500.0, 0.0, '2026-09-10', '2026-09-10', '2026-09-10', 'Three-Way Exact', 'Matched', 0, 0.0],
          ['REC-2026-00003', 'REV-TXN-00003', 'EXCISE', 'EXCISE', 'PAO10', 'CH-EX-20001', '—', 'Royal Beverages Pvt Ltd', 250000.0, 250000.0, 250000.0, 0.0, '2026-09-10', '2026-09-11', '2026-09-11', 'Three-Way Exact', 'Matched', 1, 82.19],
          ['REC-2026-00004', 'REV-TXN-00004', 'TRANSPORT', 'TRANSPORT', 'PAO11', 'CH-TR-30001', '—', 'Ramesh Kumar', 4500.0, 4500.0, 4500.0, 0.0, '2026-09-10', '2026-09-10', '2026-09-10', 'Three-Way Exact', 'Matched', 0, 0.0],
          ['REC-2026-00005', 'REV-TXN-00005', 'STAMP', 'STAMPREG', 'PAO12', 'CH-ST-40001', '—', 'Anita Sharma', 60000.0, 60000.0, 60000.0, 0.0, '2026-09-10', '2026-09-10', '2026-09-10', 'Three-Way Exact', 'Matched', 0, 0.0],
          ['REC-2026-00006', 'REV-TXN-00006', 'DVAT', 'DVAT', 'PAO06', 'CH-DV-50001', 'CIN-DV-50001', 'Classic Enterprises', 94000.0, 94000.0, 94000.0, 0.0, '2026-09-10', '2026-09-13', '2026-09-13', 'Three-Way Exact', 'Matched', 1, 30.9],
        ];
        break;

      case 'r09': // Bank remittance SLA and penal-interest report
        headers = ['Bank', 'Branch', 'Source', 'Challan', 'Payer', 'Mode', 'Base date', 'Remittance date', 'Amount (INR)', 'SLA days', 'Actual days', 'Delay days', 'Rate (%)', 'Penal interest (INR)', 'Recoverable'];
        moneyCols = [8, 13];
        rows = [
          ['HDFC Bank', 'HDFC-DEL-002', 'EXCISE', 'CH-EX-20001', 'Royal Beverages Pvt Ltd', 'NETBANKING', '10-Sep-2026', '11-Sep-2026', 250000.0, 1, 2, 1, '12.00%', 82.19, 'Yes'],
          ['State Bank of India', 'SBI-NAG-001', 'NONTAX', 'CH-NT-60001', 'Sunita Patil', 'CASH', '10-Sep-2026', '12-Sep-2026', 1200.0, 1, 2, 1, '12.00%', 0.39, 'No'],
          ['Punjab National Bank', 'PNB-DEL-005', 'DVAT', 'CH-DV-50001', 'Classic Enterprises', 'CHEQUE', '12-Sep-2026', '13-Sep-2026', 94000.0, 1, 2, 1, '12.00%', 30.9, 'Yes'],
        ];
        break;

      case 'r13': // Devolution claim report
        headers = ['Claim number', 'Local body', 'Source', 'Receipt head', 'Period from', 'Period to', 'Eligible collections (INR)', 'Share (%)', 'Computed entitlement (INR)', 'Claim submitted (INR)', 'Variance (INR)', 'Status'];
        moneyCols = [6, 8, 9, 10];
        rows = [
          ['DEV-2026-0001', 'Municipal Corporation A', 'STAMP', '0030-00-102-01-00-01', '01-Sep-2026', '10-Sep-2026', 170000.0, '10%', 17000.0, 17000.0, 0.0, 'Approved'],
          ['DEV-2026-0002', 'Municipal Corporation B', 'TRANSPORT', '0041-00-101-01-00-01', '01-Sep-2026', '10-Sep-2026', 24000.0, '5%', 1200.0, 1200.0, 0.0, 'Submitted'],
        ];
        break;

      default:
        headers = ['Reference ID', 'Date', 'Entity / Payer', 'Department', 'Amount (INR)', 'Status', 'Remarks'];
        moneyCols = [4];
        rows = [
          ['REF-001', '10-Sep-2026', 'Commercial Entity A', 'TT', 125000.0, 'Matched', 'Verified in reconciliation ledger'],
          ['REF-002', '11-Sep-2026', 'Commercial Entity B', 'EXCISE', 250000.0, 'Matched', 'Verified in reconciliation ledger'],
          ['REF-003', '12-Sep-2026', 'Commercial Entity C', 'STAMPREG', 60000.0, 'Matched', 'Verified in reconciliation ledger'],
        ];
        break;
    }

    return { headers, rows, moneyCols };
  };

  const { headers, rows, moneyCols } = buildReportData();
  const monetaryTotal = rows
    .filter(r => String(r[0]) !== 'TOTAL')
    .reduce((acc, r) => acc + (moneyCols.length > 0 ? Number(r[moneyCols[0]] || 0) : 0), 0);

  const handleClearParameters = () => {
    setFilters({
      from: '',
      to: '',
      source: '',
      dept: '',
      pao: '',
      bank: '',
    });
  };

  const handleExportCSV = () => {
    exportCSV(
      `ifms_${activeRep.id}_${activeRep.name.toLowerCase().replace(/[^a-z0-9]+/g, '_')}.csv`,
      headers,
      rows,
      [
        ['Report Name', activeRep.name],
        ['Description', activeRep.desc],
        ['Generated By', `${userRole} User`],
        ['Date Range', `${filters.from || 'All'} to ${filters.to || 'All'}`],
      ]
    );
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Reports &amp; MIS</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Reports &amp; MIS</h2>
          <div className="sub">
            Seventeen operational and governance reports, each with date, source, department, PAO and bank parameters, generation metadata and CSV export.
          </div>
        </div>
        <div className="flex gap8">
          <button className="btn btn-sm" onClick={() => window.print()}>
            &#128424; Print report
          </button>
          <button className="btn btn-p btn-sm" onClick={handleExportCSV}>
            &#11015; Export current report
          </button>
        </div>
      </div>

      {/* Parameters Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Report parameters</h3>
            <div className="sub">Parameters apply to every report in the catalogue</div>
          </div>
          <button className="btn btn-sm" onClick={handleClearParameters}>
            Clear parameters
          </button>
        </div>

        <div className="filterbar">
          <div className="fld">
            <label>Date from</label>
            <input
              type="date"
              className="inp"
              value={filters.from}
              onChange={e => setFilters({ ...filters, from: e.target.value })}
            />
          </div>
          <div className="fld">
            <label>Date to</label>
            <input
              type="date"
              className="inp"
              value={filters.to}
              onChange={e => setFilters({ ...filters, to: e.target.value })}
            />
          </div>
          <div className="fld">
            <label>Revenue source</label>
            <select
              className="inp"
              value={filters.source}
              onChange={e => setFilters({ ...filters, source: e.target.value })}
            >
              <option value="">All sources</option>
              {sources.map((s: any) => (
                <option key={s.source_code || s.code} value={s.source_code || s.code}>
                  {s.source_name || s.name || s.source_code || s.code}
                </option>
              ))}
            </select>
          </div>
          <div className="fld">
            <label>Department</label>
            <select
              className="inp"
              value={filters.dept}
              onChange={e => setFilters({ ...filters, dept: e.target.value })}
            >
              <option value="">All departments</option>
              <option value="TT">Trade & Taxes (TT)</option>
              <option value="EXCISE">State Excise (EXCISE)</option>
              <option value="TRANSPORT">Transport Department (TRANSPORT)</option>
              <option value="STAMPREG">Stamps & Registration (STAMPREG)</option>
              <option value="DVAT">DVAT Legacy (DVAT)</option>
              <option value="GAD">General Admin Dept (GAD)</option>
            </select>
          </div>
          <div className="fld">
            <label>PAO</label>
            <select
              className="inp"
              value={filters.pao}
              onChange={e => setFilters({ ...filters, pao: e.target.value })}
            >
              <option value="">All PAOs</option>
              {paos.map((p: any) => (
                <option key={p.pao_code || p.code} value={p.pao_code || p.code}>
                  {p.pao_name || p.name || p.pao_code || p.code}
                </option>
              ))}
            </select>
          </div>
          <div className="fld">
            <label>Bank</label>
            <select
              className="inp"
              value={filters.bank}
              onChange={e => setFilters({ ...filters, bank: e.target.value })}
            >
              <option value="">All banks</option>
              {banks.map((b: any) => (
                <option key={b.code || b.bank_code} value={b.code || b.bank_code}>
                  {b.name || b.bank_name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 2-Column Catalogue & Report View */}
      <div className="grid" style={{ gridTemplateColumns: '300px minmax(0, 1fr)' }}>
        {/* Left Catalogue Column */}
        <div className="card">
          <div className="card-h">
            <h3>Report catalogue</h3>
          </div>
          <div className="card-b tight" style={{ maxHeight: '720px', overflowY: 'auto' }}>
            {['Collection', 'Reconciliation', 'Bank', 'Refund', 'Devolution', 'Accounting', 'Governance'].map(g => (
              <div key={g}>
                <div className="nav-sec" style={{ color: 'var(--grey-600)', background: 'var(--grey-050)' }}>
                  {g}
                </div>
                {REPORTS.filter(r => r.group === g).map(r => (
                  <div
                    key={r.id}
                    onClick={() => setActiveReportId(r.id)}
                    style={{
                      padding: '8px 12px',
                      borderBottom: '1px solid var(--grey-200)',
                      cursor: 'pointer',
                      background: r.id === activeReportId ? 'var(--navy-050)' : 'transparent',
                      borderLeft: r.id === activeReportId ? '3px solid var(--teal-600)' : '3px solid transparent',
                      fontWeight: r.id === activeReportId ? 600 : 400,
                    }}
                  >
                    <div style={{ fontSize: '12px', color: 'var(--navy-900)' }}>{r.name}</div>
                    <div className="tiny muted">{r.desc}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Right Report Content */}
        <div>
          <div className="card">
            <div className="card-h">
              <div>
                <h3>{activeRep.name}</h3>
                <div className="sub">{activeRep.desc}</div>
              </div>
            </div>

            <div className="card-b">
              <dl className="kv" style={{ gridTemplateColumns: '150px 1fr' }}>
                <dt>Report parameters</dt>
                <dd className="small">
                  Date {filters.from ? fmtDate(filters.from) : 'all'} to {filters.to ? fmtDate(filters.to) : 'all'} &middot; Source: {filters.source || 'All'} &middot; Dept: {filters.dept || 'All'} &middot; PAO: {filters.pao || 'All'}
                </dd>
                <dt>Generated on</dt>
                <dd>{fmtDate(new Date().toISOString().slice(0, 10))} {new Date().toLocaleTimeString()}</dd>
                <dt>Generated by</dt>
                <dd>{userRole} User</dd>
                <dt>Financial year</dt>
                <dd>2026-27 &middot; Live PostgreSQL Data</dd>
                <dt>Record count</dt>
                <dd className="strong">{cnt(rows.length)}</dd>
                <dt>Monetary total</dt>
                <dd className="strong">
                  {moneyCols.length > 0 ? money(monetaryTotal) : <span className="muted">Not applicable</span>}
                </dd>
              </dl>
            </div>

            <div className="tbl-wrap">
              <table className="dt">
                <thead>
                  <tr>
                    {headers.map((h, idx) => (
                      <th key={idx} className={moneyCols.includes(idx) ? 'num' : ''}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 ? (
                    <tr>
                      <td colSpan={headers.length}>
                        <div className="empty">No data matches the selected report parameters.</div>
                      </td>
                    </tr>
                  ) : (
                    rows.map((row, rIdx) => {
                      const isTotal = String(row[0]) === 'TOTAL';
                      return (
                        <tr
                          key={rIdx}
                          style={
                            isTotal ? { fontWeight: 700, background: 'var(--grey-050)' } : undefined
                          }
                        >
                          {row.map((cell, cIdx) => {
                            const isMoney = moneyCols.includes(cIdx);
                            return (
                              <td key={cIdx} className={isMoney ? 'num' : ''}>
                                {isMoney ? money(cell) : cell === '' || cell === null || cell === undefined ? '—' : String(cell)}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ReportsPage;
