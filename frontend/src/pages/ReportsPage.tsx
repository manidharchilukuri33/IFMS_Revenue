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

  // Report picker: compact search-combo dropdown
  const [searchCat, setSearchCat] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);

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

  // Filter catalogue by the picker's search box
  const filteredCatalogue = catalogue.filter(r => {
    const query = searchCat.toLowerCase().trim();
    return (
      !query ||
      r.id.toLowerCase().includes(query) ||
      r.name.toLowerCase().includes(query) ||
      r.desc.toLowerCase().includes(query) ||
      r.group.toLowerCase().includes(query)
    );
  });

  const selectReport = (id: string) => {
    setActiveReportId(id);
    setPickerOpen(false);
    setSearchCat('');
  };

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
            Seventeen operational and governance reports dynamically querying PostgreSQL schema with real-time parameters, live totals, and CSV export.
          </div>
        </div>
        <div className="flex gap8">
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
        <div className="card-h" style={{ padding: '8px 14px' }}>
          <div className="flex items-center gap8">
            <span style={{ fontSize: '14px' }}>⚙️</span>
            <div>
              <h3 style={{ fontSize: '12.5px' }}>Report Parameters</h3>
              <div className="sub" style={{ fontSize: '11px' }}>Filter live database records across all catalogue reports</div>
            </div>
          </div>
          <button className="btn btn-sm" onClick={handleClearParameters}>
            Clear parameters
          </button>
        </div>

        <div className="filterbar" style={{ padding: '8px 14px', gap: '8px' }}>
          <div className="fld" style={{ marginBottom: 0 }}>
            <label>Date from</label>
            <input
              type="date"
              className="inp"
              value={filters.from}
              onChange={e => setFilters({ ...filters, from: e.target.value })}
            />
          </div>
          <div className="fld" style={{ marginBottom: 0 }}>
            <label>Date to</label>
            <input
              type="date"
              className="inp"
              value={filters.to}
              onChange={e => setFilters({ ...filters, to: e.target.value })}
            />
          </div>
          <div className="fld" style={{ marginBottom: 0 }}>
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
          <div className="fld" style={{ marginBottom: 0 }}>
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
          <div className="fld" style={{ marginBottom: 0 }}>
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
          <div className="fld" style={{ marginBottom: 0 }}>
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

      {/* Report Picker: compact search-combo dropdown (replaces the old fixed sidebar list) */}
      <div className="report-picker-wrap">
        <button
          type="button"
          className="report-picker-combo"
          onClick={() => setPickerOpen(o => !o)}
        >
          <span aria-hidden="true">🔍</span>
          <span className="report-picker-combo-label">
            {activeRep.id.toUpperCase()} &middot; {activeRep.name}
          </span>
          <span className="report-picker-caret" aria-hidden="true">{pickerOpen ? '▲' : '▼'}</span>
        </button>

        {pickerOpen && (
          <>
            <div className="report-picker-backdrop" onClick={() => setPickerOpen(false)} />
            <div className="report-picker-dropdown">
              <div className="catalogue-search" style={{ background: 'var(--white)' }}>
                <input
                  type="text"
                  className="catalogue-search-inp"
                  placeholder="Search reports (e.g. R01, Bank, Tax)..."
                  value={searchCat}
                  onChange={e => setSearchCat(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="catalogue-list" style={{ maxHeight: '360px' }}>
                {filteredCatalogue.length === 0 ? (
                  <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--grey-500)', fontSize: '12px' }}>
                    No reports match &ldquo;{searchCat}&rdquo;
                  </div>
                ) : (
                  filteredGroups.map(g => (
                    <div key={g} style={{ marginBottom: '8px' }}>
                      <div className="catalogue-group-heading">
                        <span>{g}</span>
                        <span className="catalogue-group-count">
                          {filteredCatalogue.filter(r => r.group === g).length}
                        </span>
                      </div>
                      {filteredCatalogue
                        .filter(r => r.group === g)
                        .map(r => {
                          const isActive = r.id === activeReportId;
                          return (
                            <div
                              key={r.id}
                              className={`catalogue-item ${isActive ? 'active' : ''}`}
                              onClick={() => selectReport(r.id)}
                            >
                              <div className="catalogue-item-header">
                                <span className="report-code-badge">{r.id.toUpperCase()}</span>
                                {isActive && (
                                  <span style={{ fontSize: '11px', color: 'var(--teal-600)', fontWeight: 700 }}>
                                    Active ▶
                                  </span>
                                )}
                              </div>
                              <div className="catalogue-item-title">{r.name}</div>
                              <div className="catalogue-item-desc">{r.desc}</div>
                            </div>
                          );
                        })}
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Dedicated Report Viewer Panel */}
        <div className="report-viewer-panel">
          {/* Header Banner */}
          <div className="report-viewer-header">
            <div>
              <div className="flex items-center gap8">
                <span className="badge b-blue" style={{ fontSize: '11px', fontWeight: 700 }}>
                  {activeRep.id.toUpperCase()}
                </span>
                <span className="badge b-grey" style={{ fontSize: '11px' }}>
                  {activeRep.group}
                </span>
                <h3 style={{ fontSize: '15px', color: 'var(--navy-900)', margin: 0 }}>
                  {reportData?.report_name || activeRep.name}
                </h3>
              </div>
              <div className="sub mt4" style={{ fontSize: '12px', color: 'var(--grey-600)' }}>
                {reportData?.description || activeRep.desc}
              </div>
            </div>

            <div className="flex items-center gap8">
              {loading && <span className="badge b-amber">Querying Database...</span>}
              <button className="btn btn-sm" onClick={fetchReport} title="Refresh report from live database">
                🔄 Refresh
              </button>
            </div>
          </div>

          {/* Meta & Filter Summary Strip */}
          <div className="report-meta-strip">
            <div className="report-meta-item">
              <span className="report-meta-label">📅 Date Range:</span>
              <span className="report-meta-val">
                {filters.from ? fmtDate(filters.from) : 'All'} &rarr; {filters.to ? fmtDate(filters.to) : 'All'}
              </span>
            </div>
            <div className="report-meta-item">
              <span className="report-meta-label">🏛️ Scope:</span>
              <span className="report-meta-val">
                {filters.source || filters.dept || filters.pao || filters.bank
                  ? [filters.source, filters.dept, filters.pao, filters.bank].filter(Boolean).join(' / ')
                  : 'All Sources & Entities'}
              </span>
            </div>
            <div className="report-meta-item">
              <span className="report-meta-label">📊 Records:</span>
              <span className="report-meta-val strong">{cnt(rows.length)}</span>
            </div>
            <div className="report-meta-item">
              <span className="report-meta-label">💰 Monetary Total:</span>
              <span className="report-meta-val strong" style={{ color: 'var(--teal-700)' }}>
                {moneyCols.length > 0 ? money(monetaryTotal) : 'N/A'}
              </span>
            </div>
            <div className="report-meta-item" style={{ marginLeft: 'auto' }}>
              <span className="report-meta-label">⚡ Database:</span>
              <span className="report-meta-val" style={{ fontSize: '11px', color: 'var(--grey-600)' }}>
                ifms_budget (Live)
              </span>
            </div>
          </div>

          {/* Dynamic Data Table with Sticky Headers & Sleek Scrollbar */}
          <div className="report-table-container">
            <table>
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
                      <div className="empty" style={{ padding: '40px 16px', textAlign: 'center' }}>
                        ⏳ Querying live PostgreSQL tables for {activeRep.name}...
                      </div>
                    </td>
                  </tr>
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={Math.max(headers.length, 1)}>
                      <div className="empty" style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--grey-500)' }}>
                        🔍 No records match the selected report parameters in the database.
                      </div>
                    </td>
                  </tr>
                ) : (
                  rows.map((row, rIdx) => {
                    const isTotal = String(row[0]) === 'TOTAL';
                    return (
                      <tr
                        key={rIdx}
                        className={isTotal ? 'total-row' : ''}
                        style={
                          isTotal
                            ? { fontWeight: 700, background: '#eef2f7', borderTop: '2px solid var(--navy-500)' }
                            : undefined
                        }
                      >
                        {row.map((cell, cIdx) => {
                          const isMoney = moneyCols.includes(cIdx);
                          return (
                            <td key={cIdx} className={isMoney ? 'num mono' : ''}>
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
        </div>

    </div>
  );
};

export default ReportsPage;
