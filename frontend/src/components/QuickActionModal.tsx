import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { UserRole } from '../types';
import { api } from '../api/client';

const ROLE_NAMES: Record<UserRole, string> = {
  SYSADMIN: 'System Administrator',
  TRE_ADMIN: 'Treasury Administration',
  PAO_MAKER: 'PAO Maker',
  PAO_CHECK: 'PAO Checker',
  DDO: 'DDO / Department User',
  FINANCE: 'Finance Department User',
  BANK_OPS: 'Bank Operations User',
  AUDITOR: 'Auditor / Read-only',
  CITIZEN: 'Citizen / Payer View',
};

// Capability Matrix matching Prototype
const CAPS: Record<string, UserRole[]> = {
  'nav.dashboard': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'nav.collection': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'nav.upload': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'BANK_OPS', 'AUDITOR'],
  'nav.recon': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'AUDITOR'],
  'nav.exceptions': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'nav.sla': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'nav.refund': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'AUDITOR', 'CITIZEN'],
  'nav.devolution': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'AUDITOR'],
  'nav.accounting': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'FINANCE', 'AUDITOR'],
  'nav.reports': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'nav.masters': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'nav.audit': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'nav.help': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR', 'CITIZEN'],

  'upload.portal': ['PAO_MAKER', 'DDO', 'TRE_ADMIN', 'SYSADMIN'],
  'upload.bank': ['PAO_MAKER', 'BANK_OPS', 'TRE_ADMIN', 'SYSADMIN'],
  'upload.rbi': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
  'batch.approve': ['PAO_CHECK', 'TRE_ADMIN'],
  'batch.delete': ['SYSADMIN', 'TRE_ADMIN'],
  'collection.create': ['PAO_MAKER', 'DDO'],
  'collection.edit': ['PAO_MAKER', 'DDO'],
  'dept.validate': ['DDO', 'PAO_MAKER'],
  'recon.run': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
  'recon.commit': ['PAO_MAKER', 'TRE_ADMIN', 'SYSADMIN'],
  'recon.reset': ['TRE_ADMIN', 'SYSADMIN'],
  'override.propose': ['PAO_MAKER', 'TRE_ADMIN'],
  'override.approve': ['PAO_CHECK'],
  'exception.manage': ['PAO_MAKER', 'PAO_CHECK', 'TRE_ADMIN', 'DDO'],
  'exception.escalate': ['PAO_MAKER', 'PAO_CHECK', 'TRE_ADMIN'],
  'penalty.letter': ['PAO_MAKER', 'TRE_ADMIN'],
  'penalty.response': ['BANK_OPS', 'PAO_MAKER', 'TRE_ADMIN'],
  'penalty.waive': ['PAO_CHECK'],
  'refund.create': ['DDO', 'PAO_MAKER'],
  'refund.process': ['DDO', 'PAO_MAKER', 'FINANCE'],
  'refund.approve': ['PAO_CHECK'],
  'refund.pay': ['PAO_MAKER'],
  'devolution.create': ['DDO', 'PAO_MAKER'],
  'devolution.approve': ['PAO_CHECK'],
  'devolution.pay': ['PAO_MAKER'],
  'voucher.create': ['PAO_MAKER'],
  'voucher.approve': ['PAO_CHECK'],
  'masters.edit': ['SYSADMIN'],
  'config.edit': ['SYSADMIN'],
  'bizdate.edit': ['SYSADMIN'],
  'data.reset': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'],
  'export': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR'],
  'testsuite.run': ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER'],
};

const can = (role: UserRole, cap: string): boolean => {
  if (role === 'AUDITOR' && !cap.startsWith('nav.') && cap !== 'export') return false;
  const list = CAPS[cap];
  return !!(list && list.includes(role));
};

