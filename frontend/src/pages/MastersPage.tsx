import React, { useEffect, useState, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { money, cnt } from '../utils/format';
import {
  Department,
  Pao,
  Ddo,
  TreasuryBranch,
  AgencyBank,
  AgencyBankBranch,
  RevenuePortal,
  RevenueSource,
  LocalBody,
  ReceiptHead,
  ReconciliationRule,
  SlaRule,
} from '../types';

export const MastersPage: React.FC = () => {
  const { userRole, showToast, setActiveTab, refreshKey, triggerRefresh } = useApp();
  const [activeTab, setActiveTabLocal] = useState<'org' | 'sources' | 'heads' | 'rules' | 'slaRules' | 'config'>('org');
  const [subTab, setSubTab] = useState<'departments' | 'paos' | 'ddos' | 'treasuries' | 'localBodies' | 'banks' | 'branches' | 'portals'>('departments');

  const [loading, setLoading] = useState(true);
  const [searchFilter, setSearchFilter] = useState('');

  // Live Master Datasets
  const [departments, setDepartments] = useState<Department[]>([]);
  const [paos, setPaos] = useState<Pao[]>([]);
  const [ddos, setDdos] = useState<Ddo[]>([]);
  const [treasuries, setTreasuries] = useState<TreasuryBranch[]>([]);
  const [banks, setBanks] = useState<AgencyBank[]>([]);
  const [branches, setBranches] = useState<AgencyBankBranch[]>([]);
  const [portals, setPortals] = useState<RevenuePortal[]>([]);
  const [sources, setSources] = useState<RevenueSource[]>([]);
  const [localBodies, setLocalBodies] = useState<LocalBody[]>([]);
  const [heads, setHeads] = useState<ReceiptHead[]>([]);
  const [rules, setRules] = useState<ReconciliationRule[]>([]);
  const [slaRules, setSlaRules] = useState<SlaRule[]>([]);

  // Config State
  const [config, setConfig] = useState<any>({
    bizDate: '2026-09-15',
    fy: '2026-27',
    dateTolerance: 2,
    amtTolerance: 0.01,
    penalRate: 12.0,
    penalDayBasis: 365,
    escalationDays: 7,
    suspenseHead: '8658-00-102-01-00-01',
    ratHead: '8658-00-110-01-00-01',
    clearingAccount: '8658-00-101-01-00-01',
    refundHead: '0030-00-900-01-00-01',
    devolutionHead: '3604-00-200-01-00-01',
    penalInterestHead: '8658-00-102-01-00-02',
    penaltyHead: '0070-60-800-01-00-02',
  });

  // Modal State for Add & Edit
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    mode: 'add' | 'edit';
    entity: string;
    item: any;
  }>({
    isOpen: false,
    mode: 'add',
    entity: '',
    item: null,
  });
  const [modalSaving, setModalSaving] = useState(false);

  // Both SYSADMIN and TRE_ADMIN have permissions to manage masters
  const canEdit = ['SYSADMIN', 'TRE_ADMIN'].includes(userRole);

  const fetchMasterData = async () => {
    try {
      setLoading(true);
      const [
        deptRes,
        paoRes,
        ddoRes,
        tryRes,
        bankRes,
        brnRes,
        portRes,
        srcRes,
        bodyRes,
        headRes,
        ruleRes,
        slaRes,
        cfgRes,
      ] = await Promise.all([
        api.getDepartments().catch(() => []),
        api.getPaos().catch(() => []),
        api.getDdos().catch(() => []),
        api.getTreasuries().catch(() => []),
        api.getAgencyBanks().catch(() => []),
        api.getAgencyBankBranches().catch(() => []),
        api.getRevenuePortals().catch(() => []),
        api.getRevenueSources().catch(() => []),
        api.getLocalBodies().catch(() => []),
        api.getReceiptHeads().catch(() => []),
        api.getReconciliationRules().catch(() => []),
        api.getSlaRules().catch(() => []),
        api.getSystemConfig().catch(() => null),
      ]);

      setDepartments(deptRes || []);
      setPaos(paoRes || []);
      setDdos(ddoRes || []);
      setTreasuries(tryRes || []);
      setBanks(bankRes || []);
      setBranches(brnRes || []);
      setPortals(portRes || []);
      setSources(srcRes || []);
      setLocalBodies(bodyRes || []);
      setHeads(headRes || []);
      setRules(ruleRes || []);
      setSlaRules(slaRes || []);

      if (cfgRes) {
        setConfig((prev: any) => ({
          ...prev,
          ...cfgRes,
          bizDate: cfgRes.bizDate || cfgRes.demo_business_date || prev.bizDate,
          fy: cfgRes.fy || cfgRes.current_financial_year || prev.fy,
          dateTolerance: cfgRes.dateTolerance ?? cfgRes.date_tolerance_days ?? prev.dateTolerance,
          amtTolerance: cfgRes.amtTolerance ?? cfgRes.amount_tolerance ?? prev.amtTolerance,
          penalRate: cfgRes.penalRate ?? cfgRes.default_penal_rate_pct ?? prev.penalRate,
          penalDayBasis: cfgRes.penalDayBasis ?? prev.penalDayBasis,
          escalationDays: cfgRes.escalationDays ?? cfgRes.exception_escalation_days ?? prev.escalationDays,
          suspenseHead: cfgRes.suspenseHead || prev.suspenseHead,
          ratHead: cfgRes.ratHead || prev.ratHead,
          clearingAccount: cfgRes.clearingAccount || prev.clearingAccount,
          refundHead: cfgRes.refundHead || prev.refundHead,
          penalInterestHead: cfgRes.penalInterestHead || prev.penalInterestHead,
          penaltyHead: cfgRes.penaltyHead || prev.penaltyHead,
        }));
      }
    } catch (e: any) {
      showToast('Failed to load master configuration from database', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMasterData();
  }, [refreshKey]);

  // Toggle Status Handler
  const handleToggleStatus = async (entity: string, item: any) => {
    if (!canEdit) {
      showToast('Master maintenance requires Administrator privileges.', 'warning');
      return;
    }
    const newStatus = !(item.is_active !== false);
    try {
      if (entity === 'departments') {
        await api.updateDepartment(item.department_id, { is_active: newStatus });
      } else if (entity === 'paos') {
        await api.updatePao(item.pao_id || item.id, { is_active: newStatus });
      } else if (entity === 'ddos') {
        await api.updateDdo(item.ddo_id, { is_active: newStatus });
      } else if (entity === 'treasuries') {
        await api.updateTreasury(item.branch_id, { is_active: newStatus });
      } else if (entity === 'banks') {
        await api.updateAgencyBank(item.bank_id, { is_active: newStatus });
      } else if (entity === 'branches') {
        await api.updateAgencyBankBranch(item.bank_branch_id || item.branch_id, { is_active: newStatus });
      } else if (entity === 'portals') {
        await api.updateRevenuePortal(item.portal_id, { is_active: newStatus });
      } else if (entity === 'sources') {
        await api.updateRevenueSource(item.source_id, { is_active: newStatus });
      } else if (entity === 'localBodies') {
        await api.updateLocalBody(item.local_body_id, { is_active: newStatus });
      } else if (entity === 'heads') {
        await api.updateReceiptHead(item.coa_id || item.id, { is_active: newStatus });
      } else if (entity === 'rules') {
        await api.updateReconciliationRule(item.rule_id || item.id, { is_active: newStatus });
      } else if (entity === 'slaRules') {
        await api.updateSlaRule(item.sla_rule_id || item.id, { is_active: newStatus });
      }
      showToast(`Status updated to ${newStatus ? 'Active' : 'Inactive'}. Audit logged.`, 'success');
      await fetchMasterData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to update record status', 'error');
    }
  };

  // Open Add Modal with appropriate defaults
  const handleOpenAdd = (entity: string) => {
    let defaultItem: any = { is_active: true };
    if (entity === 'departments') {
      defaultItem = { department_code: '', department_name: '', department_type: 'DEPARTMENT', is_active: true };
    } else if (entity === 'paos') {
      defaultItem = {
        pao_code: '',
        pao_name: '',
        dept_code: departments[0]?.department_code || 'TT',
        treasury_code: treasuries[0]?.treasury_code || 'TRY-CENTRAL',
        is_active: true,
      };
    } else if (entity === 'ddos') {
      defaultItem = {
        ddo_code: '',
        ddo_name: '',
        department_id: departments[0]?.department_id || 1,
        ddo_type: 'REGULAR',
        treasury_code: treasuries[0]?.treasury_code || 'TRY-CENTRAL',
        is_active: true,
      };
    } else if (entity === 'treasuries') {
      defaultItem = { branch_code: '', branch_name: '', branch_type: 'TREASURY', city: 'Delhi', is_active: true };
    } else if (entity === 'banks') {
      defaultItem = { bank_code: '', bank_name: '', clearing_account_no: '', nodal_officer_name: '', nodal_officer_phone: '', is_active: true };
    } else if (entity === 'branches') {
      defaultItem = { bank_id: banks[0]?.bank_id || 1, branch_code: '', branch_name: '', ifsc_code: '', city: 'Delhi', is_active: true };
    } else if (entity === 'portals') {
      defaultItem = {
        portal_code: '',
        portal_name: '',
        department_id: departments[0]?.department_id || 1,
        api_endpoint: '',
        technical_contact: '',
        is_active: true,
      };
    } else if (entity === 'localBodies') {
      defaultItem = {
        local_body_code: '',
        local_body_name: '',
        body_type: 'MUNICIPAL_CORP',
        bank_account_no: '',
        ifsc_code: 'SBIN0001001',
        treasury_code: 'TRY-CENTRAL',
        is_active: true,
      };
    } else if (entity === 'sources') {
      defaultItem = {
        source_code: '',
        source_name: '',
        department_id: departments[0]?.department_id || 1,
        default_pao_code: paos[0]?.pao_code || 'PAO21',
        portal_id: portals[0]?.portal_id || 1,
        default_receipt_head_id: heads[0]?.coa_id || 1,
        is_tax_revenue: true,
        is_active: true,
      };
    } else if (entity === 'heads') {
      defaultItem = {
        coa_code: '',
        coa_name: '',
        major_head_id: 40,
        sub_major_head_id: 0,
        minor_head_id: 102,
        account_nature: 'REVENUE',
        is_active: true,
      };
    } else if (entity === 'rules') {
      defaultItem = {
        rule_code: `RR-0${rules.length + 1}`,
        rule_name: '',
        priority: rules.length + 1,
        primary_match_keys: 'REVENUE_SOURCE + CIN + AMOUNT',
        amount_tolerance: 0.01,
        date_tolerance_days: 2,
        matching_mode: 'THREE_WAY_EXACT',
        outcome_status: 'Matched',
        is_active: true,
      };
    } else if (entity === 'slaRules') {
      defaultItem = {
        rule_code: `SLA-MODE-${slaRules.length + 1}`,
        rule_name: '',
        payment_mode: 'ONLINE, NETBANKING, UPI',
        allowed_remittance_days: 1,
        grace_days: 0,
        annual_penal_rate_pct: 12.0,
        calculation_basis: 'DAILY_SIMPLE',
        is_active: true,
      };
    }

    setModalState({ isOpen: true, mode: 'add', entity, item: defaultItem });
  };

  const handleOpenEdit = (entity: string, item: any) => {
    setModalState({ isOpen: true, mode: 'edit', entity, item: { ...item } });
  };

  // Submit Modal Handler (Persists to PostgreSQL ifms_budget + Audit Log)
  const handleModalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalState.item) return;
    const { mode, entity, item } = modalState;

    try {
      setModalSaving(true);
      if (mode === 'add') {
        if (entity === 'departments') await api.createDepartment(item);
        else if (entity === 'paos') await api.createPao(item);
        else if (entity === 'ddos') await api.createDdo(item);
        else if (entity === 'treasuries') await api.createTreasury(item);
        else if (entity === 'banks') await api.createAgencyBank(item);
        else if (entity === 'branches') await api.createAgencyBankBranch(item);
        else if (entity === 'portals') await api.createRevenuePortal(item);
        else if (entity === 'sources') await api.createRevenueSource(item);
        else if (entity === 'localBodies') await api.createLocalBody(item);
        else if (entity === 'heads') await api.createReceiptHead(item);
        else if (entity === 'rules') await api.createReconciliationRule(item);
        else if (entity === 'slaRules') await api.createSlaRule(item);
        showToast(`New ${entity} record created successfully in PostgreSQL. Audit logged.`, 'success');
      } else {
        if (entity === 'departments') await api.updateDepartment(item.department_id, item);
        else if (entity === 'paos') await api.updatePao(item.pao_id || item.id, item);
        else if (entity === 'ddos') await api.updateDdo(item.ddo_id, item);
        else if (entity === 'treasuries') await api.updateTreasury(item.branch_id, item);
        else if (entity === 'banks') await api.updateAgencyBank(item.bank_id, item);
        else if (entity === 'branches') await api.updateAgencyBankBranch(item.bank_branch_id || item.branch_id, item);
        else if (entity === 'portals') await api.updateRevenuePortal(item.portal_id, item);
        else if (entity === 'sources') await api.updateRevenueSource(item.source_id, item);
        else if (entity === 'localBodies') await api.updateLocalBody(item.local_body_id, item);
        else if (entity === 'heads') await api.updateReceiptHead(item.coa_id || item.id, item);
        else if (entity === 'rules') await api.updateReconciliationRule(item.rule_id || item.id, item);
        else if (entity === 'slaRules') await api.updateSlaRule(item.sla_rule_id || item.id, item);
        showToast(`${entity} record updated successfully in PostgreSQL. Audit logged.`, 'success');
      }

      setModalState({ isOpen: false, mode: 'add', entity: '', item: null });
      await fetchMasterData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Operation failed on server', 'error');
    } finally {
      setModalSaving(false);
    }
  };

  // System Configuration Save
  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) {
      showToast('Only System or Treasury Administrator can edit configuration.', 'warning');
      return;
    }
    try {
      setLoading(true);
      await api.updateSystemConfig(config);
      showToast('System configuration saved to PostgreSQL. Audit log recorded.', 'success');
      await fetchMasterData();
      triggerRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to save configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Filter Helper
  const filterList = <T,>(list: T[], filterFn: (item: T, q: string) => boolean): T[] => {
    if (!searchFilter.trim()) return list;
    const q = searchFilter.toLowerCase();
    return list.filter(item => filterFn(item, q));
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
            Administrative masters, revenue streams, Chart of Accounts, reconciliation rules, SLA standards, and core system parameters. Every change persists to PostgreSQL and is written to the audit trail.
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
          Signed in as <strong>{userRole}</strong>. Master configuration maintenance requires the <strong>System Administrator</strong> or <strong>Treasury Administrator</strong> role.
        </div>
      )}

      {/* Main Tabs */}
      <div className="tabs">
        {[
          { k: 'org', label: `Organisation masters (${departments.length + paos.length + ddos.length + treasuries.length + banks.length + branches.length + portals.length + localBodies.length})` },
          { k: 'sources', label: `Revenue sources (${sources.length})` },
          { k: 'heads', label: `Receipt heads (${heads.length})` },
          { k: 'rules', label: `Reconciliation rules (${rules.length})` },
          { k: 'slaRules', label: `Bank SLA & penal interest (${slaRules.length})` },
          { k: 'config', label: 'System configuration' },
        ].map(t => (
          <div
            key={t.k}
            className={`tab ${activeTab === t.k ? 'active' : ''}`}
            onClick={() => {
              setActiveTabLocal(t.k as any);
              setSearchFilter('');
            }}
          >
            {t.label}
          </div>
        ))}
      </div>

      {/* 1. Organisation Masters View */}
      {activeTab === 'org' && (
        <div>
          <div className="tabs">
            {[
              { k: 'departments', label: `Departments (${departments.length})` },
              { k: 'paos', label: `PAOs (${paos.length})` },
              { k: 'ddos', label: `DDOs (${ddos.length})` },
              { k: 'treasuries', label: `Treasuries (${treasuries.length})` },
              { k: 'localBodies', label: `Local bodies (${localBodies.length})` },
              { k: 'banks', label: `Banks (${banks.length})` },
              { k: 'branches', label: `Bank branches (${branches.length})` },
              { k: 'portals', label: `Revenue portals (${portals.length})` },
            ].map(s => (
              <div
                key={s.k}
                className={`tab ${subTab === s.k ? 'active' : ''}`}
                onClick={() => {
                  setSubTab(s.k as any);
                  setSearchFilter('');
                }}
              >
                {s.label}
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-h">
              <div>
                <h3 className="capitalize">{subTab} Master</h3>
                <div className="sub">Live records maintained in PostgreSQL (schema: ifms_budget)</div>
              </div>
              <div className="flex gap8 items-center">
                <input
                  type="text"
                  className="inp"
                  placeholder={`Search ${subTab}...`}
                  value={searchFilter}
                  onChange={e => setSearchFilter(e.target.value)}
                  style={{ width: '220px', padding: '4px 8px', fontSize: '12px' }}
                />
                {canEdit && (
                  <button className="btn btn-p btn-sm" onClick={() => handleOpenAdd(subTab)}>
                    &#43; Add Record
                  </button>
                )}
              </div>
            </div>

            <div className="tbl-wrap">
              <table className="dt">
                {/* 1.1 Departments */}
                {subTab === 'departments' && (
                  <>
                    <thead>
                      <tr>
                        <th>Department Code</th>
                        <th>Department Name</th>
                        <th>Department Type</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(departments, (d, q) =>
                        d.department_code.toLowerCase().includes(q) ||
                        d.department_name.toLowerCase().includes(q) ||
                        (d.department_type || '').toLowerCase().includes(q)
                      ).map(d => (
                        <tr key={d.department_id}>
                          <td className="mono strong">{d.department_code}</td>
                          <td>{d.department_name}</td>
                          <td><span className="badge b-blue">{d.department_type || 'DEPARTMENT'}</span></td>
                          <td>
                            <span
                              className={`badge ${d.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('departments', d)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {d.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('departments', d)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('departments', d)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {d.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {departments.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 5 : 4} className="tc muted py16">
                            {loading ? 'Loading departments...' : 'No departments found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}

                {/* 1.2 PAOs */}
                {subTab === 'paos' && (
                  <>
                    <thead>
                      <tr>
                        <th>PAO Code</th>
                        <th>PAO Name</th>
                        <th>Department</th>
                        <th>Treasury</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(paos, (p, q) =>
                        p.pao_code.toLowerCase().includes(q) ||
                        p.pao_name.toLowerCase().includes(q) ||
                        (p.dept_code || '').toLowerCase().includes(q)
                      ).map(p => (
                        <tr key={p.pao_id || p.id || p.pao_code}>
                          <td className="mono strong">{p.pao_code}</td>
                          <td>{p.pao_name}</td>
                          <td className="mono">{p.dept_code || 'TT'}</td>
                          <td>{p.treasury_code || 'TRY-CENTRAL'}</td>
                          <td>
                            <span
                              className={`badge ${p.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('paos', p)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {p.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('paos', p)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('paos', p)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {p.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {paos.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 6 : 5} className="tc muted py16">
                            {loading ? 'Loading PAOs...' : 'No PAOs found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}

                {/* 1.3 DDOs */}
                {subTab === 'ddos' && (
                  <>
                    <thead>
                      <tr>
                        <th>DDO Code</th>
                        <th>DDO Name / Description</th>
                        <th>Department</th>
                        <th>Type</th>
                        <th>Treasury</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(ddos, (d, q) =>
                        d.ddo_code.toLowerCase().includes(q) ||
                        d.ddo_name.toLowerCase().includes(q) ||
                        (d.department_code || '').toLowerCase().includes(q)
                      ).map(d => (
                        <tr key={d.ddo_id}>
                          <td className="mono strong">{d.ddo_code}</td>
                          <td>{d.ddo_name}</td>
                          <td>{d.department_code || d.department_name || `Dept #${d.department_id}`}</td>
                          <td><span className="badge b-blue">{d.ddo_type || 'REGULAR'}</span></td>
                          <td>{d.treasury_code || 'TRY-CENTRAL'}</td>
                          <td>
                            <span
                              className={`badge ${d.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('ddos', d)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {d.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('ddos', d)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('ddos', d)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {d.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {ddos.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 7 : 6} className="tc muted py16">
                            {loading ? 'Loading DDOs...' : 'No DDOs found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}

                {/* 1.4 Treasuries */}
                {subTab === 'treasuries' && (
                  <>
                    <thead>
                      <tr>
                        <th>Branch / Treasury Code</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>City / Jurisdiction</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(treasuries, (t, q) =>
                        t.branch_code.toLowerCase().includes(q) ||
                        t.branch_name.toLowerCase().includes(q) ||
                        (t.city || '').toLowerCase().includes(q)
                      ).map(t => (
                        <tr key={t.branch_id}>
                          <td className="mono strong">{t.branch_code}</td>
                          <td>{t.branch_name}</td>
                          <td><span className="badge b-purple">{t.branch_type || 'TREASURY'}</span></td>
                          <td>{t.city || 'Delhi'}</td>
                          <td>
                            <span
                              className={`badge ${t.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('treasuries', t)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {t.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('treasuries', t)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('treasuries', t)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {t.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {treasuries.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 6 : 5} className="tc muted py16">
                            {loading ? 'Loading treasuries...' : 'No treasuries found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}

                {/* 1.5 Local Bodies */}
                {subTab === 'localBodies' && (
                  <>
                    <thead>
                      <tr>
                        <th>Body Code</th>
                        <th>Local Body Name</th>
                        <th>Type</th>
                        <th>Bank Account</th>
                        <th>IFSC</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(localBodies, (b, q) =>
                        (b.local_body_code || '').toLowerCase().includes(q) ||
                        b.local_body_name.toLowerCase().includes(q) ||
                        b.body_type.toLowerCase().includes(q)
                      ).map(b => (
                        <tr key={b.local_body_id}>
                          <td className="mono strong">{b.local_body_code || `LB-${b.local_body_id}`}</td>
                          <td>{b.local_body_name}</td>
                          <td><span className="badge b-blue">{b.body_type}</span></td>
                          <td className="mono">{b.bank_account_no}</td>
                          <td className="mono">{b.ifsc_code}</td>
                          <td>
                            <span
                              className={`badge ${b.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('localBodies', b)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {b.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('localBodies', b)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('localBodies', b)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {b.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {localBodies.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 7 : 6} className="tc muted py16">
                            {loading ? 'Loading local bodies...' : 'No local bodies found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}

                {/* 1.6 Banks */}
                {subTab === 'banks' && (
                  <>
                    <thead>
                      <tr>
                        <th>Bank Code</th>
                        <th>Bank Name</th>
                        <th>Clearing Account No</th>
                        <th>Nodal Officer</th>
                        <th>Contact Phone</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(banks, (b, q) =>
                        b.bank_code.toLowerCase().includes(q) ||
                        b.bank_name.toLowerCase().includes(q)
                      ).map(b => (
                        <tr key={b.bank_id}>
                          <td className="mono strong">{b.bank_code}</td>
                          <td>{b.bank_name}</td>
                          <td className="mono">{b.clearing_account_no || 'Govt Pool A/c'}</td>
                          <td>{b.nodal_officer_name || 'Chief Manager'}</td>
                          <td>{b.nodal_officer_phone || '011-23382901'}</td>
                          <td>
                            <span
                              className={`badge ${b.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('banks', b)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {b.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('banks', b)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('banks', b)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {b.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {banks.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 7 : 6} className="tc muted py16">
                            {loading ? 'Loading agency banks...' : 'No banks found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}

                {/* 1.7 Bank Branches */}
                {subTab === 'branches' && (
                  <>
                    <thead>
                      <tr>
                        <th>Branch Code</th>
                        <th>Branch Name</th>
                        <th>Bank</th>
                        <th>IFSC Code</th>
                        <th>City</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(branches, (br, q) =>
                        br.branch_code.toLowerCase().includes(q) ||
                        br.branch_name.toLowerCase().includes(q) ||
                        (br.ifsc_code || '').toLowerCase().includes(q)
                      ).map(br => (
                        <tr key={br.branch_id || (br as any).bank_branch_id}>
                          <td className="mono strong">{br.branch_code}</td>
                          <td>{br.branch_name}</td>
                          <td>{(br as any).bank_name || `Bank #${br.bank_id}`}</td>
                          <td className="mono">{br.ifsc_code}</td>
                          <td>{br.city || 'Delhi'}</td>
                          <td>
                            <span
                              className={`badge ${br.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('branches', br)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {br.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('branches', br)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('branches', br)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {br.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {branches.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 7 : 6} className="tc muted py16">
                            {loading ? 'Loading bank branches...' : 'No bank branches found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}

                {/* 1.8 Revenue Portals */}
                {subTab === 'portals' && (
                  <>
                    <thead>
                      <tr>
                        <th>Portal Code</th>
                        <th>Portal Name</th>
                        <th>Department</th>
                        <th>API Endpoint</th>
                        <th>Technical Contact</th>
                        <th>Status</th>
                        {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                      </tr>
                    </thead>
                    <tbody>
                      {filterList(portals, (p, q) =>
                        p.portal_code.toLowerCase().includes(q) ||
                        p.portal_name.toLowerCase().includes(q) ||
                        (p.api_endpoint || '').toLowerCase().includes(q)
                      ).map(p => (
                        <tr key={p.portal_id}>
                          <td className="mono strong">{p.portal_code}</td>
                          <td>{p.portal_name}</td>
                          <td>{(p as any).department_code || (p as any).department_name || `Dept #${p.department_id || 1}`}</td>
                          <td className="mono tiny">{p.api_endpoint || 'REST / SFTP Gateway'}</td>
                          <td className="small">{p.technical_contact || 'tech-support@portal.gov.in'}</td>
                          <td>
                            <span
                              className={`badge ${p.is_active !== false ? 'b-green' : 'b-gray'}`}
                              style={{ cursor: canEdit ? 'pointer' : 'default' }}
                              onClick={() => canEdit && handleToggleStatus('portals', p)}
                              title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                            >
                              {p.is_active !== false ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          {canEdit && (
                            <td style={{ textAlign: 'right' }}>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleOpenEdit('portals', p)}
                                style={{ padding: '2px 8px', fontSize: '11px' }}
                              >
                                Edit
                              </button>
                              <button
                                className="btn btn-sm"
                                onClick={() => handleToggleStatus('portals', p)}
                                style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                              >
                                {p.is_active !== false ? 'Deactivate' : 'Activate'}
                              </button>
                            </td>
                          )}
                        </tr>
                      ))}
                      {portals.length === 0 && (
                        <tr>
                          <td colSpan={canEdit ? 7 : 6} className="tc muted py16">
                            {loading ? 'Loading portals...' : 'No portals found.'}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </>
                )}
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 2. Revenue Sources View */}
      {activeTab === 'sources' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Revenue Sources</h3>
              <div className="sub">{cnt(sources.length)} registered revenue streams configured in PostgreSQL</div>
            </div>
            <div className="flex gap8 items-center">
              <input
                type="text"
                className="inp"
                placeholder="Search sources..."
                value={searchFilter}
                onChange={e => setSearchFilter(e.target.value)}
                style={{ width: '220px', padding: '4px 8px', fontSize: '12px' }}
              />
              {canEdit && (
                <button className="btn btn-p btn-sm" onClick={() => handleOpenAdd('sources')}>
                  &#43; Add Source
                </button>
              )}
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Source Code</th>
                  <th>Source Name</th>
                  <th>Department</th>
                  <th>PAO Code</th>
                  <th>Revenue Head</th>
                  <th>Type</th>
                  <th>Status</th>
                  {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {filterList(sources, (s, q) =>
                  s.source_code.toLowerCase().includes(q) ||
                  s.source_name.toLowerCase().includes(q) ||
                  (s.default_pao_code || '').toLowerCase().includes(q)
                ).map(s => (
                  <tr key={s.source_id}>
                    <td className="mono strong">{s.source_code}</td>
                    <td>{s.source_name}</td>
                    <td>{(s as any).department_code || (s as any).department_name || 'Trade & Taxes'}</td>
                    <td className="mono">{s.default_pao_code || 'PAO21'}</td>
                    <td className="mono tiny">{(s as any).receipt_head || s.default_receipt_head || '0040-00-102-01-00-01'}</td>
                    <td>
                      <span className={`badge ${s.is_tax_revenue !== false ? 'b-blue' : 'b-purple'}`}>
                        {s.is_tax_revenue !== false ? 'Tax Revenue' : 'Non-Tax Revenue'}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge ${s.is_active !== false ? 'b-green' : 'b-gray'}`}
                        style={{ cursor: canEdit ? 'pointer' : 'default' }}
                        onClick={() => canEdit && handleToggleStatus('sources', s)}
                        title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                      >
                        {s.is_active !== false ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    {canEdit && (
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleOpenEdit('sources', s)}
                          style={{ padding: '2px 8px', fontSize: '11px' }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleToggleStatus('sources', s)}
                          style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                        >
                          {s.is_active !== false ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {sources.length === 0 && (
                  <tr>
                    <td colSpan={canEdit ? 8 : 7} className="tc muted py16">
                      {loading ? 'Loading sources...' : 'No revenue sources found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 3. Receipt Heads / Chart of Accounts View */}
      {activeTab === 'heads' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Chart of Accounts &mdash; Receipt Heads</h3>
              <div className="sub">{cnt(heads.length)} dynamic major-to-object heads mapped from PostgreSQL</div>
            </div>
            <div className="flex gap8 items-center">
              <input
                type="text"
                className="inp"
                placeholder="Search heads by code or name..."
                value={searchFilter}
                onChange={e => setSearchFilter(e.target.value)}
                style={{ width: '250px', padding: '4px 8px', fontSize: '12px' }}
              />
              {canEdit && (
                <button className="btn btn-p btn-sm" onClick={() => handleOpenAdd('heads')}>
                  &#43; Add Receipt Head
                </button>
              )}
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Full Head Code</th>
                  <th>Head Description / Account Name</th>
                  <th>Major Head</th>
                  <th>Sub-Major</th>
                  <th>Minor Head</th>
                  <th>Nature</th>
                  <th>Status</th>
                  {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {filterList(heads, (h, q) =>
                  (h.coa_code || h.head_code || h.code || '').toLowerCase().includes(q) ||
                  (h.coa_name || h.description || h.name || '').toLowerCase().includes(q)
                ).map(h => (
                  <tr key={h.coa_id || h.id || h.coa_code}>
                    <td className="mono strong">{h.coa_code || h.head_code || h.code}</td>
                    <td>{h.coa_name || h.description || h.name}</td>
                    <td className="mono">{h.major_head_id || h.major_head || h.major || '0040'}</td>
                    <td className="mono">{h.sub_major_head_id ?? h.submajor_head ?? '00'}</td>
                    <td className="mono">{h.minor_head_id || h.minor_head || h.minor || '102'}</td>
                    <td>
                      <span className="badge b-blue">{h.account_nature || 'REVENUE'}</span>
                    </td>
                    <td>
                      <span
                        className={`badge ${h.is_active !== false ? 'b-green' : 'b-gray'}`}
                        style={{ cursor: canEdit ? 'pointer' : 'default' }}
                        onClick={() => canEdit && handleToggleStatus('heads', h)}
                        title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                      >
                        {h.is_active !== false ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    {canEdit && (
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleOpenEdit('heads', h)}
                          style={{ padding: '2px 8px', fontSize: '11px' }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleToggleStatus('heads', h)}
                          style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                        >
                          {h.is_active !== false ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {heads.length === 0 && (
                  <tr>
                    <td colSpan={canEdit ? 8 : 7} className="tc muted py16">
                      {loading ? 'Loading receipt heads...' : 'No receipt heads found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. Reconciliation Matching Rules View */}
      {activeTab === 'rules' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Reconciliation Matching Rules</h3>
              <div className="sub">Evaluated strictly in priority sequence by the automated matching engine (Table: ifms_budget.rev_recon_rule)</div>
            </div>
            <div className="flex gap8 items-center">
              <input
                type="text"
                className="inp"
                placeholder="Search rules..."
                value={searchFilter}
                onChange={e => setSearchFilter(e.target.value)}
                style={{ width: '200px', padding: '4px 8px', fontSize: '12px' }}
              />
              {canEdit && (
                <button className="btn btn-p btn-sm" onClick={() => handleOpenAdd('rules')}>
                  &#43; Add Matching Rule
                </button>
              )}
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Rule ID</th>
                  <th className="num">Priority</th>
                  <th>Rule Name</th>
                  <th>Primary Match Keys</th>
                  <th>Amount Tol (INR)</th>
                  <th>Date Tol (Days)</th>
                  <th>Matching Mode</th>
                  <th>Outcome</th>
                  <th>Status</th>
                  {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {filterList(rules, (r, q) =>
                  r.rule_code.toLowerCase().includes(q) ||
                  (r.rule_name || '').toLowerCase().includes(q) ||
                  (r.primary_match_keys || '').toLowerCase().includes(q)
                ).map(r => (
                  <tr key={r.rule_id || r.id || r.rule_code}>
                    <td className="mono strong">{r.rule_code}</td>
                    <td className="num strong">{r.priority}</td>
                    <td>{r.rule_name || r.rule_code}</td>
                    <td>{r.primary_match_keys || (r as any).primary}</td>
                    <td className="num">₹ {r.amount_tolerance ?? 0.01}</td>
                    <td className="num">{r.date_tolerance_days ?? 2} day(s)</td>
                    <td><span className="badge b-purple">{r.matching_mode || 'THREE_WAY_EXACT'}</span></td>
                    <td>
                      <span className="badge b-blue">{r.outcome_status || 'Matched'}</span>
                    </td>
                    <td>
                      <span
                        className={`badge ${r.is_active !== false ? 'b-green' : 'b-gray'}`}
                        style={{ cursor: canEdit ? 'pointer' : 'default' }}
                        onClick={() => canEdit && handleToggleStatus('rules', r)}
                        title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                      >
                        {r.is_active !== false ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    {canEdit && (
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleOpenEdit('rules', r)}
                          style={{ padding: '2px 8px', fontSize: '11px' }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleToggleStatus('rules', r)}
                          style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                        >
                          {r.is_active !== false ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {rules.length === 0 && (
                  <tr>
                    <td colSpan={canEdit ? 10 : 9} className="tc muted py16">
                      {loading ? 'Loading rules...' : 'No reconciliation rules found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="card-b">
            <div className="box info small">
              <strong>Rule Evaluation Priority:</strong> Priority 1 evaluates first. Exact 3-way matches match first. Subsequent rules handle one-to-many aggregations, suspense ageing, orphan receipts (RAT), and duplicate scans. All mutations are recorded in PostgreSQL audit logs.
            </div>
          </div>
        </div>
      )}

      {/* 5. Bank SLA Rules View */}
      {activeTab === 'slaRules' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Bank SLA &amp; Penal Interest Configuration</h3>
              <div className="sub">Remittance SLAs, grace days, and statutory penal rates per channel (Table: ifms_budget.rev_sla_rule)</div>
            </div>
            <div className="flex gap8 items-center">
              <input
                type="text"
                className="inp"
                placeholder="Search SLA rules..."
                value={searchFilter}
                onChange={e => setSearchFilter(e.target.value)}
                style={{ width: '200px', padding: '4px 8px', fontSize: '12px' }}
              />
              {canEdit && (
                <button className="btn btn-p btn-sm" onClick={() => handleOpenAdd('slaRules')}>
                  &#43; Add SLA Rule
                </button>
              )}
            </div>
          </div>
          <div className="tbl-wrap">
            <table className="dt">
              <thead>
                <tr>
                  <th>Rule ID</th>
                  <th>Rule Name</th>
                  <th>Payment Modes</th>
                  <th className="num">Allowed SLA Days</th>
                  <th className="num">Grace Days</th>
                  <th className="num">Penal Rate (% p.a.)</th>
                  <th>Calculation Basis</th>
                  <th>Status</th>
                  {canEdit && <th style={{ textAlign: 'right' }}>Actions</th>}
                </tr>
              </thead>
              <tbody>
                {filterList(slaRules, (s, q) =>
                  (s.rule_code || '').toLowerCase().includes(q) ||
                  (s.rule_name || '').toLowerCase().includes(q) ||
                  s.payment_mode.toLowerCase().includes(q)
                ).map(s => (
                  <tr key={s.sla_rule_id || (s as any).id || s.rule_code}>
                    <td className="mono strong">{s.rule_code}</td>
                    <td>{s.rule_name || s.rule_code}</td>
                    <td>{s.payment_mode}</td>
                    <td className="num">{s.allowed_remittance_days ?? 1} day(s)</td>
                    <td className="num">{s.grace_days ?? 0} day(s)</td>
                    <td className="num strong">{s.annual_penal_rate_pct ?? 12.0}%</td>
                    <td>{s.calculation_basis || 'DAILY_SIMPLE'}</td>
                    <td>
                      <span
                        className={`badge ${s.is_active !== false ? 'b-green' : 'b-gray'}`}
                        style={{ cursor: canEdit ? 'pointer' : 'default' }}
                        onClick={() => canEdit && handleToggleStatus('slaRules', s)}
                        title={canEdit ? 'Click to toggle Active/Inactive' : undefined}
                      >
                        {s.is_active !== false ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    {canEdit && (
                      <td style={{ textAlign: 'right' }}>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleOpenEdit('slaRules', s)}
                          style={{ padding: '2px 8px', fontSize: '11px' }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm"
                          onClick={() => handleToggleStatus('slaRules', s)}
                          style={{ padding: '2px 8px', fontSize: '11px', marginLeft: '4px' }}
                        >
                          {s.is_active !== false ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {slaRules.length === 0 && (
                  <tr>
                    <td colSpan={canEdit ? 9 : 8} className="tc muted py16">
                      {loading ? 'Loading SLA rules...' : 'No SLA rules found.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 6. System Configuration View */}
      {activeTab === 'config' && (
        <div className="card">
          <div className="card-h">
            <div>
              <h3>System Parameters &amp; Accounts Configuration</h3>
              <div className="sub">Accounting suspense heads, clearing accounts, and business date loaded from PostgreSQL (ifms_budget.rev_system_config)</div>
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
                  <option value="2024-25">2024-25</option>
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

              <div className="fld">
                <label>Penal Interest Posting Head / Account</label>
                <input
                  className="inp"
                  value={config.penalInterestHead}
                  onChange={e => setConfig({ ...config, penalInterestHead: e.target.value })}
                  disabled={!canEdit}
                />
              </div>

              <div className="fld">
                <label>Penalty Posting Head / Account</label>
                <input
                  className="inp"
                  value={config.penaltyHead}
                  onChange={e => setConfig({ ...config, penaltyHead: e.target.value })}
                  disabled={!canEdit}
                />
              </div>
            </div>

            {canEdit && (
              <div className="mt16 flex justify-end">
                <button type="submit" className="btn btn-p btn-sm">
                  Save Configuration to Database
                </button>
              </div>
            )}
          </form>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ADD / EDIT RECORD MODAL (Dynamic according to selected entity)           */}
      {/* ========================================================================= */}
      {modalState.isOpen && modalState.item && (
        <div className="ovl">
          <div className="modal" style={{ maxWidth: '640px' }}>
            <div className="modal-h">
              <div>
                <h3>
                  {modalState.mode === 'add' ? 'Add Record to' : 'Edit Record in'}{' '}
                  <span className="capitalize">{modalState.entity} Master</span>
                </h3>
                <div className="sub">Changes will be committed directly to PostgreSQL and logged in audit trail</div>
              </div>
              <button
                type="button"
                className="modal-x"
                onClick={() => setModalState({ isOpen: false, mode: 'add', entity: '', item: null })}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleModalSubmit}>
              <div className="modal-b">
                {/* Department Form */}
                {modalState.entity === 'departments' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Department Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.department_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, department_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Department Type *</label>
                      <select
                        className="inp"
                        value={modalState.item.department_type || 'DEPARTMENT'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, department_type: e.target.value } })}
                      >
                        <option value="DEPARTMENT">Department</option>
                        <option value="SECRETARIAT">Secretariat</option>
                        <option value="DIRECTORATE">Directorate</option>
                        <option value="COMMISSIONERATE">Commissionerate</option>
                      </select>
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Department Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.department_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, department_name: e.target.value } })}
                      />
                    </div>
                  </div>
                )}

                {/* PAO Form */}
                {modalState.entity === 'paos' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>PAO Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.pao_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, pao_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Department Code</label>
                      <select
                        className="inp"
                        value={modalState.item.dept_code || 'TT'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, dept_code: e.target.value } })}
                      >
                        {departments.map(d => (
                          <option key={d.department_code} value={d.department_code}>
                            {d.department_code} - {d.department_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>PAO Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.pao_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, pao_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Treasury Code</label>
                      <select
                        className="inp"
                        value={modalState.item.treasury_code || 'TRY-CENTRAL'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, treasury_code: e.target.value } })}
                      >
                        {treasuries.map(t => (
                          <option key={t.branch_code} value={t.treasury_code || t.branch_code}>
                            {t.branch_code} - {t.branch_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {/* DDO Form */}
                {modalState.entity === 'ddos' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>DDO Code *</label>
                      <input
                        type="text"
                        required
                        className="inp mono"
                        value={modalState.item.ddo_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, ddo_code: e.target.value } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Department</label>
                      <select
                        className="inp"
                        value={modalState.item.department_id || 1}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, department_id: Number(e.target.value) } })}
                      >
                        {departments.map(d => (
                          <option key={d.department_id} value={d.department_id}>
                            {d.department_code} - {d.department_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>DDO Name / Description *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.ddo_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, ddo_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>DDO Type</label>
                      <select
                        className="inp"
                        value={modalState.item.ddo_type || 'REGULAR'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, ddo_type: e.target.value } })}
                      >
                        <option value="REGULAR">Regular DDO</option>
                        <option value="SPECIAL">Special DDO</option>
                        <option value="AUTONOMOUS">Autonomous Body</option>
                      </select>
                    </div>
                    <div className="fld">
                      <label>Treasury</label>
                      <select
                        className="inp"
                        value={modalState.item.treasury_code || 'TRY-CENTRAL'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, treasury_code: e.target.value } })}
                      >
                        {treasuries.map(t => (
                          <option key={t.branch_code} value={t.treasury_code || t.branch_code}>
                            {t.branch_code} - {t.branch_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {/* Treasury Form */}
                {modalState.entity === 'treasuries' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Branch / Treasury Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.branch_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, branch_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Branch Type</label>
                      <select
                        className="inp"
                        value={modalState.item.branch_type || 'TREASURY'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, branch_type: e.target.value } })}
                      >
                        <option value="TREASURY">Treasury</option>
                        <option value="SUB_TREASURY">Sub-Treasury</option>
                        <option value="BRANCH">Administrative Branch</option>
                      </select>
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Treasury / Branch Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.branch_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, branch_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>City / Location</label>
                      <input
                        type="text"
                        className="inp"
                        value={modalState.item.city || 'Delhi'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, city: e.target.value } })}
                      />
                    </div>
                  </div>
                )}

                {/* Agency Bank Form */}
                {modalState.entity === 'banks' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Bank Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.bank_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, bank_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>IFSC Prefix</label>
                      <input
                        type="text"
                        className="inp uppercase mono"
                        value={modalState.item.ifsc_prefix || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, ifsc_prefix: e.target.value.toUpperCase() } })}
                      />
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Bank Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.bank_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, bank_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Clearing Account No</label>
                      <input
                        type="text"
                        className="inp mono"
                        value={modalState.item.clearing_account_no || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, clearing_account_no: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Nodal Officer Name</label>
                      <input
                        type="text"
                        className="inp"
                        value={modalState.item.nodal_officer_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, nodal_officer_name: e.target.value } })}
                      />
                    </div>
                  </div>
                )}

                {/* Bank Branch Form */}
                {modalState.entity === 'branches' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Bank *</label>
                      <select
                        className="inp"
                        value={modalState.item.bank_id || 1}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, bank_id: Number(e.target.value) } })}
                      >
                        {banks.map(b => (
                          <option key={b.bank_id} value={b.bank_id}>
                            {b.bank_code} - {b.bank_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="fld">
                      <label>Branch Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.branch_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, branch_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Branch Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.branch_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, branch_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>IFSC Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.ifsc_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, ifsc_code: e.target.value.toUpperCase() } })}
                      />
                    </div>
                    <div className="fld">
                      <label>City</label>
                      <input
                        type="text"
                        className="inp"
                        value={modalState.item.city || 'Delhi'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, city: e.target.value } })}
                      />
                    </div>
                  </div>
                )}

                {/* Revenue Portal Form */}
                {modalState.entity === 'portals' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Portal Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.portal_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, portal_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Department</label>
                      <select
                        className="inp"
                        value={modalState.item.department_id || 1}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, department_id: Number(e.target.value) } })}
                      >
                        {departments.map(d => (
                          <option key={d.department_id} value={d.department_id}>
                            {d.department_code} - {d.department_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Portal Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.portal_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, portal_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>API Endpoint / SFTP URL</label>
                      <input
                        type="text"
                        className="inp mono"
                        value={modalState.item.api_endpoint || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, api_endpoint: e.target.value } })}
                      />
                    </div>
                  </div>
                )}

                {/* Local Body Form */}
                {modalState.entity === 'localBodies' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Local Body Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.local_body_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, local_body_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Body Type *</label>
                      <select
                        className="inp"
                        value={modalState.item.body_type || 'MUNICIPAL_CORP'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, body_type: e.target.value } })}
                      >
                        <option value="MUNICIPAL_CORP">Municipal Corporation</option>
                        <option value="MUNICIPAL_COUNCIL">Municipal Council</option>
                        <option value="PANCHAYAT">Panchayati Raj Institution</option>
                        <option value="DEVELOPMENT_AUTH">Development Authority</option>
                      </select>
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Local Body Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.local_body_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, local_body_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Bank Account No *</label>
                      <input
                        type="text"
                        required
                        className="inp mono"
                        value={modalState.item.bank_account_no || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, bank_account_no: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>IFSC Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.ifsc_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, ifsc_code: e.target.value.toUpperCase() } })}
                      />
                    </div>
                  </div>
                )}

                {/* Revenue Source Form */}
                {modalState.entity === 'sources' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Source Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.source_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, source_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Department</label>
                      <select
                        className="inp"
                        value={modalState.item.department_id || 1}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, department_id: Number(e.target.value) } })}
                      >
                        {departments.map(d => (
                          <option key={d.department_id} value={d.department_id}>
                            {d.department_code} - {d.department_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Source Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.source_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, source_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Default PAO</label>
                      <select
                        className="inp"
                        value={modalState.item.default_pao_code || 'PAO21'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, default_pao_code: e.target.value } })}
                      >
                        {paos.map(p => (
                          <option key={p.pao_code} value={p.pao_code}>
                            {p.pao_code} - {p.pao_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="fld">
                      <label>Tax Revenue Stream?</label>
                      <select
                        className="inp"
                        value={modalState.item.is_tax_revenue ? 'YES' : 'NO'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, is_tax_revenue: e.target.value === 'YES' } })}
                      >
                        <option value="YES">Yes (Tax Revenue)</option>
                        <option value="NO">No (Non-Tax Revenue)</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Receipt Head Form */}
                {modalState.entity === 'heads' && (
                  <div className="grid g2">
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Full Head Code (15-digit / COA Code) *</label>
                      <input
                        type="text"
                        required
                        placeholder="0040-00-102-01-00-01"
                        className="inp mono"
                        value={modalState.item.coa_code || modalState.item.head_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, coa_code: e.target.value } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Account Name / Description *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.coa_name || modalState.item.description || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, coa_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Account Nature</label>
                      <select
                        className="inp"
                        value={modalState.item.account_nature || 'REVENUE'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, account_nature: e.target.value } })}
                      >
                        <option value="REVENUE">Revenue</option>
                        <option value="RECEIPT">Receipt</option>
                        <option value="SUSPENSE">Suspense</option>
                        <option value="CLEARING">Clearing</option>
                        <option value="EXPENDITURE">Expenditure</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Reconciliation Rule Form */}
                {modalState.entity === 'rules' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Rule Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.rule_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, rule_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Evaluation Priority *</label>
                      <input
                        type="number"
                        required
                        min="1"
                        className="inp"
                        value={modalState.item.priority || 1}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, priority: Number(e.target.value) } })}
                      />
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Rule Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.rule_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, rule_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Primary Match Keys *</label>
                      <input
                        type="text"
                        required
                        className="inp mono"
                        value={modalState.item.primary_match_keys || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, primary_match_keys: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Matching Mode</label>
                      <select
                        className="inp"
                        value={modalState.item.matching_mode || 'THREE_WAY_EXACT'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, matching_mode: e.target.value } })}
                      >
                        <option value="THREE_WAY_EXACT">Three-Way Exact</option>
                        <option value="ONE_TO_MANY">One-to-Many Match</option>
                        <option value="SLA_AGEING">SLA Ageing Suspend</option>
                        <option value="ORPHAN_CREDIT">Orphan Credit (RAT)</option>
                        <option value="DUPLICATE_SCAN">Duplicate Scan</option>
                        <option value="AMOUNT_VARIANCE">Amount Variance</option>
                      </select>
                    </div>
                    <div className="fld">
                      <label>Outcome Status</label>
                      <select
                        className="inp"
                        value={modalState.item.outcome_status || 'Matched'}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, outcome_status: e.target.value } })}
                      >
                        <option value="Matched">Matched</option>
                        <option value="Matched (One-to-Many)">Matched (One-to-Many)</option>
                        <option value="Suspend">Suspend</option>
                        <option value="RAT">RAT</option>
                        <option value="Duplicate">Duplicate</option>
                        <option value="Mismatch">Mismatch</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Bank SLA Rule Form */}
                {modalState.entity === 'slaRules' && (
                  <div className="grid g2">
                    <div className="fld">
                      <label>Rule Code *</label>
                      <input
                        type="text"
                        required
                        className="inp uppercase mono"
                        value={modalState.item.rule_code || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, rule_code: e.target.value.toUpperCase() } })}
                        disabled={modalState.mode === 'edit'}
                      />
                    </div>
                    <div className="fld">
                      <label>Payment Modes *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.payment_mode || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, payment_mode: e.target.value } })}
                      />
                    </div>
                    <div className="fld" style={{ gridColumn: 'span 2' }}>
                      <label>Rule Name *</label>
                      <input
                        type="text"
                        required
                        className="inp"
                        value={modalState.item.rule_name || ''}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, rule_name: e.target.value } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Allowed SLA Remittance Days</label>
                      <input
                        type="number"
                        min="0"
                        className="inp"
                        value={modalState.item.allowed_remittance_days ?? 1}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, allowed_remittance_days: Number(e.target.value) } })}
                      />
                    </div>
                    <div className="fld">
                      <label>Penal Rate (% p.a.)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        className="inp"
                        value={modalState.item.annual_penal_rate_pct ?? 12.0}
                        onChange={e => setModalState({ ...modalState, item: { ...modalState.item, annual_penal_rate_pct: Number(e.target.value) } })}
                      />
                    </div>
                  </div>
                )}

                {/* Active Checkbox across all entities */}
                <div className="mt12 flex items-center gap8">
                  <label className="flex items-center gap8" style={{ cursor: 'pointer', fontSize: '13px' }}>
                    <input
                      type="checkbox"
                      checked={modalState.item.is_active !== false}
                      onChange={e => setModalState({ ...modalState, item: { ...modalState.item, is_active: e.target.checked } })}
                    />
                    <span><strong>Active Record</strong> (available for current business operations)</span>
                  </label>
                </div>
              </div>

              <div className="modal-f">
                <button
                  type="button"
                  className="btn btn-sm"
                  onClick={() => setModalState({ isOpen: false, mode: 'add', entity: '', item: null })}
                  disabled={modalSaving}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-p btn-sm" disabled={modalSaving}>
                  {modalSaving ? 'Saving to Database...' : modalState.mode === 'add' ? 'Create Record' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MastersPage;
