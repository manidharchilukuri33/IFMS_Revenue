import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { ReportMetadata, ReportDataset } from '../types';
import { money, cnt, fmtDate, exportCSV } from '../utils/format';

const DEFAULT_REPORTS: ReportMetadata[] = [
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
  const [catalogue, setCatalogue] = useState<ReportMetadata[]>(DEFAULT_REPORTS);
  const [activeReportId, setActiveReportId] = useState('r01');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState<ReportDataset | null>(null);
  const [generatedAt, setGeneratedAt] = useState<string>('');

  // Catalogue Search & Group Pill Filter
  const [searchCat, setSearchCat] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string>('ALL');

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

  // 1. Fetch Masters & Catalogue
  useEffect(() => {
    const fetchMasters = async () => {
      try {
        const [catRes, srcRes, paoRes, bankRes] = await Promise.all([
          api.getReportCatalogue().catch(() => DEFAULT_REPORTS),
          api.getRevenueSources().catch(() => []),
          api.getPaos().catch(() => []),
          api.getAgencyBanks().catch(() => []),
        ]);

        if (Array.isArray(catRes) && catRes.length > 0) {
          setCatalogue(catRes);
        }
        setSources(srcRes || []);
        setPaos(paoRes || []);
        setBanks(bankRes || []);
      } catch (err: any) {
        console.error('Failed to load report masters:', err);
      }
    };
    fetchMasters();
  }, [refreshKey]);

  // 2. Fetch Live Dynamic Report Data whenever report selection or filters change
  const fetchReport = async () => {
    try {
      setLoading(true);
      const res = await api.getReportData(activeReportId, {
        from_date: filters.from || undefined,
        to_date: filters.to || undefined,
        source_id: filters.source || undefined,
        bank_id: filters.bank || undefined,
        pao_code: filters.pao || undefined,
        dept_code: filters.dept || undefined,
      });
      setReportData(res);
      setGeneratedAt(new Date().toLocaleString());
    } catch (err: any) {
      showToast(err.message || 'Failed to generate report from database', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [activeReportId, filters, refreshKey]);

  const activeRep = catalogue.find(r => r.id === activeReportId) || catalogue[0] || DEFAULT_REPORTS[0];

  const headers = reportData?.headers || [];
  const rows = reportData?.rows || [];
  const moneyCols = reportData?.money_columns || [];

  // Calculate Monetary Total dynamically across data rows
  const monetaryTotal = rows
    .filter(r => String(r[0]) !== 'TOTAL')
    .reduce((acc, r) => {
      if (moneyCols.length > 0) {
        const val = Number(r[moneyCols[0]] || 0);
        return acc + (isNaN(val) ? 0 : val);
      }
      return acc;
    }, 0);

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
    if (!reportData) return;
    exportCSV(
      `ifms_${activeRep.id}_${activeRep.name.toLowerCase().replace(/[^a-z0-9]+/g, '_')}.csv`,
      headers,
      rows,
      [
        ['Report Name', activeRep.name],
        ['Description', activeRep.desc],
        ['Generated By', `${userRole} User`],
        ['Generated On', generatedAt || new Date().toISOString()],
        ['Date Range', `${filters.from || 'All'} to ${filters.to || 'All'}`],
        ['Source Filter', filters.source || 'All'],
        ['PAO Filter', filters.pao || 'All'],
        ['Bank Filter', filters.bank || 'All'],
      ]
    );
  };

  const reportGroups = Array.from(new Set(catalogue.map(r => r.group)));

  // Filter catalogue based on search and selected group pill
  const filteredCatalogue = catalogue.filter(r => {
    const matchesGroup = selectedGroup === 'ALL' || r.group.toLowerCase() === selectedGroup.toLowerCase();
    const query = searchCat.toLowerCase().trim();
    const matchesQuery =
      !query ||
      r.id.toLowerCase().includes(query) ||
      r.name.toLowerCase().includes(query) ||
      r.desc.toLowerCase().includes(query) ||
      r.group.toLowerCase().includes(query);
    return matchesGroup && matchesQuery;
  });

  const filteredGroups = Array.from(new Set(filteredCatalogue.map(r => r.group)));

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
        <div className="btn-group no-print flex gap8">
          <button className="btn btn-sm" onClick={() => window.print()}>
            🖨️ Print report
          </button>
          <button className="btn btn-p btn-sm" onClick={handleExportCSV} disabled={rows.length === 0}>
            ⬇️ Export current report
          </button>
        </div>
      </div>

      {/* Parameters Filter Toolbar Card */}
      <div className="card mb12">
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
              <option value="TT">Trade &amp; Taxes (TT)</option>
              <option value="EXCISE">State Excise (EXCISE)</option>
              <option value="TRANSPORT">Transport Department (TRANSPORT)</option>
              <option value="STAMPREG">Stamps &amp; Registration (STAMPREG)</option>
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

      {/* 2-Column Master-Detail: Catalogue Sidebar (Left) vs Interactive Report Display (Right) */}
      <div className="grid" style={{ gridTemplateColumns: '300px minmax(0, 1fr)' }}>
        
        {/* Left: Report Catalogue */}
        <div className="card">
          <div className="card-h">
            <h3>Report catalogue</h3>
          </div>

          {/* Quick Search Input (interactive only, hidden on print) */}
          <div className="catalogue-search no-print" style={{ padding: '8px 12px', borderBottom: '1px solid var(--grey-200)' }}>
            <input
              type="text"
              className="inp"
              placeholder="Search reports (e.g. R01, Bank, Tax)..."
              value={searchCat}
              onChange={e => setSearchCat(e.target.value)}
            />
          </div>

          {/* Category Group Filter Pills (interactive only, hidden on print) */}
          <div className="catalogue-filter-pills no-print" style={{ padding: '6px 12px', display: 'flex', flexWrap: 'wrap', gap: '4px', borderBottom: '1px solid var(--grey-200)' }}>
            <button
              className={`cat-pill ${selectedGroup === 'ALL' ? 'active' : ''}`}
              onClick={() => setSelectedGroup('ALL')}
            >
              All ({catalogue.length})
            </button>
            {reportGroups.map(g => {
              const count = catalogue.filter(r => r.group === g).length;
              return (
                <button
                  key={g}
                  className={`cat-pill ${selectedGroup === g ? 'active' : ''}`}
                  onClick={() => setSelectedGroup(g)}
                >
                  {g} ({count})
                </button>
              );
            })}
          </div>

          {/* Catalogue List */}
          <div className="card-b tight catalogue-list">
            {filteredCatalogue.length === 0 ? (
              <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--grey-500)', fontSize: '12px' }}>
                No reports match &ldquo;{searchCat}&rdquo;
              </div>
            ) : (
              filteredGroups.map(g => (
                <div key={g}>
                  <div
                    className="nav-sec"
                    style={{
                      color: 'var(--grey-600)',
                      background: 'var(--grey-050)',
                      padding: '6px 12px',
                      fontSize: '10px',
                      fontWeight: 700,
                      letterSpacing: '0.6px',
                      textTransform: 'uppercase',
                      borderBottom: '1px solid var(--grey-200)',
                    }}
                  >
                    {g}
                  </div>
                  {filteredCatalogue
                    .filter(r => r.group === g)
                    .map(r => {
                      const isActive = r.id === activeReportId;
                      return (
                        <div
                          key={r.id}
                          style={{
                            padding: '7px 12px',
                            borderBottom: '1px solid var(--grey-200)',
                            cursor: 'pointer',
                            background: isActive ? 'var(--navy-050)' : '#fff',
                            borderLeft: isActive ? '3px solid var(--teal-600)' : '3px solid transparent',
                            fontWeight: isActive ? 600 : 'normal',
                          }}
                          onClick={() => setActiveReportId(r.id)}
                        >
                          <div style={{ fontSize: '12px', color: isActive ? 'var(--navy-900)' : 'inherit', fontWeight: isActive ? 700 : 600 }}>
                            {r.name}
                          </div>
                          <div className="tiny muted" style={{ fontSize: '11px', color: 'var(--grey-600)', marginTop: '2px' }}>
                            {r.desc}
                          </div>
                        </div>
                      );
                    })}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Dedicated Report Viewer Panel */}
        <div>
          <div className="card">
            <div className="card-h">
              <div>
                <h3>{reportData?.report_name || activeRep.name}</h3>
                <div className="sub">{reportData?.description || activeRep.desc}</div>
              </div>
              <div className="no-print flex items-center gap8">
                {loading && <span className="badge b-amber">Querying Database...</span>}
                <button className="btn btn-sm" onClick={fetchReport} title="Refresh report from live database">
                  🔄 Refresh
                </button>
              </div>
            </div>

            <div className="card-b">
              <dl className="kv" style={{ gridTemplateColumns: '150px 1fr' }}>
                <dt>Report parameters</dt>
                <dd className="small">
                  {[
                    'Date ' + (filters.from ? fmtDate(filters.from) : 'all') + ' to ' + (filters.to ? fmtDate(filters.to) : 'all'),
                    'Source: ' + (filters.source || 'All'),
                    'Department: ' + (filters.dept || 'All'),
                    'PAO: ' + (filters.pao || 'All'),
                    'Bank: ' + (filters.bank || 'All'),
                  ].join(' · ')}
                </dd>
                <dt>Generated on</dt>
                <dd>{generatedAt || new Date().toLocaleString()}</dd>
                <dt>Generated by</dt>
                <dd>
                  {userRole === 'PAO_MAKER'
                    ? 'pao21.maker (PAO Maker)'
                    : `${userRole} User`}
                </dd>
                <dt>Demo business date</dt>
                <dd>15-Sep-2026 · financial year 2026-27</dd>
                <dt>Record count</dt>
                <dd className="strong">{cnt(rows.length)}</dd>
                <dt>Monetary total</dt>
                <dd className="strong">
                  {moneyCols.length > 0 ? money(monetaryTotal) : <span className="muted">Not applicable</span>}
                </dd>
              </dl>
            </div>

            <div className="tbl-wrap">
              <table className="dt" id="rpTable">
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
                  {loading ? (
                    <tr>
                      <td colSpan={Math.max(headers.length, 1)}>
                        <div className="empty" style={{ padding: '34px 14px', textAlign: 'center' }}>
                          ⏳ Querying live PostgreSQL tables for {activeRep.name}...
                        </div>
                      </td>
                    </tr>
                  ) : rows.length === 0 ? (
                    <tr>
                      <td colSpan={Math.max(headers.length, 1)}>
                        <div className="empty" style={{ padding: '34px 14px', textAlign: 'center', color: 'var(--grey-600)' }}>
                          No data matches the selected report parameters.
                        </div>
                      </td>
                    </tr>
                  ) : (
                    rows.slice(0, 400).map((row, rIdx) => {
                      const isTotal = String(row[0]) === 'TOTAL';
                      return (
                        <tr
                          key={rIdx}
                          style={
                            isTotal
                              ? { fontWeight: 700, background: 'var(--grey-050)' }
                              : undefined
                          }
                        >
                          {row.map((cell, cIdx) => {
                            const isMoney = moneyCols.includes(cIdx);
                            return (
                              <td key={cIdx} className={isMoney ? 'num' : ''}>
                                {isMoney
                                  ? typeof cell === 'number'
                                    ? money(cell)
                                    : money(Number(cell) || 0)
                                  : cell === '' || cell === null || cell === undefined
                                  ? '—'
                                  : String(cell)}
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
            {rows.length > 400 && (
              <div className="tbl-foot">
                Showing the first 400 of {cnt(rows.length)} rows on screen. Export to CSV for the complete report.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default ReportsPage;
