import React, { useEffect, useState, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { cnt, fmtStamp, exportCSV } from '../utils/format';

interface AuditRow {
  id: number;
  audit_id: number;
  ts: string;
  user: string;
  role: string;
  module: string;
  action: string;
  entity: string;
  entityId?: string;
  oldV?: string;
  newV?: string;
  old_data?: any;
  new_data?: any;
  remarks: string;
  txid?: number;
}

interface AuditSummary {
  total_entries: number;
  distinct_modules: number;
  distinct_actions: number;
  earliest_entry: string;
  latest_entry: string;
  modules: string[];
  actions: string[];
}

export const AuditTrailPage: React.FC = () => {
  const { showToast, refreshKey } = useApp();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<AuditRow[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  // Live KPI Summary
  const [summary, setSummary] = useState<AuditSummary>({
    total_entries: 0,
    distinct_modules: 0,
    distinct_actions: 0,
    earliest_entry: '—',
    latest_entry: '—',
    modules: [],
    actions: [],
  });

  // Filters
  const [filters, setFilters] = useState({
    module: '',
    action: '',
    user: '',
    from: '',
    to: '',
    search: '',
  });

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 25;

  // Selected Audit Row for Detail / Diff Modal
  const [selectedAudit, setSelectedAudit] = useState<AuditRow | null>(null);

  // Auto-refresh / Live polling toggle
  const [liveSync, setLiveSync] = useState(false);

  const fetchAuditLogs = useCallback(async (isSilent: boolean = false) => {
    try {
      if (!isSilent) setLoading(true);
      const res = await api.getAuditLogs({
        module: filters.module || undefined,
        action: filters.action || undefined,
        user: filters.user || undefined,
        from_date: filters.from || undefined,
        to_date: filters.to || undefined,
        search: filters.search || undefined,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      });

      const mapped: AuditRow[] = (res.items || []).map((a: any, idx: number) => ({
        id: a.audit_id || a.id || (page - 1) * pageSize + idx + 1,
        audit_id: a.audit_id || a.id || (page - 1) * pageSize + idx + 1,
        ts: a.ts || a.timestamp || a.changed_at || a.created_at || '',
        user: a.user || a.user_name || 'System Administrator',
        role: a.role || a.user_role || 'SYSADMIN',
        module: a.module || a.module_name || 'Reconciliation',
        action: (a.action || a.operation || a.action_type || 'UPDATE').toUpperCase(),
        entity: a.entity || a.entity_type || 'Reconciliation Result',
        entityId: a.entityId || a.entity_id || a.row_pk ? String(a.entityId || a.entity_id || a.row_pk) : '—',
        oldV: a.oldV || a.old_value || '',
        newV: a.newV || a.new_value || '',
        old_data: a.old_data || null,
        new_data: a.new_data || null,
        remarks: a.remarks || `${a.action || 'Operation'} recorded in PostgreSQL`,
        txid: a.txid,
      }));

      setItems(mapped);
      setTotalCount(res.total || 0);

      if (res.summary && Object.keys(res.summary).length > 0) {
        setSummary(prev => ({
          ...prev,
          ...res.summary,
        }));
      }
    } catch (err: any) {
      if (!isSilent) {
        showToast(err.message || 'Failed to fetch audit logs from PostgreSQL', 'error');
      }
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, [filters, page, pageSize, showToast]);

  // Initial and reactive fetch on refreshKey or filter changes
  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs, refreshKey]);

  // Optional Live Sync (polls every 8 seconds if enabled)
  useEffect(() => {
    if (!liveSync) return;
    const interval = setInterval(() => {
      fetchAuditLogs(true);
    }, 8000);
    return () => clearInterval(interval);
  }, [liveSync, fetchAuditLogs]);

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

  const handleClearFilters = () => {
    setFilters({
      module: '',
      action: '',
      user: '',
      from: '',
      to: '',
      search: '',
    });
    setPage(1);
  };

  const handleExport = () => {
    const headers = [
      'Audit ID',
      'Date / Time',
      'User',
      'Role',
      'Module',
      'Action',
      'Entity Type',
      'Entity ID',
      'Old Value Summary',
      'New Value Summary',
      'Remarks',
    ];
    const rows = items.map(a => [
      a.audit_id,
      a.ts,
      a.user,
      a.role,
      a.module,
      a.action,
      a.entity,
      a.entityId || '',
      a.oldV || '',
      a.newV || '',
      a.remarks,
    ]);
    exportCSV('ifms_budget_audit_trail.csv', headers, rows, [
      ['Report', 'IFMS Revenue Collection & Reconciliation Audit Trail'],
      ['Source Database', 'PostgreSQL (schema: ifms_budget, table: audit_change_log)'],
      ['Total Database Entries', String(summary.total_entries || totalCount)],
      ['Filter Applied', JSON.stringify(filters)],
      ['Generated On', new Date().toISOString()],
    ]);
    showToast('Audit trail exported successfully.', 'success');
  };

  // Badge helper
  const getActionBadge = (action: string) => {
    const act = action.toUpperCase();
    if (act === 'INSERT' || act === 'CREATE') return 'badge b-green';
    if (act === 'UPDATE' || act === 'MODIFY' || act === 'RECON_RUN') return 'badge b-blue';
    if (act === 'DELETE' || act === 'REMOVE') return 'badge b-red';
    return 'badge b-purple';
  };

  // Extract Diff Fields for Modal
  const getDiffEntries = (oldData: any, newData: any) => {
    const keys = Array.from(new Set([...Object.keys(oldData || {}), ...Object.keys(newData || {})]));
    return keys.map(k => {
      const oldVal = oldData ? oldData[k] : undefined;
      const newVal = newData ? newData[k] : undefined;
      const isChanged = JSON.stringify(oldVal) !== JSON.stringify(newVal);
      return { key: k, oldVal, newVal, isChanged };
    });
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Audit Trail</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Audit Trail</h2>
          <div className="sub">
            An immutable-style record of every upload, deletion, reset, reconciliation run, status override, approval, rejection, configuration change, and database mutation retained in PostgreSQL (table: ifms_budget.audit_change_log).
          </div>
        </div>
        <div className="flex gap8 items-center">
          <button
            className={`btn btn-sm ${liveSync ? 'btn-p' : ''}`}
            onClick={() => setLiveSync(!liveSync)}
            title="Automatically poll for new database mutations every 8s"
          >
            {liveSync ? '● Live Sync ON' : '○ Live Sync OFF'}
          </button>
          <button className="btn btn-sm" onClick={() => fetchAuditLogs()} title="Refresh audit entries from database">
            &#8635; Refresh
          </button>
          <button className="btn btn-sm" onClick={handleClearFilters}>
            Clear filters
          </button>
        </div>
      </div>

      {/* 4 KPI Cards */}
      <div className="grid g4 mb16">
        <div className="kpi">
          <div className="lab">Audit entries</div>
          <div className="val">{cnt(summary.total_entries || totalCount)}</div>
          <div className="sec">Retained in database</div>
        </div>
        <div className="kpi">
          <div className="lab">Distinct modules</div>
          <div className="val">{cnt(summary.distinct_modules || summary.modules.length || 7)}</div>
          <div className="sec">All application modules</div>
        </div>
        <div className="kpi">
          <div className="lab">Distinct actions</div>
          <div className="val">{cnt(summary.distinct_actions || summary.actions.length || 3)}</div>
          <div className="sec">CRUD, approval &amp; engine runs</div>
        </div>
        <div className="kpi">
          <div className="lab">Earliest entry</div>
          <div className="val" style={{ fontSize: '13px' }}>
            {summary.earliest_entry ? summary.earliest_entry.slice(0, 11) : '—'}
          </div>
          <div className="sec">
            Most recent {summary.latest_entry ? summary.latest_entry.slice(0, 11) : '—'}
          </div>
        </div>
      </div>

      {/* Filter Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Audit entries</h3>
            <div className="sub">Filtered directly via PostgreSQL queries on ifms_budget.audit_change_log</div>
          </div>
          <div className="flex gap8 items-center">
            <input
              type="text"
              className="inp"
              placeholder="Search keyword (ID, table, data)..."
              value={filters.search}
              onChange={e => {
                setFilters({ ...filters, search: e.target.value });
                setPage(1);
              }}
              style={{ width: '250px', padding: '4px 8px', fontSize: '12px' }}
            />
          </div>
        </div>

        <div className="filterbar">
          <div className="fld">
            <label>Module</label>
            <select
              className="inp"
              value={filters.module}
              onChange={e => {
                setFilters({ ...filters, module: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All modules</option>
              {summary.modules.length > 0
                ? summary.modules.map(m => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))
                : ['Reconciliation', 'Accounting', 'Masters', 'Upload', 'Refund Management', 'Exceptions', 'Budget'].map(m => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
            </select>
          </div>

          <div className="fld">
            <label>Action</label>
            <select
              className="inp"
              value={filters.action}
              onChange={e => {
                setFilters({ ...filters, action: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All actions</option>
              <option value="INSERT">INSERT</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>

          <div className="fld">
            <label>User contains</label>
            <input
              className="inp"
              placeholder="e.g. pao21 or admin"
              value={filters.user}
              onChange={e => {
                setFilters({ ...filters, user: e.target.value });
                setPage(1);
              }}
            />
          </div>

          <div className="fld">
            <label>From date</label>
            <input
              type="date"
              className="inp"
              value={filters.from}
              onChange={e => {
                setFilters({ ...filters, from: e.target.value });
                setPage(1);
              }}
            />
          </div>

          <div className="fld">
            <label>To date</label>
            <input
              type="date"
              className="inp"
              value={filters.to}
              onChange={e => {
                setFilters({ ...filters, to: e.target.value });
                setPage(1);
              }}
            />
          </div>
        </div>

        {/* Main Table */}
        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th>Audit ID</th>
                <th>Date / time</th>
                <th>User</th>
                <th>Role</th>
                <th>Module</th>
                <th>Action</th>
                <th>Entity type</th>
                <th>Entity ID</th>
                <th>Old value</th>
                <th>New value</th>
                <th>Remarks</th>
                <th style={{ textAlign: 'right' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={12} className="center py-8 muted">
                    Loading audit trail entries from PostgreSQL...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={12}>
                    <div className="empty">No audit entries match your filters in PostgreSQL.</div>
                  </td>
                </tr>
              ) : (
                items.map(a => (
                  <tr
                    key={a.audit_id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedAudit(a)}
                    title="Click to view detailed JSON diff"
                  >
                    <td className="mono strong">#{a.audit_id}</td>
                    <td className="nowrap">{a.ts || fmtStamp(a.ts)}</td>
                    <td className="mono">{a.user}</td>
                    <td><span className="badge b-purple">{a.role}</span></td>
                    <td><span className="badge b-blue">{a.module}</span></td>
                    <td>
                      <span className={getActionBadge(a.action)}>{a.action}</span>
                    </td>
                    <td>{a.entity}</td>
                    <td className="mono tiny">{a.entityId || '—'}</td>
                    <td>
                      {a.oldV ? (
                        <div className="small muted" style={{ maxWidth: '180px', wordBreak: 'break-word' }}>
                          {a.oldV}
                        </div>
                      ) : (
                        <span className="muted">&mdash;</span>
                      )}
                    </td>
                    <td>
                      {a.newV ? (
                        <div className="small strong" style={{ maxWidth: '200px', wordBreak: 'break-word', color: 'var(--c-pri, #1e88e5)' }}>
                          {a.newV}
                        </div>
                      ) : (
                        <span className="muted">&mdash;</span>
                      )}
                    </td>
                    <td>
                      <div className="small" style={{ maxWidth: '280px' }}>{a.remarks}</div>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-xs"
                        onClick={e => {
                          e.stopPropagation();
                          setSelectedAudit(a);
                        }}
                        style={{ padding: '2px 6px', fontSize: '11px' }}
                      >
                        View Diff
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer */}
        <div className="tbl-foot">
          <div>
            Showing {totalCount > 0 ? (page - 1) * pageSize + 1 : 0} &ndash; {Math.min(page * pageSize, totalCount)} of {cnt(totalCount)} entries
          </div>
          <div className="flex gap8 items-center">
            <button
              className="btn btn-xs"
              disabled={page <= 1 || loading}
              onClick={() => setPage(p => Math.max(1, p - 1))}
            >
              &larr; Prev
            </button>
            <span className="small muted">
              Page {page} of {totalPages}
            </span>
            <button
              className="btn btn-xs"
              disabled={page >= totalPages || loading}
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

      {/* ========================================================================= */}
      {/* AUDIT RECORD DETAIL & JSON DIFF MODAL                                    */}
      {/* ========================================================================= */}
      {selectedAudit && (
        <div className="ovl" onClick={() => setSelectedAudit(null)}>
          <div className="modal" style={{ maxWidth: '850px' }} onClick={e => e.stopPropagation()}>
            <div className="modal-h">
              <div>
                <h3>
                  Audit Record #{selectedAudit.audit_id}: {selectedAudit.entity} {selectedAudit.entityId !== '—' ? selectedAudit.entityId : ''}
                </h3>
                <div className="sub">
                  Executed by <strong>{selectedAudit.user}</strong> ({selectedAudit.role}) on <strong>{selectedAudit.ts}</strong> &bull; Module: {selectedAudit.module}
                </div>
              </div>
              <button type="button" className="modal-x" onClick={() => setSelectedAudit(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <div className="grid g3 mb12">
                <div className="box info small">
                  <strong>Operation:</strong> <span className={getActionBadge(selectedAudit.action)}>{selectedAudit.action}</span>
                </div>
                <div className="box info small">
                  <strong>Entity:</strong> {selectedAudit.entity} (#{selectedAudit.entityId})
                </div>
                <div className="box info small">
                  <strong>Transaction ID:</strong> {selectedAudit.txid || 'Auto-CDC'}
                </div>
              </div>

              <div className="mb12">
                <strong>Audit Description:</strong>
                <p className="small muted mt4">{selectedAudit.remarks}</p>
              </div>

              {/* Side-by-side Diff Table */}
              <h4 className="mb8">Field Level State Diff (Before vs After)</h4>
              <div className="tbl-wrap mb16">
                <table className="dt">
                  <thead>
                    <tr>
                      <th style={{ width: '25%' }}>Field Name</th>
                      <th style={{ width: '37%' }}>Old Value (Before)</th>
                      <th style={{ width: '38%' }}>New Value (After)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getDiffEntries(selectedAudit.old_data, selectedAudit.new_data).map(diff => (
                      <tr
                        key={diff.key}
                        style={{
                          backgroundColor: diff.isChanged ? 'rgba(30, 136, 229, 0.08)' : undefined,
                        }}
                      >
                        <td className="mono strong small">{diff.key}</td>
                        <td className="small" style={{ wordBreak: 'break-word', color: diff.isChanged ? '#e53935' : undefined }}>
                          {diff.oldVal !== undefined ? JSON.stringify(diff.oldVal) : <span className="muted">—</span>}
                        </td>
                        <td className="small" style={{ wordBreak: 'break-word', color: diff.isChanged ? '#43a047' : undefined, fontWeight: diff.isChanged ? 'bold' : 'normal' }}>
                          {diff.newVal !== undefined ? JSON.stringify(diff.newVal) : <span className="muted">—</span>}
                        </td>
                      </tr>
                    ))}
                    {getDiffEntries(selectedAudit.old_data, selectedAudit.new_data).length === 0 && (
                      <tr>
                        <td colSpan={3} className="tc muted py8">
                          No JSON field payload available.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Raw JSON Payloads */}
              <details className="box small">
                <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Raw JSON Payloads</summary>
                <div className="grid g2 mt8">
                  <div>
                    <strong>old_data:</strong>
                    <pre className="mono tiny p8 mt4 bg-dim" style={{ overflowX: 'auto', maxHeight: '180px' }}>
                      {JSON.stringify(selectedAudit.old_data, null, 2) || 'null'}
                    </pre>
                  </div>
                  <div>
                    <strong>new_data:</strong>
                    <pre className="mono tiny p8 mt4 bg-dim" style={{ overflowX: 'auto', maxHeight: '180px' }}>
                      {JSON.stringify(selectedAudit.new_data, null, 2) || 'null'}
                    </pre>
                  </div>
                </div>
              </details>
            </div>

            <div className="modal-f">
              <button type="button" className="btn btn-sm btn-p" onClick={() => setSelectedAudit(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AuditTrailPage;
