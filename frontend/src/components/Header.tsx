import React from 'react';
import { useApp } from '../context/AppContext';
import { UserRole } from '../types';

const ROUTE_TITLE: Record<string, string> = {
  dashboard: 'Revenue Dashboard',
  collection: 'Revenue Collection Register',
  upload: 'Data Upload Centre',
  recon: 'Reconciliation Workbench',
  exceptions: 'Exceptions & Investigation',
  sla: 'Bank SLA & Penal Interest',
  refund: 'Refund Management',
  refunds: 'Refund Management',
  citizen: 'Citizen / Payer View',
  devolution: 'Revenue Devolution',
  accounting: 'Accounting & Receipt Booking',
  reports: 'Reports & MIS',
  masters: 'Masters & Configuration',
  audit: 'Audit Trail',
  help: 'Help & Sample File Formats',
};

const ROLES: { code: UserRole; name: string; short: string }[] = [
  { code: 'SYSADMIN', name: 'System Administrator', short: 'SA' },
  { code: 'TRE_ADMIN', name: 'Treasury Administration', short: 'TA' },
  { code: 'PAO_MAKER', name: 'PAO Maker', short: 'PM' },
  { code: 'PAO_CHECK', name: 'PAO Checker', short: 'PC' },
  { code: 'DDO', name: 'DDO / Department User', short: 'DU' },
  { code: 'FINANCE', name: 'Finance Department User', short: 'FD' },
  { code: 'BANK_OPS', name: 'Bank Operations User', short: 'BO' },
  { code: 'AUDITOR', name: 'Auditor / Read-only', short: 'AU' },
  { code: 'CITIZEN', name: 'Citizen / Payer View', short: 'CP' },
];

export const Header: React.FC = () => {
  const {
    activeTab,
    userRole,
    setUserRole,
    financialYear,
    setFinancialYear,
    businessDate,
    setIsQuickActionOpen,
    unreadNotificationsCount,
    setIsNotificationOpen,
  } = useApp();

  const currentTitle = ROUTE_TITLE[activeTab] || 'Revenue Dashboard';
  const activeRoleObj = ROLES.find((r) => r.code === userRole) || ROLES[1];

  return (
    <header
      id="header"
      className="h-[60px] bg-white border-b border-[#e1e7ee] flex items-center justify-between gap-3.5 px-4.5 sticky top-0 z-30 shadow-[0_1px_2px_rgba(16,32,54,0.08)] px-5"
    >
      {/* Dynamic Page Title on Left */}
      <div className="text-[15px] font-semibold text-[#0b2340] truncate">
        {currentTitle}
      </div>

      {/* Header Right Controls */}
      <div className="flex items-center gap-3 ml-auto">
        {/* FY Selector Chip */}
        <span
          className="inline-flex items-center gap-1.5 bg-[#f2f6fb] border border-[#e5edf6] text-[#143a68] px-2.5 py-1 rounded-full text-[11.5px] font-semibold whitespace-nowrap"
          title="Financial Year"
        >
          FY
          <select
            value={financialYear}
            onChange={(e) => setFinancialYear(e.target.value)}
            className="border-0 p-0 font-bold bg-transparent text-[#143a68] cursor-pointer outline-none text-[11.5px]"
          >
            <option value="2026-27">2026-27</option>
            <option value="2025-26">2025-26</option>
            <option value="2024-25">2024-25</option>
          </select>
        </span>

        {/* Business Date Chip */}
        <span
          className="inline-flex items-center gap-1.5 bg-[#f2f6fb] border border-[#e5edf6] text-[#143a68] px-2.5 py-1 rounded-full text-[11.5px] font-semibold whitespace-nowrap"
          title="Demo business date used by the reconciliation engine"
        >
          📅 <span>{businessDate || '15-Sep-2026'}</span>
        </span>

        {/* Active Role Dropdown */}
        <select
          value={userRole}
          onChange={(e) => setUserRole(e.target.value as UserRole)}
          className="border border-[#cbd3dd] rounded-[6px] py-1 px-2 text-[12px] bg-white text-[#1f2730] outline-none cursor-pointer max-w-[210px] font-medium"
          title="Active role"
        >
          {ROLES.map((r) => (
            <option key={r.code} value={r.code}>
              {r.name}
            </option>
          ))}
        </select>

        {/* Notifications Bell */}
        <div
          onClick={() => setIsNotificationOpen(true)}
          className="relative cursor-pointer text-[17px] text-[#5f6b7a] p-1 px-1.5 rounded-[6px] hover:bg-[#eef2f7] transition-colors"
          title="Notifications"
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              setIsNotificationOpen(true);
            }
          }}
        >
          🔔
          {unreadNotificationsCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-[#c92a2a] text-white text-[9.5px] font-bold rounded-full px-1 leading-3.5 min-w-[15px] text-center">
              {unreadNotificationsCount}
            </span>
          )}
        </div>

        {/* Quick Actions Button */}
        <button
          onClick={() => setIsQuickActionOpen(true)}
          className="inline-flex items-center justify-center gap-1.5 border border-[#1b4a83] bg-[#1b4a83] text-white py-1 px-3 rounded-[6px] text-[12.5px] font-semibold cursor-pointer whitespace-nowrap hover:bg-[#143a68] transition-colors shadow-xs"
          title="Quick actions (Ctrl+K)"
        >
          ⚡ Quick Actions
        </button>

        {/* User Role Avatar */}
        <div
          className="w-8 h-8 rounded-full bg-[#1b4a83] text-white flex items-center justify-center font-bold text-[12px] flex-none shadow-xs"
          title={`Signed-in Persona: ${activeRoleObj.name} (${userRole})`}
        >
          {activeRoleObj.short}
        </div>
      </div>
    </header>
  );
};

