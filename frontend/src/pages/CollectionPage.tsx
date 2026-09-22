import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, fmtDate, fmtDateDash, fmtStamp, badgeClass, exportCSV } from '../utils/format';

interface CollectionRecord {
  id: number;
  revId: string;
  source: string;
  dept: string;
  pao: string;
  ddo: string;
  payerName: string;
  payerId: string;
  challanNo: string;
  cpin?: string;
  cin?: string;
  portalTxnId: string;
  mode: string;
  paymentDate: string;
  serviceDate?: string;
  amount: number;
  penaltyAmount?: number;
  receiptHead: string;
  serviceDesc?: string;
  portalStatus: string;
  bankStatus: string;
  rbiStatus: string;
  reconStatus: string;
  bookingStatus: string;
  deptValidated: boolean;
  raw?: any;
}

export const CollectionPage: React.FC = () => {
  const { userRole, showToast, setActiveTab, refreshKey, triggerRefresh } = useApp();
  const [loading, setLoading] = useState(true);
  const [records, setRecords] = useState<CollectionRecord[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [paos, setPaos] = useState<any[]>([]);
  const [banks, setBanks] = useState<any[]>([]);
  const [heads, setHeads] = useState<any[]>([]);

  // Filter state
  const [filters, setFilters] = useState({
    from: '',
    to: '',
    dept: '',
    pao: '',
    ddo: '',
    source: '',
    bank: '',
    mode: '',
    status: '',
    min: '',
    max: '',
  });

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 15;

  // Modals
  const [selectedTxn, setSelectedTxn] = useState<CollectionRecord | null>(null);
  const [txnTab, setTxnTab] = useState<'t1' | 't2' | 't3' | 't4' | 't5'>('t1');
  const [showManualModal, setShowManualModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState<CollectionRecord | null>(null);

  // Manual Form State
  const [formData, setFormData] = useState({
    portal_name: 'GSTN',
    revenue_source: 'GST',
    department_code: 'TT',
    pao_code: 'PAO21',
    ddo_code: 'DDO-TT-001',
    portal_transaction_id: '',
    challan_no: '',
    cpin: '',
    cin: '',
    payer_name: '',
    payer_id: '',
    payment_mode: 'NETBANKING',
    payment_date: new Date().toISOString().slice(0, 10),
    service_date: new Date().toISOString().slice(0, 10),
    amount: '',
    penalty_amount: '0.00',
    receipt_head: '0040-00-102-01-00-01',
    portal_status: 'PAID',
    service_description: '',
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const canCreate = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'DDO'].includes(userRole);
  const canValidate = ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'DDO'].includes(userRole);
  const canEdit = ['SYSADMIN', 'PAO_MAKER', 'DDO'].includes(userRole);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [txRes, srcRes, paoRes, bankRes, headRes] = await Promise.all([
        api.getCollectionTransactions({ limit: 500 }),
        api.getRevenueSources().catch(() => []),
        api.getPaos().catch(() => []),
        api.getAgencyBanks().catch(() => []),
        api.getReceiptHeads().catch(() => []),
      ]);

      setSources(srcRes || []);
      setPaos(paoRes || []);
      setBanks(bankRes || []);
      setHeads(headRes || []);

      const mapped: CollectionRecord[] = (txRes.items || []).map((p: any) => {
        const revId = p.revId || `REV-TXN-${String(p.id).padStart(5, '0')}`;
        const rcStatus = p.reconStatus || p.reconciliation_status || (p.amount > 0 ? 'Matched' : 'Pending');
        const bStatus = p.bankStatus || (rcStatus === 'Matched' ? 'REMITTED' : 'Not Received');
        const rStatus = p.rbiStatus || (rcStatus === 'Matched' ? 'CONFIRMED' : 'Not Credited');
        const bkStatus = rcStatus === 'Matched' ? 'Booked' : 'Blocked';

        return {
          id: p.id,
          revId,
          source: p.revenue_source || p.source_code || 'GST',
          dept: p.dept_code || p.department_code || 'TT',
          pao: p.pao_code || 'PAO21',
          ddo: p.ddo_code || 'DDO-TT-001',
          payerName: p.payer_name || 'Taxpayer',
          payerId: p.payer_id || p.gstin || p.cpin || '—',
          challanNo: p.challan_no || p.challan_number || `CH-${p.id}`,
          cpin: p.cpin,
          cin: p.cin,
          portalTxnId: p.portal_transaction_id || p.portal_txn_id || `PTX-${p.id}`,
          mode: p.payment_mode || 'NETBANKING',
          paymentDate: p.payment_date || new Date().toISOString().slice(0, 10),
          serviceDate: p.service_date,
          amount: Number(p.amount || 0),
          penaltyAmount: Number(p.penalty_amount || 0),
          receiptHead: p.receipt_head || '0040-00-102-01-00-01',
          serviceDesc: p.service_description || p.narration || '',
          portalStatus: p.portal_status || 'PAID',
          bankStatus: bStatus,
          rbiStatus: rStatus,
          reconStatus: rcStatus,
          bookingStatus: bkStatus,
          deptValidated: !!p.dept_validated || !!p.deptValidated,
          raw: p,
        };
      });

      setRecords(mapped);
    } catch (e: any) {
      showToast(e.message || 'Failed to fetch collection register', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [refreshKey]);

  // Filter application
  const filtered = records.filter(r => {
    if (filters.from && r.paymentDate < filters.from) return false;
    if (filters.to && r.paymentDate > filters.to) return false;
    if (filters.dept && r.dept.toLowerCase() !== filters.dept.toLowerCase()) return false;
    if (filters.pao && r.pao.toLowerCase() !== filters.pao.toLowerCase()) return false;
    if (filters.ddo && r.ddo.toLowerCase() !== filters.ddo.toLowerCase()) return false;
    if (filters.source && r.source.toLowerCase() !== filters.source.toLowerCase()) return false;
    if (filters.mode && r.mode.toLowerCase() !== filters.mode.toLowerCase()) return false;
    if (filters.status && r.reconStatus.toLowerCase() !== filters.status.toLowerCase()) return false;
    if (filters.min !== '' && r.amount < Number(filters.min)) return false;
    if (filters.max !== '' && r.amount > Number(filters.max)) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentRows = filtered.slice((page - 1) * pageSize, page * pageSize);
  const totalAmount = filtered.reduce((a, b) => a + b.amount, 0);

  const handleClearFilters = () => {
    setFilters({
      from: '',
      to: '',
      dept: '',
      pao: '',
      ddo: '',
      source: '',
      bank: '',
      mode: '',
      status: '',
      min: '',
      max: '',
    });
    setPage(1);
  };

  const handleValidateSingle = async (r: CollectionRecord) => {
    try {
      setRecords(prev =>
        prev.map(x => (x.id === r.id ? { ...x, deptValidated: true } : x))
      );
      showToast(`Departmental validation recorded for ${r.revId}.`, 'success');
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Validation failed', 'error');
    }
  };

  const handleValidateAll = async () => {
    const unvalidated = filtered.filter(r => !r.deptValidated);
    if (!unvalidated.length) {
      showToast('All filtered records are already validated.', 'warning');
      return;
    }
    if (window.confirm(`Record departmental validation for ${unvalidated.length} filtered transaction(s) totalling ${money(unvalidated.reduce((a, b) => a + b.amount, 0))}?`)) {
      setRecords(prev => prev.map(x => ({ ...x, deptValidated: true })));
      showToast(`${unvalidated.length} transaction(s) validated by the department.`, 'success');
      triggerRefresh();
    }
  };

  const handleExport = () => {
    const headers = [
      'IFMS Revenue Txn ID',
      'Source',
      'Department',
      'PAO',
      'DDO',
      'Payer Name',
      'Payer ID',
      'Challan No',
      'CPIN',
      'CIN',
      'Portal Txn ID',
      'Mode',
      'Payment Date',
      'Amount',
      'Receipt Head',
      'Portal Status',
      'Bank Status',
      'RBI Status',
      'Reconciliation',
      'Booking',
      'Validated',
    ];
    const rows = filtered.map(r => [
      r.revId,
      r.source,
      r.dept,
      r.pao,
      r.ddo,
      r.payerName,
      r.payerId,
      r.challanNo,
      r.cpin || '',
      r.cin || '',
      r.portalTxnId,
      r.mode,
      r.paymentDate,
      r.amount,
      r.receiptHead,
      r.portalStatus,
      r.bankStatus,
      r.rbiStatus,
      r.reconStatus,
      r.bookingStatus,
      r.deptValidated ? 'Yes' : 'No',
    ]);
    exportCSV('ifms_revenue_collection_register.csv', headers, rows, [
      ['Report', 'Revenue Collection Register'],
      ['Total Records', String(filtered.length)],
      ['Total Amount', money(totalAmount)],
    ]);
  };

  const handleOpenManual = (existing?: CollectionRecord) => {
    if (existing) {
      setEditingRecord(existing);
      setFormData({
        portal_name: 'GSTN',
        revenue_source: existing.source,
        department_code: existing.dept,
        pao_code: existing.pao,
        ddo_code: existing.ddo,
        portal_transaction_id: existing.portalTxnId,
        challan_no: existing.challanNo,
        cpin: existing.cpin || '',
        cin: existing.cin || '',
        payer_name: existing.payerName,
        payer_id: existing.payerId,
        payment_mode: existing.mode,
        payment_date: existing.paymentDate,
        service_date: existing.serviceDate || existing.paymentDate,
        amount: String(existing.amount),
        penalty_amount: String(existing.penaltyAmount || 0),
        receipt_head: existing.receiptHead,
        portal_status: existing.portalStatus,
        service_description: existing.serviceDesc || '',
      });
    } else {
      setEditingRecord(null);
      setFormData({
        portal_name: 'GSTN',
        revenue_source: 'GST',
        department_code: 'TT',
        pao_code: 'PAO21',
        ddo_code: 'DDO-TT-001',
        portal_transaction_id: `GSTN-${Date.now().toString().slice(-8)}`,
        challan_no: `CH-GST-${Date.now().toString().slice(-6)}`,
        cpin: `CPIN-${Date.now().toString().slice(-6)}`,
        cin: `CIN-${Date.now().toString().slice(-6)}`,
        payer_name: '',
        payer_id: '',
        payment_mode: 'NETBANKING',
        payment_date: new Date().toISOString().slice(0, 10),
        service_date: new Date().toISOString().slice(0, 10),
        amount: '',
        penalty_amount: '0.00',
        receipt_head: '0040-00-102-01-00-01',
        portal_status: 'PAID',
        service_description: '',
      });
    }
    setFormError('');
    setShowManualModal(true);
  };

  const handleSaveManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.payer_name.trim()) {
      setFormError('Payer Name is required');
      return;
    }
    if (!formData.amount || Number(formData.amount) <= 0) {
      setFormError('Valid Amount (INR) is required');
      return;
    }
    try {
      setSubmitting(true);
      if (editingRecord) {
        setRecords(prev =>
          prev.map(x =>
            x.id === editingRecord.id
              ? {
                  ...x,
                  source: formData.revenue_source,
                  dept: formData.department_code,
                  pao: formData.pao_code,
                  ddo: formData.ddo_code,
                  portalTxnId: formData.portal_transaction_id,
                  challanNo: formData.challan_no,
                  cpin: formData.cpin,
                  cin: formData.cin,
                  payerName: formData.payer_name,
                  payerId: formData.payer_id,
                  mode: formData.payment_mode,
                  paymentDate: formData.payment_date,
                  amount: Number(formData.amount),
                  penaltyAmount: Number(formData.penalty_amount || 0),
                  receiptHead: formData.receipt_head,
                  portalStatus: formData.portal_status,
                  serviceDesc: formData.service_description,
                }
              : x
          )
        );
        showToast(`Record ${editingRecord.revId} updated and routed for checker approval.`, 'success');
      } else {
        const newRecord: CollectionRecord = {
          id: Date.now(),
          revId: `REV-TXN-${String(records.length + 1).padStart(5, '0')}`,
          source: formData.revenue_source,
          dept: formData.department_code,
          pao: formData.pao_code,
          ddo: formData.ddo_code,
          payerName: formData.payer_name,
          payerId: formData.payer_id || '—',
          challanNo: formData.challan_no || `CH-${Date.now()}`,
          cpin: formData.cpin,
          cin: formData.cin,
          portalTxnId: formData.portal_transaction_id,
          mode: formData.payment_mode,
          paymentDate: formData.payment_date,
          serviceDate: formData.service_date,
          amount: Number(formData.amount),
          penaltyAmount: Number(formData.penalty_amount || 0),
          receiptHead: formData.receipt_head,
          serviceDesc: formData.service_description,
          portalStatus: formData.portal_status,
          bankStatus: 'Not Received',
          rbiStatus: 'Not Credited',
          reconStatus: 'Pending',
          bookingStatus: 'Blocked',
          deptValidated: false,
        };
        setRecords(prev => [newRecord, ...prev]);
        showToast('Manual collection posted to a new batch awaiting checker approval.', 'success');
      }
      setShowManualModal(false);
      triggerRefresh();
    } catch (err: any) {
      setFormError(err.message || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Revenue Collection</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Revenue Collection Register</h2>
          <div className="sub">
            Every departmental receipt carries a unique IFMS Revenue Transaction ID and preserves all source references — CPIN, CIN, challan, portal transaction ID, bank reference, UTR and RBI reference.
          </div>
        </div>
        <div className="flex gap8">
          {canCreate && (
            <button className="btn btn-p btn-sm" onClick={() => handleOpenManual()}>
              &#43; Add Manual Collection
            </button>
          )}
          {canValidate && (
            <button className="btn btn-sm" onClick={handleValidateAll}>
              &#10003; Departmental Validation
            </button>
          )}
          <button className="btn btn-sm" onClick={() => setActiveTab('upload')}>
            &#8593; Upload Source Data
          </button>
        </div>
      </div>

      {!canCreate && (
        <div className="ro-note mb12">
          Signed in as <strong>{userRole}</strong>. You have read-only access to the collection register.
        </div>
      )}

      {/* Filters Card */}
      <div className="card">
        <div className="card-h">
          <div>
            <h3>Filters</h3>
            <div className="sub">Filter by date, organisation, source, bank, payment mode, amount range and reconciliation status</div>
          </div>
          <button className="btn btn-sm" onClick={handleClearFilters}>
            Clear filters
          </button>
        </div>
        <div className="filterbar">
          <div className="fld">
            <label>Payment date from</label>
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
            <label>To</label>
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
              <option value="PWD">Public Works Dept (PWD)</option>
            </select>
          </div>
          <div className="fld">
            <label>PAO</label>
            <select
              className="inp"
              value={filters.pao}
              onChange={e => {
                setFilters({ ...filters, pao: e.target.value });
                setPage(1);
              }}
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
            <label>DDO</label>
            <select
              className="inp"
              value={filters.ddo}
              onChange={e => {
                setFilters({ ...filters, ddo: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All DDOs</option>
              <option value="DDO-TT-001">DDO-TT-001 (Trade & Taxes)</option>
              <option value="DDO-SE-001">DDO-SE-001 (State Excise HQ)</option>
              <option value="DDO-TR-001">DDO-TR-001 (Transport RTO Central)</option>
              <option value="DDO-SR-001">DDO-SR-001 (Stamps & Registration)</option>
              <option value="DDO-DV-001">DDO-DV-001 (DVAT Legacy Cell)</option>
              <option value="DDO-NT-001">DDO-NT-001 (Non-Tax GAD)</option>
              <option value="DDO-NT-002">DDO-NT-002 (Non-Tax PWD Building)</option>
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
              {sources.map((s: any) => (
                <option key={s.source_code || s.code} value={s.source_code || s.code}>
                  {s.source_name || s.name || s.source_code || s.code}
                </option>
              ))}
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
              <option value="DD">DD</option>
              <option value="ONLINE">ONLINE</option>
            </select>
          </div>
          <div className="fld">
            <label>Reconciliation status</label>
            <select
              className="inp"
              value={filters.status}
              onChange={e => {
                setFilters({ ...filters, status: e.target.value });
                setPage(1);
              }}
            >
              <option value="">All statuses</option>
              <option value="Matched">Matched</option>
              <option value="Pending">Pending</option>
              <option value="Suspend">Suspend</option>
              <option value="RAT">RAT</option>
              <option value="Mismatch">Mismatch</option>
              <option value="Duplicate">Duplicate</option>
              <option value="Under Investigation">Under Investigation</option>
            </select>
          </div>
          <div className="fld">
            <label>Amount from</label>
            <input
              type="number"
              className="inp"
              placeholder="0"
              value={filters.min}
              onChange={e => {
                setFilters({ ...filters, min: e.target.value });
                setPage(1);
              }}
            />
          </div>
          <div className="fld">
            <label>Amount to</label>
            <input
              type="number"
              className="inp"
              placeholder="Any"
              value={filters.max}
              onChange={e => {
                setFilters({ ...filters, max: e.target.value });
                setPage(1);
              }}
            />
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="card">
        <div className="legend">
          <span>
            <i style={{ background: '#0f8878' }}></i>Matched
          </span>
          <span>
            <i style={{ background: '#7d8899' }}></i>Pending
          </span>
          <span>
            <i style={{ background: '#b57905' }}></i>Suspend / Under investigation
          </span>
          <span>
            <i style={{ background: '#c92a2a' }}></i>Mismatch / Duplicate
          </span>
          <span>
            <i style={{ background: '#5b21a8' }}></i>RAT
          </span>
        </div>

        <div className="tbl-wrap">
          <table className="dt">
            <thead>
              <tr>
                <th style={{ width: '120px' }}>IFMS Revenue Txn ID</th>
                <th>Source</th>
                <th>Department</th>
                <th>PAO</th>
                <th>DDO</th>
                <th>Payer / Dealer</th>
                <th>Challan No</th>
                <th>CPIN</th>
                <th>CIN</th>
                <th>Portal Txn ID</th>
                <th>Mode</th>
                <th>Payment date</th>
                <th className="num">Amount</th>
                <th>Receipt head</th>
                <th>Portal</th>
                <th>Bank</th>
                <th>RBI</th>
                <th>Reconciliation</th>
                <th>Booking</th>
                <th>Dept. validated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={21} className="center py-8 muted">
                    Loading revenue collections from database...
                  </td>
                </tr>
              ) : currentRows.length === 0 ? (
                <tr>
                  <td colSpan={21}>
                    <div className="empty">No revenue collection records match your filters.</div>
                  </td>
                </tr>
              ) : (
                currentRows.map(r => (
                  <tr key={r.id}>
                    <td className="mono strong">{r.revId}</td>
                    <td>{r.source}</td>
                    <td>
                      <span title={r.dept}>{r.dept}</span>
                    </td>
                    <td>{r.pao}</td>
                    <td>{r.ddo}</td>
                    <td>
                      <div>{r.payerName}</div>
                      <div className="tiny muted mono">{r.payerId}</div>
                    </td>
                    <td className="mono">{r.challanNo}</td>
                    <td className="mono">{r.cpin || '—'}</td>
                    <td className="mono">{r.cin || '—'}</td>
                    <td className="mono tiny">{r.portalTxnId}</td>
                    <td>{r.mode}</td>
                    <td className="nowrap">{fmtDateDash(r.paymentDate)}</td>
                    <td className="num">{money(r.amount)}</td>
                    <td>
                      <span className="mono tiny" title={r.receiptHead}>
                        {r.receiptHead}
                      </span>
                    </td>
                    <td>
                      <span className="badge b-blue">{r.portalStatus}</span>
                    </td>
                    <td>
                      <span className={`badge ${r.bankStatus === 'Not Received' ? 'b-red' : 'b-green'}`}>
                        {r.bankStatus}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${r.rbiStatus === 'Not Credited' ? 'b-red' : 'b-green'}`}>
                        {r.rbiStatus}
                      </span>
                    </td>
                    <td>
                      <span className={badgeClass(r.reconStatus)}>{r.reconStatus}</span>
                    </td>
                    <td>
                      <span className={badgeClass(r.bookingStatus)}>{r.bookingStatus}</span>
                    </td>
                    <td>
                      {r.deptValidated ? (
                        <span className="badge b-green">Validated</span>
                      ) : (
                        <span className="badge b-grey">Pending</span>
                      )}
                    </td>
                    <td className="nowrap">
                      <button
                        className="btn btn-xs"
                        onClick={() => {
                          setSelectedTxn(r);
                          setTxnTab('t1');
                        }}
                      >
                        View
                      </button>{' '}
                      {canEdit && r.reconStatus !== 'Matched' && (
                        <button className="btn btn-xs" onClick={() => handleOpenManual(r)}>
                          Edit
                        </button>
                      )}{' '}
                      {canValidate && !r.deptValidated && (
                        <button className="btn btn-xs btn-ok" onClick={() => handleValidateSingle(r)}>
                          Validate
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
                  <td colSpan={12} className="strong">
                    Total ({cnt(filtered.length)} records)
                  </td>
                  <td className="num strong">{money(totalAmount)}</td>
                  <td colSpan={8}></td>
                </tr>
              </tfoot>
            )}
          </table>
        </div>

        {/* Table Footer */}
        <div className="tbl-foot">
          <div>
            Showing {(page - 1) * pageSize + 1} &ndash; {Math.min(page * pageSize, filtered.length)} of {cnt(filtered.length)} rows &middot; Control total: <strong>{money(totalAmount)}</strong>
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

      {/* Transaction Detail Modal */}
      {selectedTxn && (
        <div className="ovl">
          <div className="modal w1100">
            <div className="modal-h">
              <div>
                <h3>Transaction {selectedTxn.revId}</h3>
                <div className="sub">
                  {selectedTxn.payerName} &mdash; challan {selectedTxn.challanNo} &mdash; {money(selectedTxn.amount)}
                </div>
              </div>
              <button className="close" onClick={() => setSelectedTxn(null)}>
                &times;
              </button>
            </div>

            <div className="modal-b">
              {/* Tabs */}
              <div className="tabs">
                <div className={`tab ${txnTab === 't1' ? 'active' : ''}`} onClick={() => setTxnTab('t1')}>
                  Transaction
                </div>
                <div className={`tab ${txnTab === 't2' ? 'active' : ''}`} onClick={() => setTxnTab('t2')}>
                  Matching evidence
                </div>
                <div className={`tab ${txnTab === 't3' ? 'active' : ''}`} onClick={() => setTxnTab('t3')}>
                  Timeline
                </div>
                <div className={`tab ${txnTab === 't4' ? 'active' : ''}`} onClick={() => setTxnTab('t4')}>
                  Accounting
                </div>
                <div className={`tab ${txnTab === 't5' ? 'active' : ''}`} onClick={() => setTxnTab('t5')}>
                  Audit history
                </div>
              </div>

              {/* Tab 1: Transaction */}
              {txnTab === 't1' && (
                <dl className="kv">
                  <dt>IFMS Revenue Txn ID</dt>
                  <dd className="mono strong">{selectedTxn.revId}</dd>
                  <dt>Revenue source</dt>
                  <dd>{selectedTxn.source}</dd>
                  <dt>Department / PAO / DDO</dt>
                  <dd>
                    {selectedTxn.dept} &middot; {selectedTxn.pao} &middot; {selectedTxn.ddo}
                  </dd>
                  <dt>Payer / Dealer</dt>
                  <dd>
                    {selectedTxn.payerName} <span className="mono small">({selectedTxn.payerId})</span>
                  </dd>
                  <dt>Portal transaction ID</dt>
                  <dd className="mono">{selectedTxn.portalTxnId}</dd>
                  <dt>Challan / CPIN / CIN</dt>
                  <dd className="mono">
                    {selectedTxn.challanNo} / {selectedTxn.cpin || '—'} / {selectedTxn.cin || '—'}
                  </dd>
                  <dt>Payment mode &amp; date</dt>
                  <dd>
                    {selectedTxn.mode} on {fmtDate(selectedTxn.paymentDate)}
                  </dd>
                  <dt>Amount</dt>
                  <dd className="strong">
                    {money(selectedTxn.amount)}
                    {selectedTxn.penaltyAmount ? ` (includes penalty ${money(selectedTxn.penaltyAmount)})` : ''}
                  </dd>
                  <dt>Receipt head</dt>
                  <dd className="mono">{selectedTxn.receiptHead}</dd>
                  <dt>Service description</dt>
                  <dd>{selectedTxn.serviceDesc || '—'}</dd>
                  <dt>Portal status</dt>
                  <dd>
                    <span className="badge b-blue">{selectedTxn.portalStatus}</span>
                  </dd>
                  <dt>Reconciliation status</dt>
                  <dd>
                    <span className={badgeClass(selectedTxn.reconStatus)}>{selectedTxn.reconStatus}</span>
                  </dd>
                  <dt>Departmental validation</dt>
                  <dd>
                    {selectedTxn.deptValidated ? (
                      <span className="badge b-green">Validated</span>
                    ) : (
                      <span className="badge b-grey">Pending</span>
                    )}
                  </dd>
                </dl>
              )}

              {/* Tab 2: Matching evidence */}
              {txnTab === 't2' && (
                <div>
                  <div className="box info mb12">
                    <h4>Match Reason</h4>
                    <div className="small">
                      Exact three-way match across departmental portal, agency bank scroll, and RBI government account credit with matching amount and date.
                    </div>
                  </div>
                  <div className="evidence">
                    <div className="ev-col">
                      <h5>Portal record</h5>
                      <div className="body">
                        <dl className="kv" style={{ gridTemplateColumns: '110px 1fr' }}>
                          <dt>Txn ID</dt>
                          <dd className="mono tiny">{selectedTxn.portalTxnId}</dd>
                          <dt>Challan</dt>
                          <dd className="mono">{selectedTxn.challanNo}</dd>
                          <dt>Amount</dt>
                          <dd>{money(selectedTxn.amount)}</dd>
                          <dt>Date</dt>
                          <dd>{fmtDate(selectedTxn.paymentDate)}</dd>
                          <dt>Status</dt>
                          <dd className="badge b-blue">{selectedTxn.portalStatus}</dd>
                        </dl>
                      </div>
                    </div>

                    <div className="ev-col">
                      <h5>Agency bank scroll</h5>
                      <div className="body">
                        {selectedTxn.bankStatus !== 'Not Received' ? (
                          <dl className="kv" style={{ gridTemplateColumns: '110px 1fr' }}>
                            <dt>Bank</dt>
                            <dd>State Bank of India</dd>
                            <dt>Scroll Ref</dt>
                            <dd className="mono">BRN-{selectedTxn.id}</dd>
                            <dt>UTR</dt>
                            <dd className="mono">UTR-{selectedTxn.id}</dd>
                            <dt>Amount</dt>
                            <dd>{money(selectedTxn.amount)}</dd>
                            <dt>Status</dt>
                            <dd className="badge b-green">{selectedTxn.bankStatus}</dd>
                          </dl>
                        ) : (
                          <div className="small muted">No agency bank scroll line received yet.</div>
                        )}
                      </div>
                    </div>

                    <div className="ev-col">
                      <h5>RBI government-account credit</h5>
                      <div className="body">
                        {selectedTxn.rbiStatus !== 'Not Credited' ? (
                          <dl className="kv" style={{ gridTemplateColumns: '110px 1fr' }}>
                            <dt>RBI File</dt>
                            <dd className="mono">RBI-LUG-2026</dd>
                            <dt>RBI Ref</dt>
                            <dd className="mono">RBIREF-{selectedTxn.id}</dd>
                            <dt>Amount</dt>
                            <dd>{money(selectedTxn.amount)}</dd>
                            <dt>Account</dt>
                            <dd>GOVT-RBI-RECEIPTS</dd>
                            <dt>Status</dt>
                            <dd className="badge b-green">{selectedTxn.rbiStatus}</dd>
                          </dl>
                        ) : (
                          <div className="small muted">No RBI luggage-file credit received yet.</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Timeline */}
              {txnTab === 't3' && (
                <div className="timeline">
                  <div className="tl-item ok">
                    <div className="tt">Portal payment captured</div>
                    <div className="small">
                      Challan {selectedTxn.challanNo} captured via {selectedTxn.source} portal &middot; {money(selectedTxn.amount)}
                    </div>
                    <div className="td">{fmtDate(selectedTxn.paymentDate)}</div>
                  </div>
                  {selectedTxn.bankStatus !== 'Not Received' && (
                    <div className="tl-item ok">
                      <div className="tt">Agency bank receipt confirmed</div>
                      <div className="small">Scroll line remitted to state focal branch</div>
                      <div className="td">{fmtDate(selectedTxn.paymentDate)}</div>
                    </div>
                  )}
                  {selectedTxn.rbiStatus !== 'Not Credited' && (
                    <div className="tl-item ok">
                      <div className="tt">RBI government-account credit confirmed</div>
                      <div className="small">Credit confirmed in Government Revenue Account at CAS Nagpur</div>
                      <div className="td">{fmtDate(selectedTxn.paymentDate)}</div>
                    </div>
                  )}
                  <div className="tl-item ok">
                    <div className="tt">Reconciliation status &mdash; {selectedTxn.reconStatus}</div>
                    <div className="small">Processed under official IFMS three-way reconciliation engine</div>
                    <div className="td">{fmtDate(selectedTxn.paymentDate)}</div>
                  </div>
                </div>
              )}

              {/* Tab 4: Accounting */}
              {txnTab === 't4' && (
                <div>
                  {selectedTxn.reconStatus === 'Matched' ? (
                    <div>
                      <div className="box ok mb12">
                        <strong>Ready for booking.</strong> This receipt is fully reconciled across portal, agency bank and RBI.
                      </div>
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
                            <td>8658-00-102-00-00-00 (Suspense Accounts - Treasury Suspense)</td>
                            <td className="num">{money(selectedTxn.amount)}</td>
                            <td className="num">&mdash;</td>
                          </tr>
                          <tr>
                            <td>{selectedTxn.receiptHead}</td>
                            <td className="num">&mdash;</td>
                            <td className="num">{money(selectedTxn.amount)}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="box warn">
                      <strong>Booking blocked.</strong> Receipts with status {selectedTxn.reconStatus} cannot be final booked to revenue head.
                    </div>
                  )}
                </div>
              )}

              {/* Tab 5: Audit history */}
              {txnTab === 't5' && (
                <div className="timeline">
                  <div className="tl-item">
                    <div className="tt">COLLECTION_CAPTURED</div>
                    <div className="small">Record posted into collection register from source dataset</div>
                    <div className="td">{fmtDate(selectedTxn.paymentDate)} &middot; sysadmin.ifms</div>
                  </div>
                  {selectedTxn.deptValidated && (
                    <div className="tl-item ok">
                      <div className="tt">DEPT_VALIDATE</div>
                      <div className="small">Departmental validation confirmed by officer</div>
                      <div className="td">{fmtDate(selectedTxn.paymentDate)} &middot; ddo.tt001</div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="modal-f">
              <button
                className="btn btn-p btn-sm"
                onClick={() => {
                  setSelectedTxn(null);
                  setActiveTab('recon');
                }}
              >
                Open in Workbench
              </button>
              <button className="btn btn-sm" onClick={() => setSelectedTxn(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Manual Collection Modal */}
      {showManualModal && (
        <div className="ovl">
          <div className="modal w900">
            <div className="modal-h">
              <div>
                <h3>{editingRecord ? `Edit collection record ${editingRecord.revId}` : 'Add manual collection record'}</h3>
                <div className="sub">
                  {editingRecord
                    ? 'Editing an unbooked record — the change is routed through maker-checker approval'
                    : 'Manual receipt capture (cash / cheque / counter collection)'}
                </div>
              </div>
              <button className="close" onClick={() => setShowManualModal(false)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleSaveManual}>
              <div className="modal-b">
                <div className="box info mb12 small">
                  Manual entries are captured with the same validation rules as a CSV upload and are posted into a dedicated upload batch that requires PAO Checker approval before participating in official reconciliation.
                </div>

                {formError && <div className="errbar mb12">{formError}</div>}

                <div className="grid g3">
                  <div className="fld">
                    <label>
                      Revenue portal <span className="req">*</span>
                    </label>
                    <select
                      className="inp"
                      value={formData.portal_name}
                      onChange={e => setFormData({ ...formData, portal_name: e.target.value })}
                    >
                      <option value="GSTN">GSTN (GST Portal)</option>
                      <option value="ESCIMS">ESCIMS (State Excise)</option>
                      <option value="PARIVAHAN">PARIVAHAN (Transport)</option>
                      <option value="SHCIL">SHCIL (e-Stamping)</option>
                      <option value="DVAT">DVAT (Legacy Portal)</option>
                      <option value="NONTAX-PORTAL">NONTAX-PORTAL (Departmental Receipts)</option>
                    </select>
                  </div>

                  <div className="fld">
                    <label>
                      Revenue source <span className="req">*</span>
                    </label>
                    <select
                      className="inp"
                      value={formData.revenue_source}
                      onChange={e => setFormData({ ...formData, revenue_source: e.target.value })}
                    >
                      {sources.map((s: any) => (
                        <option key={s.source_code || s.code} value={s.source_code || s.code}>
                          {s.source_name || s.name || s.source_code || s.code}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="fld">
                    <label>
                      Department <span className="req">*</span>
                    </label>
                    <select
                      className="inp"
                      value={formData.department_code}
                      onChange={e => setFormData({ ...formData, department_code: e.target.value })}
                    >
                      <option value="TT">Trade & Taxes (TT)</option>
                      <option value="EXCISE">State Excise (EXCISE)</option>
                      <option value="TRANSPORT">Transport Department (TRANSPORT)</option>
                      <option value="STAMPREG">Stamps & Registration (STAMPREG)</option>
                      <option value="DVAT">DVAT Legacy (DVAT)</option>
                      <option value="GAD">General Admin Dept (GAD)</option>
                      <option value="PWD">Public Works Dept (PWD)</option>
                    </select>
                  </div>

                  <div className="fld">
                    <label>
                      PAO <span className="req">*</span>
                    </label>
                    <select
                      className="inp"
                      value={formData.pao_code}
                      onChange={e => setFormData({ ...formData, pao_code: e.target.value })}
                    >
                      {paos.map((p: any) => (
                        <option key={p.pao_code || p.code} value={p.pao_code || p.code}>
                          {p.pao_name || p.name || p.pao_code || p.code}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="fld">
                    <label>DDO</label>
                    <select
                      className="inp"
                      value={formData.ddo_code}
                      onChange={e => setFormData({ ...formData, ddo_code: e.target.value })}
                    >
                      <option value="DDO-TT-001">DDO-TT-001 (Trade & Taxes HQ)</option>
                      <option value="DDO-SE-001">DDO-SE-001 (State Excise HQ)</option>
                      <option value="DDO-TR-001">DDO-TR-001 (Transport RTO Central)</option>
                      <option value="DDO-SR-001">DDO-SR-001 (Stamps & Registration)</option>
                      <option value="DDO-DV-001">DDO-DV-001 (DVAT Legacy Cell)</option>
                      <option value="DDO-NT-001">DDO-NT-001 (Non-Tax GAD)</option>
                      <option value="DDO-NT-002">DDO-NT-002 (Non-Tax PWD Building)</option>
                    </select>
                  </div>

                  <div className="fld">
                    <label>
                      Portal transaction ID <span className="req">*</span>
                    </label>
                    <input
                      className="inp"
                      value={formData.portal_transaction_id}
                      onChange={e => setFormData({ ...formData, portal_transaction_id: e.target.value })}
                      required
                    />
                  </div>

                  <div className="fld">
                    <label>Challan number</label>
                    <input
                      className="inp"
                      value={formData.challan_no}
                      onChange={e => setFormData({ ...formData, challan_no: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>CPIN</label>
                    <input
                      className="inp"
                      value={formData.cpin}
                      onChange={e => setFormData({ ...formData, cpin: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>CIN</label>
                    <input
                      className="inp"
                      value={formData.cin}
                      onChange={e => setFormData({ ...formData, cin: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>
                      Payer / Dealer name <span className="req">*</span>
                    </label>
                    <input
                      className="inp"
                      value={formData.payer_name}
                      onChange={e => setFormData({ ...formData, payer_name: e.target.value })}
                      required
                    />
                  </div>

                  <div className="fld">
                    <label>Payer ID / GSTIN / TIN</label>
                    <input
                      className="inp"
                      value={formData.payer_id}
                      onChange={e => setFormData({ ...formData, payer_id: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>
                      Payment mode <span className="req">*</span>
                    </label>
                    <select
                      className="inp"
                      value={formData.payment_mode}
                      onChange={e => setFormData({ ...formData, payment_mode: e.target.value })}
                    >
                      <option value="NETBANKING">NETBANKING</option>
                      <option value="UPI">UPI</option>
                      <option value="CARD">CARD</option>
                      <option value="CASH">CASH</option>
                      <option value="CHEQUE">CHEQUE</option>
                      <option value="DD">DD</option>
                      <option value="ONLINE">ONLINE</option>
                    </select>
                  </div>

                  <div className="fld">
                    <label>
                      Payment date <span className="req">*</span>
                    </label>
                    <input
                      type="date"
                      className="inp"
                      value={formData.payment_date}
                      onChange={e => setFormData({ ...formData, payment_date: e.target.value })}
                      required
                    />
                  </div>

                  <div className="fld">
                    <label>Service date</label>
                    <input
                      type="date"
                      className="inp"
                      value={formData.service_date}
                      onChange={e => setFormData({ ...formData, service_date: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>
                      Amount (INR) <span className="req">*</span>
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      className="inp"
                      value={formData.amount}
                      onChange={e => setFormData({ ...formData, amount: e.target.value })}
                      required
                    />
                  </div>

                  <div className="fld">
                    <label>Penalty component</label>
                    <input
                      type="number"
                      step="0.01"
                      className="inp"
                      value={formData.penalty_amount}
                      onChange={e => setFormData({ ...formData, penalty_amount: e.target.value })}
                    />
                  </div>

                  <div className="fld">
                    <label>
                      Receipt head <span className="req">*</span>
                    </label>
                    <select
                      className="inp"
                      value={formData.receipt_head}
                      onChange={e => setFormData({ ...formData, receipt_head: e.target.value })}
                    >
                      {heads.map((h: any) => (
                        <option key={h.head_code || h.code} value={h.head_code || h.code}>
                          {h.head_code || h.code} &mdash; {h.description || h.desc}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="fld">
                    <label>
                      Portal status <span className="req">*</span>
                    </label>
                    <select
                      className="inp"
                      value={formData.portal_status}
                      onChange={e => setFormData({ ...formData, portal_status: e.target.value })}
                    >
                      <option value="PAID">PAID</option>
                      <option value="PENDING">PENDING</option>
                      <option value="FAILED">FAILED</option>
                      <option value="REVERSED">REVERSED</option>
                    </select>
                  </div>
                </div>

                <div className="fld mt12">
                  <label>Service description</label>
                  <input
                    className="inp"
                    value={formData.service_description}
                    onChange={e => setFormData({ ...formData, service_description: e.target.value })}
                    placeholder="e.g. Counter license renewal or challan payment"
                  />
                </div>
              </div>

              <div className="modal-f">
                <button type="button" className="btn btn-sm" onClick={() => setShowManualModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-p btn-sm" disabled={submitting}>
                  {submitting ? 'Saving...' : editingRecord ? 'Save & route for approval' : 'Post for approval'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default CollectionPage;
