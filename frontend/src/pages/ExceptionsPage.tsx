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

  // Trace & Solve Modals
  const [traceModalExc, setTraceModalExc] = useState<ExceptionItem | null>(null);
  const [traceData, setTraceData] = useState<any | null>(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const [solveModalExc, setSolveModalExc] = useState<ExceptionItem | null>(null);
  const [solveType, setSolveType] = useState('MANUAL_MATCH');
  const [solveTargetStatus, setSolveTargetStatus] = useState('Matched');
  const [solveRemarks, setSolveRemarks] = useState('');
  const [solveRefNo, setSolveRefNo] = useState('');
  const [solveSuspenseHead, setSolveSuspenseHead] = useState('8658-00-102-01-00-01');
  const [solveLoading, setSolveLoading] = useState(false);

  // Discrepancy Letter Modal States
  const [letterRecipientType, setLetterRecipientType] = useState('AGENCY_BANK');
  const [letterRecipientName, setLetterRecipientName] = useState('');
  const [letterRecipientAddress, setLetterRecipientAddress] = useState('');
  const [letterSubject, setLetterSubject] = useState('');
  const [letterBody, setLetterBody] = useState('');
  const [letterSending, setLetterSending] = useState(false);
  const [letterSentResult, setLetterSentResult] = useState<any | null>(null);

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

        const dateToken = raised.replace(/[^0-9]/g, '');
        const excCode = e.exception_no || e.exception_code || `EXC-${dateToken}-${String(e.id || idx + 1).padStart(6, '0')}`;
        let revId = e.rev_transaction_id || e.rev_id;
        if (!revId || revId.includes('2026-27')) {
          revId = revId ? revId.replace('2026-27', dateToken) : `REV-TXN-${dateToken}-${String(e.recon_id || e.id || idx + 1).padStart(6, '0')}`;
        }

        return {
          id: e.id || idx + 1,
          excCode,
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
          revId,
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

  const handleOpenTrace = async (e: ExceptionItem) => {
    setTraceModalExc(e);
    setTraceLoading(true);
    try {
      const reconId = e.reconId || e.id;
      const data = await api.traceReconResult(reconId);
      setTraceData(data);
    } catch (err: any) {
      showToast(err.message || 'Trace inspection failed', 'error');
      setTraceData(null);
    } finally {
      setTraceLoading(false);
    }
  };

  const handleOpenSolve = (e: ExceptionItem) => {
    setSolveModalExc(e);
    setSolveType('MANUAL_MATCH');
    setSolveTargetStatus('Matched');
    setSolveRemarks(`Resolved exception ${e.excCode} (${e.category}) for challan ${e.challan}`);
    setSolveRefNo(`EXC-RES-${new Date().getFullYear()}-${String(e.id).padStart(4, '0')}`);
    setSolveSuspenseHead('8658-00-102-01-00-01');
  };

  const handleConfirmSolve = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!solveModalExc) return;
    try {
      setSolveLoading(true);
      const reconId = solveModalExc.reconId || solveModalExc.id;
      await api.solveReconDiscrepancy(reconId, {
        resolution_type: solveType,
        target_status: solveTargetStatus,
        remarks: solveRemarks,
        reference_no: solveRefNo,
        suspense_head_code: solveType === 'POST_TO_SUSPENSE' ? solveSuspenseHead : undefined,
      });
      showToast(`Exception and discrepancy solved successfully! Updated in PostgreSQL database.`, 'success');
      setSolveModalExc(null);
      if (traceModalExc && traceModalExc.id === solveModalExc.id) {
        setTraceModalExc(null);
      }
      if (selectedExc && selectedExc.id === solveModalExc.id) {
        setSelectedExc(null);
      }
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to solve exception', 'error');
    } finally {
      setSolveLoading(false);
    }
  };

  const handleOpenLetter = (e: ExceptionItem) => {
    setLetterModal(e);
    setLetterSentResult(null);

    let defaultType = 'AGENCY_BANK';
    let defaultName = `The Branch Manager / Nodal Officer, ${e.bank || 'State Bank of India'}`;
    let defaultAddr = `${e.bank || 'State Bank of India'}, Focal Point Branch / Government Business Division, New Delhi`;

    if (e.category.toLowerCase().includes('rat') || e.category.toLowerCase().includes('unidentified')) {
      defaultType = 'PAO_OFFICER';
      defaultName = `Pay & Accounts Officer (${e.pao} - ${e.dept})`;
      defaultAddr = `Office of the Pay & Accounts Officer (${e.pao}), Directorate of Accounts, GNCTD`;
    } else if (e.category.toLowerCase().includes('department') || e.category.toLowerCase().includes('pao mismatch')) {
      defaultType = 'DDO';
      defaultName = `Drawing & Disbursing Officer (DDO), Dept of ${e.dept}`;
      defaultAddr = `Department of ${e.dept}, Government of NCT of Delhi`;
    }

    const sub = `Discrepancy Notice: Clarification & Rectification Required for Exception ${e.excCode} (${e.category})`;

    const bodyText = `To,\n${defaultName}\n${defaultAddr}\n\n` +
      `Subject: ${sub}\n\n` +
      `Sir / Madam,\n\n` +
      `On scrutiny of the three-way revenue reconciliation between departmental portal filings and agency bank collection scrolls for FY 2026-27, the following discrepancy has been observed against Government Account:\n\n` +
      `--- EXCEPTION TRANSACTION DETAILS ---\n` +
      `• Exception ID          : ${e.excCode}\n` +
      `• Category / Nature     : ${e.category}\n` +
      `• Severity Level        : ${e.severity}\n` +
      `• Challan / Reference   : ${e.challan}\n` +
      `• Payer / Remitter      : ${e.payer}\n` +
      `• Revenue Source & Dept : ${e.source} (${e.dept})\n` +
      `• PAO Office Jurisdiction : ${e.pao}\n` +
      `• Disputed Amount       : ₹${money(e.amount)}\n` +
      `• Raised Date           : ${fmtDateDash(e.raisedOn)}\n` +
      `• Compliance Due Date   : ${fmtDateDash(e.due)}\n\n` +
      `--- DISCREPANCY FINDINGS & AUDIT OBSERVATION ---\n` +
      `Audit Observation: ${e.detail}\n\n` +
      `You are requested to verify the relevant scroll entries and submit the scroll rectification / UTR confirmation within 7 working days to enable formal receipt booking in the Treasury Account.\n\n` +
      `Yours faithfully,\n\n` +
      `(Authorized Signatory)\n` +
      `Pay & Accounts Officer / Treasury Officer\n` +
      `Government Treasury Accounts, Directorate of Accounts`;

    setLetterRecipientType(defaultType);
    setLetterRecipientName(defaultName);
    setLetterRecipientAddress(defaultAddr);
    setLetterSubject(sub);
    setLetterBody(bodyText);
  };

  const handleRecipientTypeChange = (type: string) => {
    setLetterRecipientType(type);
    if (!letterModal) return;
    const e = letterModal;
    let name = letterRecipientName;
    let addr = letterRecipientAddress;
    if (type === 'AGENCY_BANK') {
      name = `The Branch Manager / Nodal Officer, ${e.bank || 'State Bank of India'}`;
      addr = `${e.bank || 'State Bank of India'}, Focal Point Branch, New Delhi`;
    } else if (type === 'PAO_OFFICER') {
      name = `Pay & Accounts Officer (${e.pao} - ${e.dept})`;
      addr = `Office of the Pay & Accounts Officer (${e.pao}), Directorate of Accounts, GNCTD`;
    } else if (type === 'TREASURY_ADMIN') {
      name = 'The Senior Treasury Officer / Joint Director (Treasury)';
      addr = 'State Central Treasury & Revenue Settlement Cell, Directorate of Accounts';
    } else if (type === 'DDO') {
      name = `Drawing & Disbursing Officer (DDO), Dept of ${e.dept}`;
      addr = `Department of ${e.dept}, Government of NCT of Delhi`;
    } else if (type === 'TAXPAYER') {
      name = e.payer || 'Taxpayer / Remitter';
      addr = `Registered Taxpayer Address, Delhi / NCR (Challan: ${e.challan})`;
    } else if (type === 'CUSTOM_OFFICER') {
      name = 'Concerned Officer / Competent Authority';
      addr = 'Directorate of Revenue & Accounts, GNCTD';
    }
    setLetterRecipientName(name);
    setLetterRecipientAddress(addr);
  };

  const handleSendExceptionLetter = async (ev?: React.FormEvent) => {
    if (ev) ev.preventDefault();
    if (!letterModal) return;
    try {
      setLetterSending(true);
      const reconId = letterModal.reconId || letterModal.id;
      const res = await api.sendReconDiscrepancyLetter(reconId, {
        recipient_type: letterRecipientType,
        recipient_name: letterRecipientName,
        recipient_address: letterRecipientAddress,
        letter_subject: letterSubject,
        letter_body: letterBody,
        target_role: 'PAO_CHECK',
      });
      setLetterSentResult(res);
      showToast(`Discrepancy Notice ${res.letter_no || ''} dispatched & persisted to PostgreSQL database!`, 'success');
      await fetchData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to dispatch discrepancy letter', 'error');
    } finally {
      setLetterSending(false);
    }
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
                        {e.status !== 'Closed' && (
                          <div className="inline-flex gap4 ml4">
                            <button
                              className="btn btn-xs btn-outline"
                              style={{ borderColor: 'var(--navy-600, #1b4a83)', color: 'var(--navy-800, #0f2d52)', fontWeight: 600, padding: '2px 8px' }}
                              title="Trace complete 3-way transaction path and audit log"
                              onClick={() => handleOpenTrace(e)}
                            >
                              🔍 Trace
                            </button>
                            <button
                              className="btn btn-xs btn-ok"
                              style={{ fontWeight: 600, padding: '2px 8px' }}
                              title="Solve discrepancy and persist resolution in database"
                              onClick={() => handleOpenSolve(e)}
                            >
                              ⚡ Solve
                            </button>
                          </div>
                        )}
                        {canManage && e.status !== 'Closed' && (
                          <button
                            className="btn btn-xs ml4"
                            style={{ background: '#4338ca', color: '#ffffff', borderColor: '#3730a3', fontWeight: 600, padding: '2px 8px' }}
                            title="Draft and dispatch official discrepancy notice letter"
                            onClick={() => handleOpenLetter(e)}
                          >
                            ✉️ Letter
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

            <div className="modal-f flex justify-between items-center">
              <div className="flex gap8">
                {selectedExc.status !== 'Closed' && (
                  <>
                    <button
                      className="btn btn-sm btn-outline"
                      style={{ borderColor: 'var(--navy-600, #1b4a83)', color: 'var(--navy-800, #0f2d52)', fontWeight: 600 }}
                      onClick={() => {
                        const e = selectedExc;
                        setSelectedExc(null);
                        handleOpenTrace(e);
                      }}
                    >
                      🔍 Trace 3-Way Path
                    </button>
                    <button
                      className="btn btn-sm btn-ok"
                      style={{ fontWeight: 600 }}
                      onClick={() => {
                        const e = selectedExc;
                        setSelectedExc(null);
                        handleOpenSolve(e);
                      }}
                    >
                      ⚡ Solve Discrepancy
                    </button>
                  </>
                )}
              </div>
              <div className="flex gap8">
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
                      style={{ background: '#4338ca', borderColor: '#3730a3' }}
                      onClick={() => {
                        setLetterModal(selectedExc);
                        setSelectedExc(null);
                      }}
                    >
                      ✉️ Generate follow-up letter
                    </button>
                  </>
                )}
                <button className="btn btn-sm" onClick={() => setSelectedExc(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Official Clarification & Discrepancy Notice Letter Modal */}
      {letterModal && (
        <div className="ovl">
          <div className="modal" style={{ maxWidth: '980px', width: '95%' }}>
            <div className="modal-h">
              <div>
                <h3>✉️ Official Discrepancy Notice: {letterModal.excCode}</h3>
                <div className="sub">
                  Challan: <strong className="mono">{letterModal.challan}</strong> &middot; Category: <strong>{letterModal.category}</strong> &middot; Amount: <strong className="mono">{money(letterModal.amount)}</strong>
                </div>
              </div>
              <button className="close" onClick={() => setLetterModal(null)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleSendExceptionLetter}>
              <div className="modal-b" style={{ maxHeight: 'calc(85vh - 120px)', overflowY: 'auto' }}>
                {/* Dispatched Confirmation Banner */}
                {letterSentResult && (
                  <div className="box ok mb16" style={{ background: '#ecfdf5', borderColor: '#10b981', borderWidth: '2px' }}>
                    <div className="flex items-center justify-between mb8">
                      <strong style={{ color: '#065f46', fontSize: '15px' }}>
                        ✅ Discrepancy Notice Dispatched &amp; Persisted to PostgreSQL!
                      </strong>
                      <span className="badge b-green">STATUS: ISSUED</span>
                    </div>
                    <div className="small" style={{ color: '#047857' }}>
                      Official Letter No: <strong className="mono">{letterSentResult.letter_no}</strong> &middot; Issued Date: <strong>{letterSentResult.issued_date}</strong> &middot; Recipient: <strong>{letterSentResult.recipient_name}</strong> ({letterSentResult.recipient_type})
                    </div>
                    <div className="tiny mt4" style={{ color: '#065f46' }}>
                      Recorded in <code>ifms_budget.rev_exception_letter</code>, added to exception notes timeline, logged in audit change log, and dispatched as a system notification.
                    </div>
                  </div>
                )}

                {/* Exception KPI Summary */}
                <div className="grid g4 mb16">
                  <div className="kpi">
                    <div className="lab">Disputed Amount</div>
                    <div className="val">{money(letterModal.amount)}</div>
                    <div className="sec">Raised: {fmtDateDash(letterModal.raisedOn)}</div>
                  </div>
                  <div className="kpi">
                    <div className="lab">Source / Department</div>
                    <div className="val" style={{ fontSize: '15px' }}>{letterModal.source} ({letterModal.dept})</div>
                    <div className="sec">PAO: {letterModal.pao}</div>
                  </div>
                  <div className="kpi">
                    <div className="lab">Agency Bank</div>
                    <div className="val" style={{ fontSize: '15px' }}>{letterModal.bank || 'State Bank of India'}</div>
                    <div className="sec">Challan: {letterModal.challan}</div>
                  </div>
                  <div className="kpi warn">
                    <div className="lab">Severity &amp; Due Date</div>
                    <div className="val" style={{ fontSize: '15px' }}>{letterModal.severity}</div>
                    <div className="sec">Due: {fmtDateDash(letterModal.due)} ({letterModal.ageing}d)</div>
                  </div>
                </div>

                {/* Recipient Selection */}
                <div className="card p12 mb16" style={{ background: '#f8fafc', border: '1px solid #cbd5e1' }}>
                  <h4 className="mb8" style={{ color: 'var(--navy-900)' }}>1. Select Target Recipient Entity / Officer</h4>
                  <div className="fld mb12">
                    <label>Recipient Category <span className="req">*</span></label>
                    <select
                      className="inp"
                      value={letterRecipientType}
                      onChange={e => handleRecipientTypeChange(e.target.value)}
                    >
                      <option value="AGENCY_BANK">🏦 Agency Bank Branch Manager / Nodal Officer</option>
                      <option value="PAO_OFFICER">🏛️ Pay &amp; Accounts Officer (PAO Lead / Checker)</option>
                      <option value="TREASURY_ADMIN">⚖️ State Treasury Officer / Joint Director (Treasury)</option>
                      <option value="DDO">🏢 Drawing &amp; Disbursing Officer (DDO - Department)</option>
                      <option value="TAXPAYER">👤 Taxpayer / Remitter</option>
                      <option value="CUSTOM_OFFICER">📋 Custom Authority / Other Officer</option>
                    </select>
                  </div>

                  <div className="grid g2 gap12">
                    <div className="fld">
                      <label>Recipient Name &amp; Designation <span className="req">*</span></label>
                      <input
                        className="inp"
                        value={letterRecipientName}
                        onChange={e => setLetterRecipientName(e.target.value)}
                        placeholder="e.g. Branch Manager, State Bank of India"
                        required
                      />
                    </div>
                    <div className="fld">
                      <label>Recipient Address / Office Jurisdiction <span className="req">*</span></label>
                      <input
                        className="inp"
                        value={letterRecipientAddress}
                        onChange={e => setLetterRecipientAddress(e.target.value)}
                        placeholder="e.g. Focal Point Collection Branch, Government Business Division"
                        required
                      />
                    </div>
                  </div>
                </div>

                {/* Subject and Body Editor */}
                <div className="card p12 mb16" style={{ background: '#ffffff', border: '1px solid #cbd5e1' }}>
                  <h4 className="mb8" style={{ color: 'var(--navy-900)' }}>2. Letter Subject &amp; Discrepancy Breakdown</h4>
                  <div className="fld mb12">
                    <label>Letter Subject <span className="req">*</span></label>
                    <input
                      className="inp"
                      value={letterSubject}
                      onChange={e => setLetterSubject(e.target.value)}
                      required
                    />
                  </div>

                  <div className="fld mb12">
                    <label>Official Notice Body <span className="req">*</span></label>
                    <textarea
                      className="inp font-mono"
                      rows={14}
                      style={{ fontSize: '12px', lineHeight: '1.5' }}
                      value={letterBody}
                      onChange={e => setLetterBody(e.target.value)}
                      required
                    />
                  </div>

                  <div className="box info small">
                    <strong>Database Persistence:</strong> This notice is automatically stored in <code>ifms_budget.rev_exception_letter</code>, recorded in <code>rev_exception_note</code>, audited in <code>audit_change_log</code>, and notified across PAO officers.
                  </div>
                </div>
              </div>

              <div className="modal-f flex justify-between items-center">
                <div className="flex gap8 items-center">
                  <button type="button" className="btn btn-sm" onClick={() => setLetterModal(null)}>
                    {letterSentResult ? 'Done' : 'Cancel'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline"
                    title="Print official letter document"
                    onClick={() => window.print()}
                  >
                    🖨️ Print Letter
                  </button>
                </div>
                <button
                  type="submit"
                  className="btn btn-p btn-sm"
                  style={{ background: '#4338ca', borderColor: '#3730a3', minWidth: '180px' }}
                  disabled={letterSending}
                >
                  {letterSending ? 'Dispatching & Saving...' : '✉️ Send Official Letter & Save to DB'}
                </button>
              </div>
            </form>
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

      {/* Exception 3-Way Trace Modal */}
      {traceModalExc && (
        <div className="ovl">
          <div className="modal" style={{ maxWidth: '980px', width: '95%' }}>
            <div className="modal-h">
              <div>
                <h3>🔍 3-Way Transaction Trace: {traceModalExc.excCode}</h3>
                <div className="sub">
                  Challan: <strong className="mono">{traceModalExc.challan}</strong> &middot; Category: <strong>{traceModalExc.category}</strong> &middot; Payer: <strong>{traceModalExc.payer}</strong>
                </div>
              </div>
              <button className="close" onClick={() => setTraceModalExc(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              {traceLoading ? (
                <div className="center py-12 muted">
                  <div className="spinner mb8"></div>
                  <div>Inspecting 3-way transaction linkages across Portal, Agency Bank, and RBI databases...</div>
                </div>
              ) : (
                <div>
                  {/* KPI Summary Matrix */}
                  <div className="grid g4 mb16">
                    <div className="kpi">
                      <div className="lab">Exception Amount</div>
                      <div className="val">{money(traceModalExc.amount)}</div>
                      <div className="sec">Raised: {fmtDateDash(traceModalExc.raisedOn)}</div>
                    </div>
                    <div className="kpi">
                      <div className="lab">Portal / Source Total</div>
                      <div className="val">{money(traceData?.portal_total ?? traceModalExc.grossAmount ?? traceModalExc.amount)}</div>
                      <div className="sec">Source: {traceModalExc.source}</div>
                    </div>
                    <div className="kpi">
                      <div className="lab">Agency Bank / RBI Total</div>
                      <div className="val">{money(traceData?.rbi_total ?? traceData?.bank_total ?? traceModalExc.amount)}</div>
                      <div className="sec">Due: {fmtDateDash(traceModalExc.due)}</div>
                    </div>
                    <div className="kpi warn">
                      <div className="lab">Ageing &amp; Severity</div>
                      <div className="val">{traceModalExc.ageing} day(s)</div>
                      <div className="sec"><span className={badgeClass(traceModalExc.severity)}>{traceModalExc.severity}</span></div>
                    </div>
                  </div>

                  {/* 3-Way Lane Comparison */}
                  <h4 className="mb8" style={{ color: 'var(--navy-900)' }}>Three-Way Discrepancy Legs Breakdown</h4>
                  <div className="grid g3 mb16 gap12">
                    {/* Lane 1: Portal */}
                    <div className="box info" style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px' }}>
                      <div className="strong mb8 flex items-center gap6" style={{ color: 'var(--navy-900)' }}>
                        <span>🏛️ Leg 1: Department Portal</span>
                      </div>
                      <dl className="kv" style={{ gridTemplateColumns: '110px 1fr', fontSize: '12px' }}>
                        <dt>Source</dt>
                        <dd><strong>{traceModalExc.source}</strong> ({traceModalExc.dept})</dd>
                        <dt>PAO Office</dt>
                        <dd>{traceModalExc.pao}</dd>
                        <dt>Challan No</dt>
                        <dd className="mono strong">{traceModalExc.challan}</dd>
                        <dt>Payer</dt>
                        <dd>{traceModalExc.payer}</dd>
                        <dt>Staged Amount</dt>
                        <dd><strong className="mono" style={{ color: 'var(--navy-800)' }}>{money(traceData?.portal_total ?? traceModalExc.grossAmount ?? traceModalExc.amount)}</strong></dd>
                      </dl>
                    </div>

                    {/* Lane 2: Bank */}
                    <div className="box info" style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px' }}>
                      <div className="strong mb8 flex items-center gap6" style={{ color: 'var(--navy-900)' }}>
                        <span>🏦 Leg 2: Agency Bank Scroll</span>
                      </div>
                      <dl className="kv" style={{ gridTemplateColumns: '110px 1fr', fontSize: '12px' }}>
                        <dt>Bank Branch</dt>
                        <dd><strong>{traceModalExc.bank || 'State Bank of India'}</strong></dd>
                        <dt>Scroll Ref</dt>
                        <dd className="mono strong">{traceData?.bank_legs?.[0]?.scroll_no || `SCR-${traceModalExc.challan}`}</dd>
                        <dt>Bank Amount</dt>
                        <dd><strong className="mono" style={{ color: 'var(--navy-800)' }}>{money(traceData?.bank_total ?? traceModalExc.amount)}</strong></dd>
                        <dt>Assigned To</dt>
                        <dd>{traceModalExc.assigned}</dd>
                      </dl>
                    </div>

                    {/* Lane 3: RBI */}
                    <div className="box info" style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '8px' }}>
                      <div className="strong mb8 flex items-center gap6" style={{ color: 'var(--navy-900)' }}>
                        <span>⚖️ Leg 3: RBI CAS Credit</span>
                      </div>
                      <dl className="kv" style={{ gridTemplateColumns: '110px 1fr', fontSize: '12px' }}>
                        <dt>Settlement Hub</dt>
                        <dd><strong>CAS Nagpur</strong></dd>
                        <dt>RBI Credit Total</dt>
                        <dd><strong className="mono" style={{ color: 'var(--navy-800)' }}>{money(traceData?.rbi_total ?? traceModalExc.amount)}</strong></dd>
                        <dt>Exception Status</dt>
                        <dd><span className={badgeClass(traceModalExc.status)}>{traceModalExc.status}</span></dd>
                      </dl>
                    </div>
                  </div>

                  {/* Exception Description */}
                  <div className="box info mb12" style={{ fontSize: '12.5px' }}>
                    <div className="strong mb4">Exception Details &amp; Root Cause:</div>
                    <div className="mb8">{traceModalExc.detail}</div>
                    <div className="tiny muted flex items-center justify-between border-t pt-2" style={{ borderColor: '#e2e8f0' }}>
                      <span>🔒 Traced by user <strong>{userRole}</strong> &middot; Exception Code: <code>{traceModalExc.excCode}</code></span>
                      <span>Recorded in PostgreSQL <code>ifms_budget.audit_change_log</code></span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-f flex justify-between items-center">
              <button className="btn btn-sm" onClick={() => setTraceModalExc(null)}>
                Close
              </button>
              <button
                className="btn btn-ok btn-sm"
                onClick={() => {
                  const exc = traceModalExc;
                  setTraceModalExc(null);
                  handleOpenSolve(exc);
                }}
              >
                ⚡ Proceed to Solve Discrepancy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Exception Solve Resolution Modal */}
      {solveModalExc && (
        <div className="ovl">
          <div className="modal" style={{ maxWidth: '780px', width: '90%' }}>
            <div className="modal-h">
              <div>
                <h3>⚡ Solve Exception Discrepancy: {solveModalExc.excCode}</h3>
                <div className="sub">
                  Challan: <strong className="mono">{solveModalExc.challan}</strong> &middot; Category: <strong>{solveModalExc.category}</strong> &middot; Amount: <strong style={{ color: 'var(--red-700)' }}>{money(solveModalExc.amount)}</strong>
                </div>
              </div>
              <button className="close" onClick={() => setSolveModalExc(null)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleConfirmSolve}>
              <div className="modal-b">
                {/* Strategy Selection */}
                <div className="mb16">
                  <label className="strong block mb8" style={{ color: 'var(--navy-900)' }}>
                    Select Resolution Strategy <span className="req">*</span>
                  </label>
                  <div className="grid g2 gap10">
                    <div
                      className="p12 rounded pointer border transition-all"
                      style={{
                        background: solveType === 'MANUAL_MATCH' ? '#f0fdf4' : '#ffffff',
                        borderColor: solveType === 'MANUAL_MATCH' ? 'var(--teal-600)' : '#cbd5e1',
                        borderWidth: solveType === 'MANUAL_MATCH' ? '2px' : '1px',
                      }}
                      onClick={() => {
                        setSolveType('MANUAL_MATCH');
                        setSolveTargetStatus('Matched');
                      }}
                    >
                      <div className="flex items-center gap8 mb4">
                        <input
                          type="radio"
                          name="solveTypeExc"
                          checked={solveType === 'MANUAL_MATCH'}
                          onChange={() => {}}
                        />
                        <strong style={{ color: 'var(--teal-700)' }}>🟢 Manual Match Override &amp; Close</strong>
                      </div>
                      <div className="tiny muted ml20">
                        Authorize match based on verified supporting documentation and release receipt for general ledger booking.
                      </div>
                    </div>

                    <div
                      className="p12 rounded pointer border transition-all"
                      style={{
                        background: solveType === 'POST_TO_SUSPENSE' ? '#fffbeb' : '#ffffff',
                        borderColor: solveType === 'POST_TO_SUSPENSE' ? 'var(--amber-600)' : '#cbd5e1',
                        borderWidth: solveType === 'POST_TO_SUSPENSE' ? '2px' : '1px',
                      }}
                      onClick={() => {
                        setSolveType('POST_TO_SUSPENSE');
                        setSolveTargetStatus('Suspend');
                      }}
                    >
                      <div className="flex items-center gap8 mb4">
                        <input
                          type="radio"
                          name="solveTypeExc"
                          checked={solveType === 'POST_TO_SUSPENSE'}
                          onChange={() => {}}
                        />
                        <strong style={{ color: 'var(--amber-700)' }}>🟡 Transfer to Suspense Register</strong>
                      </div>
                      <div className="tiny muted ml20">
                        Move difference amount into Treasury (8658-102) or RAT (8658-101) suspense account pending bank scroll clarification.
                      </div>
                    </div>

                    <div
                      className="p12 rounded pointer border transition-all"
                      style={{
                        background: solveType === 'MARK_RESOLVED' ? '#eff6ff' : '#ffffff',
                        borderColor: solveType === 'MARK_RESOLVED' ? 'var(--navy-500)' : '#cbd5e1',
                        borderWidth: solveType === 'MARK_RESOLVED' ? '2px' : '1px',
                      }}
                      onClick={() => {
                        setSolveType('MARK_RESOLVED');
                        setSolveTargetStatus('Resolved');
                      }}
                    >
                      <div className="flex items-center gap8 mb4">
                        <input
                          type="radio"
                          name="solveTypeExc"
                          checked={solveType === 'MARK_RESOLVED'}
                          onChange={() => {}}
                        />
                        <strong style={{ color: 'var(--navy-700)' }}>🔵 Mark as Resolved / Rectified</strong>
                      </div>
                      <div className="tiny muted ml20">
                        Close exception case after verifying that departmental adjustment or timing correction was performed.
                      </div>
                    </div>

                    <div
                      className="p12 rounded pointer border transition-all"
                      style={{
                        background: solveType === 'DISCREPANCY_NOTICE' ? '#fef2f2' : '#ffffff',
                        borderColor: solveType === 'DISCREPANCY_NOTICE' ? 'var(--red-600)' : '#cbd5e1',
                        borderWidth: solveType === 'DISCREPANCY_NOTICE' ? '2px' : '1px',
                      }}
                      onClick={() => {
                        setSolveType('DISCREPANCY_NOTICE');
                        setSolveTargetStatus('Under Investigation');
                      }}
                    >
                      <div className="flex items-center gap8 mb4">
                        <input
                          type="radio"
                          name="solveTypeExc"
                          checked={solveType === 'DISCREPANCY_NOTICE'}
                          onChange={() => {}}
                        />
                        <strong style={{ color: 'var(--red-700)' }}>🔴 Escalate for Bank Recovery</strong>
                      </div>
                      <div className="tiny muted ml20">
                        Issue formal discrepancy notice to Agency Bank branch for recovery / clawback of short credit.
                      </div>
                    </div>
                  </div>
                </div>

                {/* Conditional Suspense Head */}
                {solveType === 'POST_TO_SUSPENSE' && (
                  <div className="fld mb12">
                    <label>Suspense Head <span className="req">*</span></label>
                    <select
                      className="inp"
                      value={solveSuspenseHead}
                      onChange={e => setSolveSuspenseHead(e.target.value)}
                    >
                      <option value="8658-00-102-01-00-01">8658-00-102-01-00-01 &mdash; Treasury Suspense Clearing Account</option>
                      <option value="8658-00-101-01-00-01">8658-00-101-01-00-01 &mdash; Remittance in Transit (RAT) Suspense Account</option>
                    </select>
                  </div>
                )}

                {/* Authority Reference */}
                <div className="fld mb12">
                  <label>Authority Order / Reference No</label>
                  <input
                    className="inp"
                    value={solveRefNo}
                    onChange={e => setSolveRefNo(e.target.value)}
                    placeholder="e.g. TREASURY/EXC/2026/09/44"
                  />
                </div>

                {/* Justification / Remarks */}
                <div className="fld mb12">
                  <label>Resolution Remarks &amp; Action Notes <span className="req">*</span></label>
                  <textarea
                    className="inp"
                    rows={3}
                    value={solveRemarks}
                    onChange={e => setSolveRemarks(e.target.value)}
                    placeholder="Provide the explanation, audit references, and justification for closing this exception..."
                    required
                  />
                </div>

                <div className="box info small">
                  <strong>Database Synchronization:</strong> This action updates <code>ifms_budget.rev_exception</code>, resolves the linked <code>rev_recon_result</code>, inserts into <code>rev_exception_note</code>, logs CDC in <code>audit_change_log</code>, and notifies the PAO Checker.
                </div>
              </div>

              <div className="modal-f flex justify-between items-center">
                <button type="button" className="btn btn-sm" onClick={() => setSolveModalExc(null)} disabled={solveLoading}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-ok btn-sm" disabled={solveLoading}>
                  {solveLoading ? 'Saving to Database...' : '⚡ Confirm & Persist Solution to Database'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default ExceptionsPage;
