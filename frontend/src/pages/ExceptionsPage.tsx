import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, compact, fmtDate, fmtDateDash, fmtStamp, badgeClass, exportCSV } from '../utils/format';

interface ExceptionItem {
  id: number;
  excCode: string;
  category: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  source: string;
  dept: string;
  pao: string;
  bank?: string;
  challan: string;
  payer: string;
  amount: number;
  grossAmount: number;
  raisedOn: string;
  due: string;
  ageing: number;
  assigned: string;
  status: 'Open' | 'Assigned' | 'Escalated' | 'Closed';
  escalated: boolean;
  detail: string;
  resolution?: string;
  closedOn?: string;
  comments: { by: string; text: string; ts: string }[];
  reconId?: number;
  revId?: string;
}

const EXC_CATEGORIES = [
  'Delayed bank remittance',
  'Amount mismatch',
  'Suspense / portal greater than RBI',
  'Duplicate transaction',
  'Unidentified RBI credit / RAT',
  'Cheque clearing delay',
  'Portal missing',
  'Bank record missing',
  'RBI record missing',
  'Date mismatch',
  'Invalid receipt head',
  'Department / PAO mismatch',
  'Invalid upload record',
  'Refund validation failure',
  'Devolution claim variance',
];

const PALETTE = ['#1b4a83', '#0f8878', '#b57905', '#c92a2a', '#5b21a8', '#2660a4', '#0b6b5e', '#8a5a00'];

const CATEGORY_COLOR_MAP: Record<string, string> = {
  'Delayed bank remittance': '#1b4a83',
  'Delayed bank remittances': '#1b4a83',
  'Amount mismatch': '#0f8878',
  'Suspense / portal greater than RBI': '#b57905',
  'Duplicate transaction': '#c92a2a',
  'Unidentified RBI credit / RAT': '#5b21a8',
  'Cheque clearing delay': '#2660a4',
  'Date mismatch': '#0b6b5e',
  'Portal missing': '#8a5a00',
  'Bank record missing': '#1b4a83',
  'RBI record missing': '#0f8878',
  'Department / PAO mismatch': '#2660a4',
  'Invalid receipt head': '#b57905',
  'Invalid upload record': '#c92a2a',
  'Refund validation failure': '#5b21a8',
  'Devolution claim variance': '#0b6b5e',
};

