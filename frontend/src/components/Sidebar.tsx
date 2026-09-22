import React, { useEffect, useState } from 'react';
import { useApp, can, CAPS, ROLE_NAMES } from '../context/AppContext';
import { api } from '../api/client';

interface NavSection {
  sec: string;
  items: {
    id: string;
    label: string;
    ico: string;
    cap: string;
    badgeKind?: 'exc' | 'pen' | 'ref';
  }[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    sec: 'MONITORING',
    items: [
      { id: 'dashboard', label: 'Dashboard', ico: '▦', cap: 'nav.dashboard' },
      { id: 'collection', label: 'Revenue Collection', ico: '₹', cap: 'nav.collection' },
    ],
  },
  {
    sec: 'SOURCE DATA & MATCHING',
    items: [
      { id: 'upload', label: 'Data Upload Centre', ico: '↑', cap: 'nav.upload' },
      { id: 'recon', label: 'Reconciliation Workbench', ico: '⇄', cap: 'nav.recon' },
      { id: 'exceptions', label: 'Exceptions & Investigation', ico: '⚠', cap: 'nav.exceptions', badgeKind: 'exc' },
      { id: 'sla', label: 'Bank SLA & Penal Interest', ico: '⏱', cap: 'nav.sla', badgeKind: 'pen' },
    ],
  },
  {
    sec: 'OUTFLOWS & SETTLEMENT',
    items: [
      { id: 'refunds', label: 'Refund Management', ico: '↩', cap: 'nav.refund', badgeKind: 'ref' },
      { id: 'devolution', label: 'Revenue Devolution', ico: '⚔', cap: 'nav.devolution' },
      { id: 'accounting', label: 'Accounting & Receipt Booking', ico: '≡', cap: 'nav.accounting' },
    ],
  },
  {
    sec: 'GOVERNANCE',
    items: [
      { id: 'reports', label: 'Reports & MIS', ico: '▤', cap: 'nav.reports' },
      { id: 'masters', label: 'Masters & Configuration', ico: '⚙', cap: 'nav.masters' },
      { id: 'audit', label: 'Audit Trail', ico: '☷', cap: 'nav.audit' },
      { id: 'help', label: 'Help / Sample Formats', ico: '?', cap: 'nav.help' },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, userRole, businessDate, refreshKey } = useApp();
  const [badgeCounts, setBadgeCounts] = useState<{ exc: number; pen: number; ref: number }>({
    exc: 6,
    pen: 2,
    ref: 3,
  });

  const [explainModal, setExplainModal] = useState<{
    label: string;
    cap: string;
  } | null>(null);

  useEffect(() => {
    // Fetch live badge counts
    const fetchCounts = async () => {
      try {
        const [excs, slas, refs] = await Promise.allSettled([
          api.getExceptions(),
          api.getPenalClaims(),
          api.getRefunds(),
        ]);
        setBadgeCounts({
          exc: excs.status === 'fulfilled' ? (excs.value as any).items?.length ?? 6 : 6,
          pen: slas.status === 'fulfilled' ? (slas.value as any).items?.length ?? 2 : 2,
          ref: refs.status === 'fulfilled' ? (refs.value as any).items?.length ?? 3 : 3,
        });
      } catch (e) {
        // keep defaults
      }
    };
    fetchCounts();
  }, [refreshKey]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && explainModal) {
        setExplainModal(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [explainModal]);

  const currentRoleName = ROLE_NAMES[userRole] || userRole;

  return (
    <>
      <aside
        id="sidebar"
        className="w-[250px] flex-none bg-gradient-to-b from-[#0b2340] to-[#0f2d52] text-[#cfdcec] flex flex-col fixed top-0 bottom-0 left-0 z-40 select-none shadow-lg"
        style={{ width: '250px' }}
      >
        {/* Brand Header */}
        <div className="h-[60px] px-4 border-b border-white/10 flex items-center gap-2.5">
          <div className="w-[34px] h-[34px] rounded-[7px] bg-gradient-to-br from-[#0f8878] to-[#2660a4] flex items-center justify-center font-bold text-white text-[13px] tracking-wider flex-none shadow-inner">
            IF
          </div>
          <div>
            <div className="text-white font-bold text-[14px] leading-tight tracking-[0.3px]">IFMS</div>
            <div className="text-[#8fa9c6] text-[10px] uppercase font-semibold tracking-[0.6px]">
              Revenue &amp; Reconciliation
            </div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 overflow-y-auto py-2 custom-sidebar-scroll">
          {NAV_SECTIONS.map((sec) => (
            <div key={sec.sec}>
              <div className="nav-sec">{sec.sec}</div>
              {sec.items.map((item) => {
                const isAllowed = can(userRole, item.cap);
                const isActive =
                  isAllowed &&
                  (activeTab === item.id ||
                    (item.id === 'refunds' && (activeTab === 'refund' || activeTab === 'citizen')));
                const count = item.badgeKind ? badgeCounts[item.badgeKind] : 0;

                return (
                  <div
                    key={item.id}
                    role="link"
                    tabIndex={0}
                    title={
                      isAllowed
                        ? item.label
                        : 'Not available for the selected role — click to see which roles can open it'
                    }
                    onClick={() => {
                      if (isAllowed) {
                        setActiveTab(item.id);
                      } else {
                        setExplainModal({ label: item.label, cap: item.cap });
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        if (isAllowed) {
                          setActiveTab(item.id);
                        } else {
                          setExplainModal({ label: item.label, cap: item.cap });
                        }
                      }
                    }}
                    className={`nav-item ${isActive ? 'active' : ''} ${!isAllowed ? 'locked' : ''}`}
                  >
                    <span className="ico">{item.ico}</span>
                    <span className="truncate">{item.label}</span>
                    {isAllowed && count > 0 && <span className="badge-n">{count}</span>}
                  </div>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-3 px-4 border-t border-white/10 text-[10.5px] text-[#7f9ab8] bg-[#0b2340]/40">
          <div>Prototype build 1.0 &middot; Offline</div>
          <div className="mt-0.5 font-mono">Demo business date: {businessDate || '15-Sep-2026'}</div>
        </div>
      </aside>

      {/* Restricted Screen Modal (Matches Prototype 1:1) */}
      {explainModal && (
        <div
          className="ovl"
          role="dialog"
          aria-modal="true"
          onClick={() => setExplainModal(null)}
        >
          <div
            className="modal w520"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="modal-h">
              <div>
                <h3>{explainModal.label} — not available for your role</h3>
              </div>
              <button
                className="modal-x"
                aria-label="Close"
                onClick={() => setExplainModal(null)}
              >
                &times;
              </button>
            </div>

            {/* Modal Body */}
            <div className="modal-b">
              <div className="box warn">
                <strong>Your active role is {currentRoleName}.</strong>
                <p className="mb0 mt8">
                  This screen is restricted. Switch the role in the header to one of the following to open it:
                </p>
              </div>
              <ul className="mt12 space-y-1 text-[13px] text-[#1f2730] list-disc list-inside">
                {(CAPS[explainModal.cap] || []).map((r) => (
                  <li key={r}>{ROLE_NAMES[r] || r}</li>
                ))}
              </ul>
            </div>

            {/* Modal Footer */}
            <div className="modal-f">
              <button
                className="btn"
                onClick={() => setExplainModal(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