export const QuickActionModal: React.FC = () => {
  const {
    isQuickActionOpen,
    setIsQuickActionOpen,
    userRole,
    setActiveTab,
    showToast,
    triggerRefresh,
    addNotification,
  } = useApp();

  const [loading, setLoading] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsQuickActionOpen(!isQuickActionOpen);
      }
      if (e.key === 'Escape') {
        if (showResetConfirm) {
          setShowResetConfirm(false);
        } else if (isQuickActionOpen) {
          setIsQuickActionOpen(false);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isQuickActionOpen, showResetConfirm, setIsQuickActionOpen]);

  if (!isQuickActionOpen) return null;

  const currentRoleName = ROLE_NAMES[userRole] || userRole;

  const handleResetData = async () => {
    try {
      setResetting(true);
      await api.resetDemoData();
      showToast('Demo data reset and reconciled.', 'success');
      addNotification(
        'Demo environment ready',
        '16 portal, 19 bank and 18 RBI records loaded and reconciled. 6 exception(s) raised.',
        'ok'
      );
      triggerRefresh();
      setActiveTab('dashboard');
      setShowResetConfirm(false);
      setIsQuickActionOpen(false);
    } catch (e: any) {
      showToast(e.message || 'Failed to reset demo data', 'error');
    } finally {
      setResetting(false);
    }
  };

  const items = [
    {
      label: 'Upload Portal File',
      cap: 'upload.portal',
      fn: () => {
        setIsQuickActionOpen(false);
        setActiveTab('upload');
      },
    },
    {
      label: 'Upload Agency Bank Scroll',
      cap: 'upload.bank',
      fn: () => {
        setIsQuickActionOpen(false);
        setActiveTab('upload');
      },
    },
    {
      label: 'Upload RBI Luggage File',
      cap: 'upload.rbi',
      fn: () => {
        setIsQuickActionOpen(false);
        setActiveTab('upload');
      },
    },
    {
      label: 'Run Reconciliation',
      cap: 'recon.run',
      fn: async () => {
        try {
          setLoading(true);
          const res = await api.runReconciliation();
          showToast(
            `Reconciliation Run Complete: ${res.matched_count} matched, ${res.total_processed} processed`,
            'success'
          );
          addNotification(
            'Reconciliation run executed',
            `Processed ${res.total_processed} records: ${res.matched_count} matched, ${res.total_processed - res.matched_count} exceptions.`,
            'ok'
          );
          triggerRefresh();
          setIsQuickActionOpen(false);
          setActiveTab('recon');
        } catch (e: any) {
          showToast(e.message, 'error');
        } finally {
          setLoading(false);
        }
      },
    },
    {
      label: 'View Exceptions',
      cap: 'nav.exceptions',
      fn: () => {
        setIsQuickActionOpen(false);
        setActiveTab('exceptions');
      },
    },
    {
      label: 'Download Sample Files',
      cap: 'nav.help',
      fn: () => {
        setIsQuickActionOpen(false);
        setActiveTab('help');
      },
    },
    {
      label: 'Run Demo Test Suite',
      cap: 'testsuite.run',
      fn: async () => {
        try {
          setLoading(true);
          const res = await api.runTestSuite();
          showToast(
            `Demo Test Suite Completed: ${res.passed}/${res.total_tests} passed`,
            res.failed === 0 ? 'success' : 'warning'
          );
          triggerRefresh();
          setIsQuickActionOpen(false);
          setActiveTab('help');
        } catch (e: any) {
          showToast(e.message, 'error');
        } finally {
          setLoading(false);
        }
      },
    },
    {
      label: 'Reset Demo Data',
      cap: 'data.reset',
      fn: () => {
        setShowResetConfirm(true);
      },
    },
  ];

  return (
    <>
      <div
        className="ovl"
        role="dialog"
        aria-modal="true"
        onClick={() => setIsQuickActionOpen(false)}
      >
        <div
          className="modal w520"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Modal Header */}
          <div className="modal-h">
            <div>
              <h3>Quick Actions</h3>
              <div className="sub">Role: {currentRoleName}</div>
            </div>
            <button
              className="modal-x"
              aria-label="Close"
              onClick={() => setIsQuickActionOpen(false)}
            >
              &times;
            </button>
          </div>

          {/* Modal Body with 2-column Grid */}
          <div className="modal-b">
            <div className="grid g2">
              {items.map((it, idx) => {
                const isAllowed = can(userRole, it.cap);
                return (
                  <button
                    key={idx}
                    className={`btn ${isAllowed ? 'btn-p' : ''} btn-blk`}
                    disabled={!isAllowed || loading}
                    title={isAllowed ? '' : 'Not permitted for this role'}
                    onClick={() => it.fn()}
                  >
                    {it.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog for Reset Demo Data */}
      {showResetConfirm && (
        <div
          className="ovl"
          style={{ zIndex: 110 }}
          role="dialog"
          aria-modal="true"
          onClick={() => !resetting && setShowResetConfirm(false)}
        >
          <div
            className="modal w520"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-h">
              <div>
                <h3>Reset Demo Data</h3>
              </div>
              <button
                className="modal-x"
                aria-label="Close"
                onClick={() => !resetting && setShowResetConfirm(false)}
              >
                &times;
              </button>
            </div>
            <div className="modal-b">
              <div className="box err">
                <strong>
                  This will erase all uploaded batches, reconciliation results, exceptions, refunds,
                  devolution claims, vouchers and the audit trail.
                </strong>
                <p className="mt8 mb0">
                  The included demo datasets will be re-loaded, auto-approved and reconciled from
                  scratch. This action cannot be undone.
                </p>
              </div>
            </div>
            <div className="modal-f">
              <button
                className="btn"
                onClick={() => setShowResetConfirm(false)}
                disabled={resetting}
              >
                Cancel
              </button>
              <button
                className="btn btn-dgr"
                onClick={handleResetData}
                disabled={resetting}
              >
                {resetting ? 'Resetting...' : 'Reset everything'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