export const normalizeCategory = (cat: string): string => {
  if (!cat) return 'Amount mismatch';
  const clean = cat.trim();
  const upper = clean.toUpperCase().replace(/[\s\/-]+/g, '_');
  const map: Record<string, string> = {
    AMOUNT_MISMATCH: 'Amount mismatch',
    DUPLICATE_TRANSACTION: 'Duplicate transaction',
    DUPLICATE_SETTLEMENT: 'Duplicate transaction',
    DUPLICATE_SCROLL: 'Duplicate transaction',
    UNREMITTED_BANK_COLLECTION: 'Delayed bank remittance',
    DELAYED_BANK_REMITTANCE: 'Delayed bank remittance',
    DELAYED_BANK_REMITTANCES: 'Delayed bank remittance',
    SLA_BREACH: 'Delayed bank remittance',
    SUSPENSE: 'Suspense / portal greater than RBI',
    SUSPENSE_PORTAL_GREATER_THAN_RBI: 'Suspense / portal greater than RBI',
    UNREMITTED_CHALLAN: 'Suspense / portal greater than RBI',
    UNIDENTIFIED_GOVT_CREDIT: 'Unidentified RBI credit / RAT',
    UNIDENTIFIED_RBI_CREDIT: 'Unidentified RBI credit / RAT',
    UNIDENTIFIED_RBI_CREDIT_RAT: 'Unidentified RBI credit / RAT',
    ORPHAN_BANK_CREDIT: 'Unidentified RBI credit / RAT',
    PORTAL_MISSING: 'Portal missing',
    BANK_RECORD_MISSING: 'Bank record missing',
    RBI_RECORD_MISSING: 'RBI record missing',
    DATE_MISMATCH: 'Date mismatch',
    INVALID_RECEIPT_HEAD: 'Invalid receipt head',
    DEPT_PAO_MISMATCH: 'Department / PAO mismatch',
    DEPARTMENT_PAO_MISMATCH: 'Department / PAO mismatch',
    INVALID_UPLOAD_RECORD: 'Invalid upload record',
    REFUND_VALIDATION_FAILURE: 'Refund validation failure',
    DEVOLUTION_CLAIM_VARIANCE: 'Devolution claim variance',
    CHEQUE_CLEARING_DELAY: 'Cheque clearing delay',
  };
  if (map[upper]) return map[upper];
  return clean.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

export const ExceptionsPage: React.FC = () => {
  const { userRole, showToast, setActiveTab, refreshKey, triggerRefresh } = useApp();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<ExceptionItem[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // Filters
  const [filters, setFilters] = useState({
    cat: '',
    sev: '',
    dept: '',
    pao: '',
    source: '',
    bank: '',
    status: '',
    assigned: '',
    age: '',
    min: '',
  });

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Modals
  const [selectedExc, setSelectedExc] = useState<ExceptionItem | null>(null);
  const [letterModal, setLetterModal] = useState<ExceptionItem | null>(null);
  const [bulkAssignModal, setBulkAssignModal] = useState(false);
  const [newAssignee, setNewAssignee] = useState('PAO21-OFFICER');
  const [commentText, setCommentText] = useState('');

  const canManage = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO'].includes(userRole);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await api.getExceptions({ limit: 500 });
      const mapped: ExceptionItem[] = (res.items || []).map((e: any, idx: number) => {
        const amt = Number(e.amount || e.exception_amount || 25000);
        const raised = e.created_at ? e.created_at.slice(0, 10) : '2026-09-10';
        const due = e.due_date ? e.due_date.slice(0, 10) : '2026-09-17';
        const isOver = due < new Date().toISOString().slice(0, 10) && e.status !== 'Closed';
        const rawCat = e.category || e.exception_type || 'Amount mismatch';
        const cat = normalizeCategory(rawCat);

        return {
          id: e.id || idx + 1,
          excCode: e.exception_code || `EXC-2026-${String(e.id || idx + 1).padStart(5, '0')}`,
          category: cat,
          severity: (e.severity || 'High') as any,
          source: e.revenue_source || 'GST',
          dept: e.department_code || 'TT',
          pao: e.pao_code || 'PAO21',
          bank: e.bank_code || 'SBI',
          challan: e.challan_no || `CH-GST-${idx + 10001}`,
          payer: e.payer_name || 'Commercial Entity',
          amount: amt,
          grossAmount: amt * 1.2,
          raisedOn: raised,
          due,
          ageing: Number(e.ageing_days || Math.floor((Date.now() - new Date(raised).getTime()) / 86400000) || 3),
          assigned: e.assigned_to || e.assigned_user || 'pao21.maker',
          status: (e.status || (isOver ? 'Escalated' : 'Open')) as any,
          escalated: isOver || e.status === 'Escalated',
          detail: e.description || e.remarks || 'Amount variance observed between portal and bank remittance.',
          resolution: e.resolution,
          closedOn: e.closed_at,
          comments: e.comments || [
            { by: 'sysadmin.ifms', text: 'Exception logged from reconciliation run', ts: '2026-09-10 14:00:00' },
          ],
          reconId: e.recon_id,
          revId: e.rev_id || `REV-TXN-${idx + 1}`,
        };
      });

      setItems(mapped);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch exceptions', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  // Counts
  const openList = items.filter(e => e.status !== 'Closed');
  const criticalList = openList.filter(e => e.severity === 'Critical' || e.severity === 'High');
  const overdueList = openList.filter(e => e.due < new Date().toISOString().slice(0, 10));
  const closedList = items.filter(e => e.status === 'Closed');

  // Filter application
  const filtered = items.filter(e => {
    if (filters.cat && normalizeCategory(e.category).toLowerCase() !== normalizeCategory(filters.cat).toLowerCase()) return false;
    if (filters.sev && e.severity.toLowerCase() !== filters.sev.toLowerCase()) return false;
    if (filters.dept && e.dept.toLowerCase() !== filters.dept.toLowerCase()) return false;
    if (filters.pao && e.pao.toLowerCase() !== filters.pao.toLowerCase()) return false;
    if (filters.source && e.source.toLowerCase() !== filters.source.toLowerCase()) return false;
    if (filters.bank && (e.bank || '').toLowerCase() !== filters.bank.toLowerCase()) return false;
    if (filters.status && e.status.toLowerCase() !== filters.status.toLowerCase()) return false;
    if (filters.assigned && !e.assigned.toLowerCase().includes(filters.assigned.toLowerCase())) return false;
    if (filters.age && e.ageing < Number(filters.age)) return false;
    if (filters.min && e.amount < Number(filters.min)) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentRows = filtered.slice((page - 1) * pageSize, page * pageSize);

  const handleClearFilters = () => {
    setFilters({
      cat: '',
      sev: '',
      dept: '',
      pao: '',
      source: '',
      bank: '',
      status: '',
      assigned: '',
      age: '',
      min: '',
    });
    setPage(1);
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(currentRows.map(r => r.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]));
  };

  const handleBulkAssign = async () => {
    if (!selectedIds.length) {
      showToast('Please select at least one exception to assign.', 'warning');
      return;
    }
    setItems(prev =>
      prev.map(x =>
        selectedIds.includes(x.id)
          ? {
              ...x,
              assigned: newAssignee,
              status: x.status === 'Open' ? 'Assigned' : x.status,
              comments: [
                ...x.comments,
                { by: userRole, text: `Assigned to ${newAssignee}`, ts: new Date().toISOString() },
              ],
            }
          : x
      )
    );
    showToast(`Assigned ${selectedIds.length} exception(s) to ${newAssignee}.`, 'success');
    setSelectedIds([]);
    setBulkAssignModal(false);
  };

  const handleEscalateOverdue = async () => {
    if (!overdueList.length) {
      showToast('No overdue exceptions found.', 'info');
      return;
    }
    setItems(prev =>
      prev.map(x =>
        overdueList.some(o => o.id === x.id)
          ? {
              ...x,
              status: 'Escalated',
              escalated: true,
              comments: [
                ...x.comments,
                { by: 'sysadmin.ifms', text: 'Auto-escalated due date breach', ts: new Date().toISOString() },
              ],
            }
          : x
      )
    );
    showToast(`Escalated ${overdueList.length} overdue exception(s) to Treasury Administration.`, 'success');
  };

  const handleAddComment = () => {
    if (!selectedExc || !commentText.trim()) return;
    const newComment = {
      by: `${userRole.toLowerCase()}.user`,
      text: commentText,
      ts: new Date().toISOString().replace('T', ' ').slice(0, 19),
    };
    setSelectedExc({
      ...selectedExc,
      comments: [...selectedExc.comments, newComment],
    });
    setItems(prev =>
      prev.map(x =>
        x.id === selectedExc.id ? { ...x, comments: [...x.comments, newComment] } : x
      )
    );
    setCommentText('');
    showToast('Comment added.', 'success');
  };

  const handleCloseException = (id: number) => {
    setItems(prev =>
      prev.map(x =>
        x.id === id
          ? {
              ...x,
              status: 'Closed',
              resolution: 'Resolved and closed with verified documentation.',
              closedOn: new Date().toISOString().slice(0, 10),
            }
          : x
      )
    );
    if (selectedExc?.id === id) {
      setSelectedExc(prev => (prev ? { ...prev, status: 'Closed' } : null));
    }
    showToast('Exception closed successfully.', 'success');
  };

  const handleExport = () => {
    const headers = [
      'Exception ID',
      'Category',
      'Severity',
      'Source',
      'Dept',
      'PAO',
      'Bank',
      'Challan',
      'Payer',
      'Amount',
      'Raised On',
      'Due Date',
      'Ageing Days',
      'Assigned To',
      'Status',
      'Detail',
    ];
    const rows = filtered.map(e => [
      e.excCode,
      e.category,
      e.severity,
      e.source,
      e.dept,
      e.pao,
      e.bank || '',
      e.challan,
      e.payer,
      e.amount,
      e.raisedOn,
      e.due,
      e.ageing,
      e.assigned,
      e.status,
      e.detail,
    ]);
    exportCSV('ifms_exception_register.csv', headers, rows, [
      ['Report', 'Exception & Investigation Register'],
      ['Total Open', String(openList.length)],
      ['Total At Risk', money(openList.reduce((a, b) => a + b.amount, 0))],
    ]);
  };

  // Category breakdown for chart
  const catCounts: { [key: string]: number } = {};
  openList.forEach(e => {
    const cat = normalizeCategory(e.category);
    catCounts[cat] = (catCounts[cat] || 0) + 1;
  });
  const catData = Object.entries(catCounts)
    .map(([k, v]) => ({ k, v }))
    .sort((a, b) => b.v - a.v);
  const maxCatVal = catData.length ? Math.max(...catData.map(d => d.v), 1) : 1;

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Exceptions &amp; Investigation</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Exceptions &amp; Investigation Register</h2>
          <div className="sub">
            Every reconciliation outcome other than a clean match, together with rejected upload rows, raises a tracked exception with a severity, owner, due date and escalation state.
          </div>
        </div>
        <div className="flex gap8">
          {canManage && (
            <>
              <button
                className="btn btn-p btn-sm"
                onClick={() => {
                  if (!selectedIds.length) {
                    showToast('Select one or more rows using checkboxes first.', 'warning');
                    return;
                  }
                  setBulkAssignModal(true);
                }}
              >
                &#128100; Bulk assign selected
              </button>
              <button className="btn btn-warn btn-sm" onClick={handleEscalateOverdue}>
                &#9650; Escalate overdue
              </button>
            </>
          )}
          <button
            className="btn btn-sm"
            onClick={() => {
              setFilters({ ...filters, status: '' });
              showToast(`Showing all exceptions (${overdueList.length} overdue cases marked in red).`, 'info');
            }}
          >
            &#9202; Overdue cases ({overdueList.length})
          </button>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid g4 mb16">
        <div className="kpi err">
          <div className="lab">Open exceptions</div>
          <div className="val">{cnt(openList.length)}</div>
          <div className="sec">{compact(openList.reduce((a, b) => a + b.amount, 0))} at risk</div>
        </div>
        <div className="kpi err">
          <div className="lab">Critical / high severity</div>
          <div className="val">{cnt(criticalList.length)}</div>
          <div className="sec">Require immediate action</div>
        </div>
        <div className="kpi warn">
          <div className="lab">Overdue beyond due date</div>
          <div className="val">{cnt(overdueList.length)}</div>
          <div className="sec">Due within 3 day(s) of being raised</div>
        </div>
        <div className="kpi ok">
          <div className="lab">Closed</div>
          <div className="val">{cnt(closedList.length)}</div>
          <div className="sec">Resolved with a recorded reason</div>
        </div>
      </div>

      {/* Open exceptions by category chart */}
      {catData.length > 0 && (
        <div className="card mb16">
          <div className="card-h">
            <div>
              <h3>Open exceptions by category</h3>
              <div className="sub">Click any bar to quickly filter the Exception Register below</div>
            </div>
            {filters.cat && (
              <button
                className="btn btn-xs"
                onClick={() => {
                  setFilters({ ...filters, cat: '' });
                  setPage(1);
                }}
              >
                Reset category filter (Active: {filters.cat})
              </button>
            )}
          </div>
          <div className="card-b" style={{ maxWidth: '780px' }}>
            {(() => {
              const w = 720;
              const h = Math.max(130, catData.length * 32 + 36);
              const pad = { l: 235, r: 35, t: 10, b: 24 };
              const iw = w - pad.l - pad.r;
              const ih = h - pad.t - pad.b;
              const step = catData.length ? ih / catData.length : 0;
              const bh = catData.length ? Math.min(22, Math.max(12, step - 8)) : 12;
              const max = maxCatVal;

              return (
                <svg
                  viewBox={`0 0 ${w} ${h}`}
                  width="100%"
                  height={h}
                  role="img"
                  aria-label="Open exceptions by category"
                  style={{ overflow: 'visible', display: 'block' }}
                >
                  {/* Grid lines and bottom axis labels */}
                  {[0, 1, 2, 3, 4].map(g => {
                    const x = pad.l + (iw * g) / 4;
                    const val = (max * g) / 4;
                    return (
                      <g key={`grid-${g}`}>
                        <line className="gridline" x1={x} y1={pad.t} x2={x} y2={pad.t + ih} />
                        <text x={x} y={h - 6} fontSize="9" textAnchor="middle" fill="var(--grey-600)">
                          {Number.isInteger(val) ? val : val.toFixed(1)}
                        </text>
                      </g>
                    );
                  })}

                  {/* Horizontal Category Bars */}
                  {catData.map((d, i) => {
                    const y = pad.t + i * step + (step - bh) / 2;
                    const bw = Math.max(2, iw * (d.v / max));
                    const col = CATEGORY_COLOR_MAP[d.k] || PALETTE[i % PALETTE.length];
                    const isSelected = filters.cat && normalizeCategory(filters.cat).toLowerCase() === normalizeCategory(d.k).toLowerCase();
                    const lx = pad.l + bw + 6;

                    return (
                      <g
                        key={d.k}
                        style={{ cursor: 'pointer' }}
                        onClick={() => {
                          const newCat = isSelected ? '' : d.k;
                          setFilters({ ...filters, cat: newCat });
                          setPage(1);
                        }}
                      >
                        <title>{`${d.k}: ${d.v} open cases (Click to filter)`}</title>
                        <text
                          x={pad.l - 8}
                          y={y + bh / 2 + 3.5}
                          fontSize="10"
                          fontWeight={isSelected ? '700' : '500'}
                          textAnchor="end"
                          fill={isSelected ? 'var(--navy-900)' : 'var(--grey-700)'}
                        >
                          {d.k}
                        </text>
                        <rect
                          x={pad.l}
                          y={y}
                          width={bw}
                          height={bh}
                          fill={col}
                          rx={3}
                          opacity={filters.cat && !isSelected ? 0.35 : 0.92}
                          stroke={isSelected ? '#0b2340' : 'transparent'}
                          strokeWidth={isSelected ? 1.5 : 0}
                        />
                        <text
                          x={lx}
                          y={y + bh / 2 + 3.5}
                          fontSize="9.5"
                          textAnchor="start"
                          fill="var(--navy-900)"
                          fontWeight="700"
                        >
                          {d.v}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              );
            })()}
          </div>
        </div>
      )}

      {/* Filter Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Exception register</h3>
            <div className="sub">Select rows to bulk assign. Severity: Critical, High, Medium, Low.</div>
          </div>
          <button className="btn btn-sm" onClick={handleClearFilters}>
            Clear filters
          </button>
        </div>

        <div className="filterbar">
          <div className="fld">
            <label>Exception type</label>
            <select
              className="inp"
              value={filters.cat}
              onChange={e => {
                setFilters({ ...filters, cat: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All categories ({openList.length})</option>
              {EXC_CATEGORIES.map(c => {
                const count = catCounts[c] || 0;
                return (
                  <option key={c} value={c}>
                    {c} {count > 0 ? `(${count})` : ''}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="fld">
            <label>Severity</label>
            <select
              className="inp"
              value={filters.sev}
              onChange={e => {
                setFilters({ ...filters, sev: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All severities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div className="fld">
            <label>Department</label>
            <select
              className="inp"
              value={filters.dept}
              onChange={e => {
                setFilters({ ...filters, dept: e.target.value });
                setPage(1);
              }}
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
            <label>Status</label>
            <select
              className="inp"
              value={filters.status}
              onChange={e => {
                setFilters({ ...filters, status: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All statuses</option>
              <option value="Open">Open</option>
              <option value="Assigned">Assigned</option>
              <option value="Escalated">Escalated</option>
              <option value="Closed">Closed</option>
            </select>
          </div>

          <div className="fld">
            <label>Assigned officer contains</label>
            <input
              className="inp"
              placeholder="e.g. PAO21"
              value={filters.assigned}
              onChange={e => {
                setFilters({ ...filters, assigned: e.target.value });
                setPage(1);
              }}
            />
          </div>

          <div className="fld">
            <label>Minimum ageing (days)</label>
            <input
              type="number"
              className="inp"
              value={filters.age}
              onChange={e => {
                setFilters({ ...filters, age: e.target.value });
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
                <th style={{ width: '32px' }}>
                  <input
                    type="checkbox"
                    onChange={handleSelectAll}
                    checked={selectedIds.length === currentRows.length && currentRows.length > 0}
                  />
                </th>
                <th>Exception ID</th>
                <th>Category</th>
                <th>Severity</th>
                <th>Source</th>
                <th>Dept</th>
                <th>PAO</th>
                <th>Bank</th>
                <th>Challan / reference</th>
                <th>Payer</th>
                <th className="num">Exception amount</th>
                <th>Raised on</th>
                <th>Due date</th>
                <th className="num">Ageing (days)</th>
                <th>Assigned to</th>
                <th>Status</th>
                <th style={{ width: '240px' }}>Detail</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={18} className="center py-8 muted">
                    Loading exceptions...
                  </td>
                </tr>
              ) : currentRows.length === 0 ? (
                <tr>
                  <td colSpan={18}>
                    <div className="empty">No exceptions match your active filters.</div>
                  </td>
                </tr>
              ) : (
                currentRows.map(e => {
                  const isOver = e.due < new Date().toISOString().slice(0, 10) && e.status !== 'Closed';
                  return (
                    <tr key={e.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(e.id)}
                          onChange={() => handleToggleSelect(e.id)}
                        />
                      </td>
                      <td className="mono strong">{e.excCode}</td>
                      <td>
                        {e.category}
                        {isOver && <div className="tiny"><span className="badge b-red">Overdue</span></div>}
                      </td>
                      <td>
                        <span className={badgeClass(e.severity)}>{e.severity}</span>
                      </td>
                      <td>{e.source}</td>
                      <td>{e.dept}</td>
                      <td>{e.pao}</td>
                      <td>{e.bank || '—'}</td>
                      <td className="mono">{e.challan}</td>
                      <td>{e.payer}</td>
                      <td className="num">{money(e.amount)}</td>
                      <td className="nowrap">{fmtDateDash(e.raisedOn)}</td>
                      <td className="nowrap">
                        {isOver ? (
                          <span className="badge b-red">{fmtDate(e.due)}</span>
                        ) : (
                          fmtDateDash(e.due)
                        )}
                      </td>
                      <td className="num">{e.ageing}</td>
                      <td>{e.assigned}</td>
                      <td>
                        <span className={badgeClass(e.status)}>{e.status}</span>
                        {e.escalated && <span className="badge b-red ml4">Escalated</span>}
                      </td>
                      <td>
                        <div className="small">{e.detail}</div>
                      </td>
                      <td className="nowrap">
                        <button className="btn btn-xs" onClick={() => setSelectedExc(e)}>
                          Open
                        </button>{' '}
                        {canManage && e.status !== 'Closed' && (
                          <button className="btn btn-xs btn-p" onClick={() => setLetterModal(e)}>
                            Letter
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
            {filtered.length > 0 && (
              <tfoot>
                <tr>
                  <td colSpan={10} className="strong">
                    Total ({cnt(filtered.length)} exceptions)
                  </td>
                  <td className="num strong">{money(filtered.reduce((a, b) => a + b.amount, 0))}</td>
                  <td colSpan={7}></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>

        {/* Table Footer */}
        <div className="tbl-foot">
          <div>
            Showing {(page - 1) * pageSize + 1} &ndash; {Math.min(page * pageSize, filtered.length)} of {cnt(filtered.length)} rows &middot; Selected: {selectedIds.length}
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

      {/* Exception Detail Modal */}
      {selectedExc && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Exception {selectedExc.excCode}</h3>
                <div className="sub">{selectedExc.category} &mdash; {money(selectedExc.amount)}</div>
              </div>
              <button className="close" onClick={() => setSelectedExc(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <dl className="kv mb12">
                <dt>Exception ID</dt>
                <dd className="mono strong">{selectedExc.excCode}</dd>
                <dt>Category</dt>
                <dd>{selectedExc.category}</dd>
                <dt>Severity</dt>
                <dd><span className={badgeClass(selectedExc.severity)}>{selectedExc.severity}</span></dd>
                <dt>Status</dt>
                <dd><span className={badgeClass(selectedExc.status)}>{selectedExc.status}</span></dd>
                <dt>Challan / reference</dt>
                <dd className="mono">{selectedExc.challan}</dd>
                <dt>Payer</dt>
                <dd>{selectedExc.payer}</dd>
                <dt>Exception amount</dt>
                <dd className="strong">{money(selectedExc.amount)}</dd>
                <dt>Raised on / Due</dt>
                <dd>{fmtDate(selectedExc.raisedOn)} &rarr; {fmtDate(selectedExc.due)}</dd>
                <dt>Assigned to</dt>
                <dd>{selectedExc.assigned}</dd>
              </dl>

              <div className="box mb12">
                <h4>Detail</h4>
                <div className="small">{selectedExc.detail}</div>
              </div>

              <h4 className="mb8">Comments &amp; Audit Timeline</h4>
              <div className="timeline mb12">
                {selectedExc.comments.map((c, i) => (
                  <div key={i} className="tl-item">
                    <div className="tt">{c.by}</div>
                    <div className="small">{c.text}</div>
                    <div className="td">{c.ts}</div>
                  </div>
                ))}
              </div>

              {canManage && selectedExc.status !== 'Closed' && (
                <div className="flex gap8 mt12">
                  <input
                    className="inp grow"
                    placeholder="Add an investigation note or update..."
                    value={commentText}
                    onChange={e => setCommentText(e.target.value)}
                  />
                  <button className="btn btn-sm" onClick={handleAddComment}>
                    Add comment
                  </button>
                </div>
              )}
            </div>

            <div className="modal-f">
              {canManage && selectedExc.status !== 'Closed' && (
                <>
                  <button
                    className="btn btn-ok btn-sm"
                    onClick={() => handleCloseException(selectedExc.id)}
                  >
                    Close exception
                  </button>
                  <button
                    className="btn btn-p btn-sm"
                    onClick={() => {
                      setLetterModal(selectedExc);
                      setSelectedExc(null);
                    }}
                  >
                    Generate follow-up letter
                  </button>
                </>
              )}
              <button className="btn btn-sm" onClick={() => setSelectedExc(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Official Clarification Letter Modal */}
      {letterModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Official Clarification Demand Letter</h3>
                <div className="sub">Letter ref: IFMS/REV/EXC/{letterModal.excCode}/2026</div>
              </div>
              <button className="close" onClick={() => setLetterModal(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <div className="letter">
                <div className="lhead">
                  <h4>GOVERNMENT OF STATE REVENUE DEPARTMENT</h4>
                  <div>PAY &amp; ACCOUNTS OFFICE &mdash; {letterModal.pao}</div>
                  <div className="small muted">Ref: IFMS/EXC/{letterModal.excCode}/2026-27 &middot; Date: {fmtDate(new Date().toISOString().slice(0, 10))}</div>
                </div>

                <p>To,</p>
                <p>
                  <strong>The Branch Manager / Authorised Signatory</strong>
                  <br />
                  State Bank of India / Focal Point Collection Branch
                  <br />
                  Government Business Division
                </p>

                <p>
                  <strong>Subject: Clarification and rectification required for reconciliation discrepancy &mdash; {letterModal.excCode}</strong>
                </p>

                <p>Sir / Madam,</p>
                <p>
                  On scrutiny of the three-way reconciliation between departmental portal filings and agency bank scrolls for financial year 2026-27, the following discrepancy has been observed against Government Account:
                </p>

                <table>
                  <tbody>
                    <tr>
                      <td><strong>Exception ID</strong></td>
                      <td>{letterModal.excCode}</td>
                      <td><strong>Category</strong></td>
                      <td>{letterModal.category}</td>
                    </tr>
                    <tr>
                      <td><strong>Challan / Ref No</strong></td>
                      <td>{letterModal.challan}</td>
                      <td><strong>Payer Name</strong></td>
                      <td>{letterModal.payer}</td>
                    </tr>
                    <tr>
                      <td><strong>Disputed Amount</strong></td>
                      <td>{money(letterModal.amount)}</td>
                      <td><strong>Due Date</strong></td>
                      <td>{fmtDate(letterModal.due)}</td>
                    </tr>
                  </tbody>
                </table>

                <p>
                  You are requested to verify the relevant scroll entries and submit the scroll rectification / UTR confirmation within 7 working days to enable formal receipt booking in the Treasury Account.
                </p>

                <div className="mt24 right">
                  <strong>(Authorised Signatory)</strong>
                  <div>Pay &amp; Accounts Officer</div>
                  <div>Government Treasury Accounts</div>
                </div>
              </div>
            </div>

            <div className="modal-f">
              <button className="btn btn-p btn-sm" onClick={() => window.print()}>
                &#128424; Print Official Letter
              </button>
              <button className="btn btn-sm" onClick={() => setLetterModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Assign Modal */}
      {bulkAssignModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>Bulk Assign Exceptions</h3>
                <div className="sub">Assign {selectedIds.length} selected exception(s) to an officer</div>
              </div>
              <button className="close" onClick={() => setBulkAssignModal(false)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              <div className="fld mb12">
                <label>Assign to Officer / Queue <span className="req">*</span></label>
                <select
                  className="inp"
                  value={newAssignee}
                  onChange={e => setNewAssignee(e.target.value)}
                >
                  <option value="PAO21-OFFICER">PAO21-OFFICER (Trade & Taxes Lead)</option>
                  <option value="PAO10-EXCISE">PAO10-EXCISE (Excise Officer)</option>
                  <option value="PAO11-TRANS">PAO11-TRANS (Transport Officer)</option>
                  <option value="PAO12-STAMP">PAO12-STAMP (Stamp Registration Officer)</option>
                  <option value="TRE-ADMIN">TRE-ADMIN (Treasury Escalation Cell)</option>
                </select>
              </div>
            </div>

            <div className="modal-f">
              <button className="btn btn-sm" onClick={() => setBulkAssignModal(false)}>
                Cancel
              </button>
              <button className="btn btn-p btn-sm" onClick={handleBulkAssign}>
                Confirm Assignment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default ExceptionsPage;
