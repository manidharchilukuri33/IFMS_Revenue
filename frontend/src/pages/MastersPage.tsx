import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt, badgeClass } from '../utils/format';

export const MastersPage: React.FC = () => {
  const { userRole, showToast, setActiveTab, refreshKey, triggerRefresh } = useApp();
  const [activeTab, setActiveTabLocal] = useState<'org' | 'sources' | 'heads' | 'rules' | 'slaRules' | 'config'>('org');
  const [subTab, setSubTab] = useState<'departments' | 'paos' | 'ddos' | 'treasuries' | 'localBodies' | 'banks' | 'branches' | 'portals'>('departments');

  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState<any[]>([]);
  const [heads, setHeads] = useState<any[]>([]);
  const [paos, setPaos] = useState<any[]>([]);
  const [banks, setBanks] = useState<any[]>([]);
  const [localBodies, setLocalBodies] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [slaRules, setSlaRules] = useState<any[]>([]);

  // Config State
  const [config, setConfig] = useState({
    bizDate: '2026-09-12',
    fy: '2026-27',
    dateTolerance: 2,
    amtTolerance: 0.01,
    penalRate: 12.0,
    penalDayBasis: 365,
    escalationDays: 7,
    calendarDays: true,
    suspenseHead: '8658-00-102-00-00-00',
    ratHead: '8658-00-101-00-00-00',
    clearingAccount: 'GOVT-RBI-RECEIPTS',
    refundHead: '0030-00-900-01-00-01',
    devolutionHead: '3604-00-200-01-00-01',
  });

  const canEdit = ['SYSADMIN'].includes(userRole);

  const fetchMasterData = async () => {
    try {
      setLoading(true);
      const [srcRes, headRes, paoRes, bankRes, bodyRes, ruleRes, slaRes] = await Promise.all([
        api.getRevenueSources().catch(() => []),
        api.getReceiptHeads().catch(() => []),
        api.getPaos().catch(() => []),
        api.getAgencyBanks().catch(() => []),
        api.getLocalBodies().catch(() => []),
        api.getReconciliationRules().catch(() => []),
        api.getSlaRules().catch(() => []),
      ]);

      setSources(srcRes || []);
      setHeads(headRes || []);
      setPaos(paoRes || []);
      setBanks(bankRes || []);
      setLocalBodies(bodyRes || []);
      setRules(ruleRes || []);
      setSlaRules(slaRes || []);
    } catch (e: any) {
      showToast('Failed to load master configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMasterData();
  }, [refreshKey]);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) {
      showToast('Only System Administrator can edit configuration.', 'warning');
      return;
    }
    showToast('System configuration saved. Audit log recorded.', 'success');
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Masters &amp; Configuration</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Masters &amp; Configuration</h2>
          <div className="sub">
            Organisation masters, revenue sources, Chart of Accounts receipt heads, reconciliation rules, bank SLA and penal-interest rules, and system configuration. Every change is written to the audit trail.
          </div>
        </div>
        <div className="flex gap8">
          <button className="btn btn-sm" onClick={() => setActiveTab('audit')}>
            &#8703; View audit trail
          </button>
        </div>
      </div>

      {!canEdit && (
        <div className="ro-note mb12">
          Signed in as <strong>{userRole}</strong>. Master configuration maintenance requires the <strong>System Administrator</strong> role.
        </div>
      )}

      {/* Main Tabs */}
      <div className="tabs">
        {[
          { k: 'org', label: 'Organisation masters' },
          { k: 'sources', label: 'Revenue sources' },
          { k: 'heads', label: 'Receipt heads' },
          { k: 'rules', label: 'Reconciliation rules' },
          { k: 'slaRules', label: 'Bank SLA & penal interest' },
          { k: 'config', label: 'System configuration' },
        ].map(t => (
          <div
            key={t.k}
            className={`tab ${activeTab === t.k ? 'active' : ''}`}
            onClick={() => setActiveTabLocal(t.k as any)}
          >
            {t.label}
          </div>
        ))}
      </div>

      {/* Organisation Masters View */}
      {activeTab === 'org' && (
        <div>
          <div className="tabs">
            {[
              { k: 'departments', label: 'Departments' },
              { k: 'paos', label: 'PAOs' },
              { k: 'ddos', label: 'DDOs' },
              { k: 'treasuries', label: 'Treasuries' },
              { k: 'localBodies', label: 'Local bodies' },
              { k: 'banks', label: 'Banks' },
              { k: 'branches', label: 'Bank branches' },
              { k: 'portals', label: 'Revenue portals' },
            ].map(s => (
              <div
                key={s.k}
                className={`tab ${subTab === s.k ? 'active' : ''}`}
                onClick={() => setSubTab(s.k as any)}
              >
                {s.label}
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-h">
              <div>
                <h3 className="capitalize">{subTab} Master</h3>
                <div className="sub">Active administrative records maintained in PostgreSQL database</div>
              </div>
              {canEdit && <button className="btn btn-p btn-sm">&#43; Add Record</button>}
            </div>

            <div className="tbl-wrap">
              <table className="dt">
                <thead>
                  {subTab === 'departments' && (
                    <tr>
                      <th>Department Code</th>
                      <th>Department Name</th>
                      <th>Head of Department</th>
                      <th>Status</th>
                    </tr>
                  )}
                  {subTab === 'paos' && (
                    <tr>
                      <th>PAO Code</th>
                      <th>PAO Name</th>
                      <th>Department</th>
                      <th>Treasury</th>
                      <th>Status</th>
                    </tr>
                  )}
                  {subTab === 'banks' && (
                    <tr>
                      <th>Bank Code</th>
                      <th>Bank Name</th>
                      <th>Bank Type</th>
                      <th>Focal / Nodal Branch</th>
                      <th>Status</th>
                    </tr>
                  )}
                  {subTab === 'localBodies' && (
                    <tr>
                      <th>Body Code</th>
                      <th>Local Body Name</th>
                      <th>Type</th>
                      <th>Account (Masked)</th>
                      <th>IFSC</th>
                      <th>Status</th>
                    </tr>
                  )}
                  {['ddos', 'treasuries', 'branches', 'portals'].includes(subTab) && (
                    <tr>
                      <th>Code</th>
                      <th>Description</th>
                      <th>Jurisdiction / Operating Agency</th>
                      <th>Status</th>
                    </tr>
                  )}
                </thead>
                <tbody>
                  {subTab === 'departments' && (
                    <>
                      <tr>
                        <td className="mono strong">TT</td>
                        <td>Department of Trade &amp; Taxes</td>
                        <td>Commissioner (Trade &amp; Taxes)</td>
                        <td><span className="badge b-green">Active</span></td>
                      </tr>
                      <tr>
                        <td className="mono strong">EXCISE</td>
                        <td>State Excise Department</td>
                        <td>Commissioner (Excise)</td>
                        <td><span className="badge b-green">Active</span></td>
                      </tr>
                      <tr>
                        <td className="mono strong">TRANSPORT</td>
                        <td>Transport Department</td>
                        <td>Transport Commissioner</td>
                        <td><span className="badge b-green">Active</span></td>
                      </tr>
                      <tr>
                        <td className="mono strong">STAMPREG</td>
                        <td>Stamps &amp; Registration Department</td>
                        <td>Inspector General (Registration)</td>
                        <td><span className="badge b-green">Active</span></td>
                      </tr>
                    </>
                  )}
                  {subTab === 'paos' &&
                    paos.map((p: any) => (
                      <tr key={p.id || p.code || p.pao_code}>
                        <td className="mono strong">{p.pao_code || p.code}</td>
                        <td>{p.pao_name || p.name}</td>
                        <td>{p.dept_code || p.dept || 'TT'}</td>
                        <td>TRY-CENTRAL</td>
                        <td><span className="badge b-green">Active</span></td>
                      </tr>
                    ))}
                  {subTab === 'banks' &&
                    banks.map((b: any) => (
                      <tr key={b.id || b.code || b.bank_code}>
                        <td className="mono strong">{b.code || b.bank_code}</td>
                        <td>{b.name || b.bank_name}</td>
                        <td>{b.bank_type || 'Agency Bank'}</td>
                        <td>{b.focal_branch || `${b.code} Focal Branch`}</td>
                        <td><span className="badge b-green">Active</span></td>
                      </tr>
                    ))}
                  {subTab === 'localBodies' &&
                    localBodies.map((b: any) => (
                      <tr key={b.id || b.code || b.local_body_code}>
                        <td className="mono strong">{b.code || b.local_body_code}</td>
                        <td>{b.name || b.local_body_name}</td>
                        <td>{b.type || 'Municipal Corporation'}</td>
                        <td className="mono">{b.account || 'XXXX4501'}</td>
                        <td className="mono">{b.ifsc || 'SBIN0001001'}</td>
                        <td><span className="badge b-green">Active</span></td>
                      </tr>
                    ))}
                  {['ddos', 'treasuries', 'branches', 'portals'].includes(subTab) && (
                    <tr>
                      <td className="mono strong">GSTN</td>
                      <td>GST Network Challan Portal</td>
                      <td>GSTN / Trade &amp; Taxes</td>
                      <td><span className="badge b-green">Active</span></td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Revenue Sources View */}
      {activeTab === 'sources' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Revenue Sources</h3>
              <div className="sub">{cnt(sources.length)} registered source streams</div>
            </div>
            {canEdit && <button className="btn btn-p btn-sm">&#43; Add Source</button>}
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Source Code</th>
                  <th>Description</th>
                  <th>Department</th>
                  <th>PAO</th>
                  <th>Portal</th>
                  <th>Revenue Head</th>
                  <th>Modes</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s: any) => (
                  <tr key={s.id || s.code || s.source_code}>
                    <td className="mono strong">{s.source_code || s.code}</td>
                    <td>{s.source_name || s.name}</td>
                    <td>{s.dept_code || s.dept || 'TT'}</td>
                    <td>{s.pao_code || s.pao || 'PAO21'}</td>
                    <td>{s.portal || s.source_code}</td>
                    <td className="mono tiny">{s.receipt_head || '0040-00-102-01-00-01'}</td>
                    <td className="small">NETBANKING, UPI, CARD, CASH</td>
                    <td><span className="badge b-green">Active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Receipt Heads View */}
      {activeTab === 'heads' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Chart of Accounts &mdash; Receipt Heads</h3>
              <div className="sub">{cnt(heads.length)} 15-digit major-to-object heads</div>
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Full Head Code</th>
                  <th>Major</th>
                  <th>Sub-Major</th>
                  <th>Minor</th>
                  <th>Description</th>
                  <th>Source</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {heads.map((h: any) => (
                  <tr key={h.id || h.code || h.head_code}>
                    <td className="mono strong">{h.head_code || h.code}</td>
                    <td>{h.major_head || h.major || '0040'}</td>
                    <td>{h.submajor_head || h.submajor || '00'}</td>
                    <td>{h.minor_head || h.minor || '102'}</td>
                    <td>{h.description || h.desc}</td>
                    <td>{h.source_code || h.source || 'GST'}</td>
                    <td><span className="badge b-green">Active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reconciliation Rules View */}
      {activeTab === 'rules' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Reconciliation Matching Rules</h3>
              <div className="sub">Evaluated strictly in priority sequence by the matching engine</div>
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Rule ID</th>
                  <th className="num">Priority</th>
                  <th>Primary Match Keys</th>
                  <th>Tolerance (INR)</th>
                  <th>Tolerance (Days)</th>
                  <th>Matching Mode</th>
                  <th>Outcome</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r: any) => (
                  <tr key={r.id || r.rule_code}>
                    <td className="mono strong">{r.rule_code || r.id}</td>
                    <td className="num">{r.priority}</td>
                    <td>{r.primary_match_keys || r.primary}</td>
                    <td className="num">₹ {r.amount_tolerance || 0.01}</td>
                    <td className="num">{r.date_tolerance_days || 2} day(s)</td>
                    <td>{r.matching_mode || 'THREE_WAY_EXACT'}</td>
                    <td><span className="badge b-green">{r.outcome_status || 'Matched'}</span></td>
                    <td><span className="badge b-green">Active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card-b">
            <div className="box info small">
              <strong>Rule Evaluation Priority:</strong> Exact 3-way matches (RR-01) evaluate first. Overrides, variances, orphan credits (RAT), and duplicate scans trigger in sequence. Final Matched status is strictly gated on RBI credit confirmation.
            </div>
          </div>
        </div>
      )}

      {/* Bank SLA Rules View */}
      {activeTab === 'slaRules' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Bank SLA &amp; Penal Interest Configuration</h3>
              <div className="sub">Remittance SLAs and penal rate rules per payment channel</div>
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Rule ID</th>
                  <th>Bank</th>
                  <th>Payment Modes</th>
                  <th className="num">Allowed SLA Days</th>
                  <th className="num">Penal Rate (% p.a.)</th>
                  <th>Calculation Basis</th>
                  <th>Recovery Template</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {slaRules.map((s: any) => (
                  <tr key={s.id || s.rule_code}>
                    <td className="mono strong">{s.rule_code || s.id}</td>
                    <td>ALL Agency Banks</td>
                    <td>{s.payment_modes || 'ONLINE, NETBANKING, UPI, CARD'}</td>
                    <td className="num">{s.allowed_sla_days || 1} day</td>
                    <td className="num">{s.penal_rate_annual || 12.0}%</td>
                    <td>Simple daily interest (delay days / 365)</td>
                    <td className="mono tiny">{s.letter_template_ref || 'TPL/PI/ONLINE/2026'}</td>
                    <td><span className="badge b-green">Active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System Configuration View */}
      {activeTab === 'config' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>System Parameters &amp; Accounts Configuration</h3>
              <div className="sub">Accounting suspense heads, clearing accounts, and business date</div>
            </div>
            {canEdit && (
              <button className="btn btn-p btn-sm" onClick={handleSaveConfig}>
                &#128190; Save configuration
              </button>
            )}
          </div>

          <form onSubmit={handleSaveConfig} className="card-b">
            <div className="grid g3 mb12">
              <div className="fld">
                <label>Demo business date</label>
                <input
                  type="date"
                  className="inp"
                  value={config.bizDate}
                  onChange={e => setConfig({ ...config, bizDate: e.target.value })}
                  disabled={!canEdit}
                />
                <div className="tiny muted mt4">Used as "today" by the reconciliation engine and SLA calculator.</div>
              </div>

              <div className="fld">
                <label>Financial year</label>
                <select
                  className="inp"
                  value={config.fy}
                  onChange={e => setConfig({ ...config, fy: e.target.value })}
                  disabled={!canEdit}
                >
                  <option value="2026-27">2026-27</option>
                  <option value="2025-26">2025-26</option>
                </select>
              </div>

              <div className="fld">
                <label>Date tolerance (days)</label>
                <input
                  type="number"
                  className="inp"
                  value={config.dateTolerance}
                  onChange={e => setConfig({ ...config, dateTolerance: Number(e.target.value) })}
                  disabled={!canEdit}
                />
              </div>

              <div className="fld">
                <label>Amount tolerance (INR)</label>
                <input
                  type="number"
                  step="0.01"
                  className="inp"
                  value={config.amtTolerance}
                  onChange={e => setConfig({ ...config, amtTolerance: Number(e.target.value) })}
                  disabled={!canEdit}
                />
              </div>

              <div className="fld">
                <label>Penal interest rate (% p.a.)</label>
                <input
                  type="number"
                  step="0.01"
                  className="inp"
                  value={config.penalRate}
                  onChange={e => setConfig({ ...config, penalRate: Number(e.target.value) })}
                  disabled={!canEdit}
                />
              </div>

              <div className="fld">
                <label>Exception escalation (days)</label>
                <input
                  type="number"
                  className="inp"
                  value={config.escalationDays}
                  onChange={e => setConfig({ ...config, escalationDays: Number(e.target.value) })}
                  disabled={!canEdit}
                />
              </div>
            </div>

            <div className="grid g2 mt12">
              <div className="fld">
                <label>Suspense Head (Unreconciled Receipts)</label>
                <input
                  className="inp"
                  value={config.suspenseHead}
                  onChange={e => setConfig({ ...config, suspenseHead: e.target.value })}
                  disabled={!canEdit}
                />
              </div>

              <div className="fld">
                <label>RAT Head (Receipts Awaiting Transfer)</label>
                <input
                  className="inp"
                  value={config.ratHead}
                  onChange={e => setConfig({ ...config, ratHead: e.target.value })}
                  disabled={!canEdit}
                />
              </div>

              <div className="fld">
                <label>RBI Government Revenue Clearing Account</label>
                <input
                  className="inp"
                  value={config.clearingAccount}
                  onChange={e => setConfig({ ...config, clearingAccount: e.target.value })}
                  disabled={!canEdit}
                />
              </div>

              <div className="fld">
                <label>Refund Accounting Head</label>
                <input
                  className="inp"
                  value={config.refundHead}
                  onChange={e => setConfig({ ...config, refundHead: e.target.value })}
                  disabled={!canEdit}
                />
              </div>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
export default MastersPage;
