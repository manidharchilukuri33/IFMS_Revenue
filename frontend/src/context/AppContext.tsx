import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserRole, SystemConfig, NotificationItem } from '../types';
import { api } from '../api/client';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning' | 'ok' | 'err' | 'warn';
  text: string;
}


export const formatNotificationTimestamp = (d: Date = new Date()): string => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const day = String(d.getDate()).padStart(2, '0');
  const month = months[d.getMonth()];
  const year = d.getFullYear();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');
  return `${day}-${month}-${year} ${hours}:${minutes}:${seconds}`;
};

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'NTF-00006',
    ts: '19-Sep-2026 10:41:54',
    title: 'Reconciliation exceptions raised',
    text: '1 suspense, 1 RAT, 1 mismatch and 1 duplicate case(s) require action.',
    level: 'warn',
    read: false,
  },
  {
    id: 'NTF-00005',
    ts: '19-Sep-2026 10:41:54',
    title: 'Demo environment ready',
    text: '16 portal, 19 bank and 18 RBI records loaded and reconciled. 6 exception(s) raised.',
    level: 'ok',
    read: false,
  },
  {
    id: 'NTF-00004',
    ts: '19-Sep-2026 10:41:54',
    title: 'Reconciliation exceptions raised',
    text: '1 suspense, 1 RAT, 1 mismatch and 1 duplicate case(s) require action.',
    level: 'warn',
    read: false,
  },
  {
    id: 'NTF-00003',
    ts: '19-Sep-2026 10:41:54',
    title: 'Upload batch UPB-RBI-2026-0003 posted',
    text: '18 record(s) totalling ₹ 10,88,700.00 awaiting PAO Checker approval.',
    level: 'info',
    read: false,
  },
  {
    id: 'NTF-00002',
    ts: '19-Sep-2026 10:41:54',
    title: 'Upload batch UPB-BNK-2026-0002 posted',
    text: '19 record(s) totalling ₹ 11,03,700.00 awaiting PAO Checker approval.',
    level: 'info',
    read: false,
  },
  {
    id: 'NTF-00001',
    ts: '19-Sep-2026 10:41:54',
    title: 'Upload batch UPB-PRT-2026-0001 posted',
    text: '16 record(s) totalling ₹ 11,05,700.00 awaiting PAO Checker approval.',
    level: 'info',
    read: false,
  },
];

interface AppContextType {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  userRole: UserRole;
  setUserRole: (role: UserRole) => void;
  financialYear: string;
  setFinancialYear: (fy: string) => void;
  businessDate: string;
  setBusinessDate: (date: string) => void;
  toasts: ToastMessage[];
    showToast: (text: string, type?: 'success' | 'error' | 'info' | 'warning' | 'ok' | 'err' | 'warn') => void;
  removeToast: (id: string) => void;
  systemConfig: SystemConfig | null;
  refreshSystemConfig: () => Promise<void>;
  refreshKey: number;
  triggerRefresh: () => void;
  isQuickActionOpen: boolean;
  setIsQuickActionOpen: (open: boolean) => void;
  notifications: NotificationItem[];
  unreadNotificationsCount: number;
  isNotificationOpen: boolean;
  setIsNotificationOpen: (open: boolean) => void;
  addNotification: (title: string, text: string, level?: 'ok' | 'warn' | 'err' | 'info') => void;
  markAllNotificationsRead: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const ROLE_NAMES: Record<UserRole, string> = {
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

export const CAPS: Record<string, UserRole[]> = {
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
};

export const can = (role: UserRole, cap: string): boolean => {
  if (role === 'AUDITOR' && !cap.startsWith('nav.') && cap !== 'export') return false;
  const list = CAPS[cap];
  return !!(list && list.includes(role));
};

export const ROUTE_CAPS: Record<string, string> = {
  dashboard: 'nav.dashboard',
  collection: 'nav.collection',
  upload: 'nav.upload',
  recon: 'nav.recon',
  exceptions: 'nav.exceptions',
  sla: 'nav.sla',
  refund: 'nav.refund',
  refunds: 'nav.refund',
  citizen: 'nav.refund',
  devolution: 'nav.devolution',
  accounting: 'nav.accounting',
  reports: 'nav.reports',
  masters: 'nav.masters',
  audit: 'nav.audit',
  help: 'nav.help',
};

export const firstAllowedRoute = (role: UserRole): string => {
  const routes = [
    { r: 'dashboard', cap: 'nav.dashboard' },
    { r: 'collection', cap: 'nav.collection' },
    { r: 'upload', cap: 'nav.upload' },
    { r: 'recon', cap: 'nav.recon' },
    { r: 'exceptions', cap: 'nav.exceptions' },
    { r: 'sla', cap: 'nav.sla' },
    { r: 'refunds', cap: 'nav.refund' },
    { r: 'devolution', cap: 'nav.devolution' },
    { r: 'accounting', cap: 'nav.accounting' },
    { r: 'reports', cap: 'nav.reports' },
    { r: 'masters', cap: 'nav.masters' },
    { r: 'audit', cap: 'nav.audit' },
    { r: 'help', cap: 'nav.help' },
  ];
  for (const item of routes) {
    if (can(role, item.cap)) return item.r;
  }
  return 'help';
};

const getInitialTab = (): string => {
  if (typeof window !== 'undefined') {
    try {
      const hash = window.location.hash.replace('#', '').trim();
      if (hash && ROUTE_CAPS[hash]) {
        return hash;
      }
      const saved = localStorage.getItem('ifms_active_tab');
      if (saved && ROUTE_CAPS[saved]) {
        return saved;
      }
    } catch (e) {}
  }
  return 'dashboard';
};

const getInitialRole = (): UserRole => {
  if (typeof window !== 'undefined') {
    try {
      const saved = localStorage.getItem('ifms_user_role') as UserRole;
      if (saved && ['SYSADMIN', 'TRE_ADMIN', 'PAO_MAKER', 'PAO_CHECK', 'DDO', 'FINANCE', 'BANK_OPS', 'AUDITOR', 'CITIZEN'].includes(saved)) {
        return saved;
      }
    } catch (e) {}
  }
  return 'SYSADMIN';
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTabState] = useState<string>(getInitialTab);
  const [userRole, setUserRoleState] = useState<UserRole>(getInitialRole);
  const [financialYear, setFinancialYearState] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('ifms_financial_year');
        if (saved) return saved;
      } catch (e) {}
    }
    return '2026-27';
  });
  const [businessDate, setBusinessDateState] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('ifms_business_date');
        if (saved) return saved;
      } catch (e) {}
    }
    return '2026-09-15';
  });
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const [isQuickActionOpen, setIsQuickActionOpen] = useState<boolean>(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>(INITIAL_NOTIFICATIONS);
  const [isNotificationOpen, setIsNotificationOpen] = useState<boolean>(false);

  const unreadNotificationsCount = notifications.filter((n) => !n.read).length;

  const setActiveTab = (tab: string) => {
    setActiveTabState(tab);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('ifms_active_tab', tab);
        if (window.location.hash !== `#${tab}`) {
          window.location.hash = `#${tab}`;
        }
      } catch (e) {}
    }
  };

  const setFinancialYear = (fy: string) => {
    setFinancialYearState(fy);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('ifms_financial_year', fy);
      } catch (e) {}
    }
  };

  const setBusinessDate = (dt: string) => {
    setBusinessDateState(dt);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('ifms_business_date', dt);
      } catch (e) {}
    }
  };

  const fetchNotifications = async (role?: UserRole) => {
    try {
      const activeRole = role || userRole;
      const res = await api.getNotifications(activeRole);
      if (res && Array.isArray(res.notifications)) {
        setNotifications(res.notifications);
      }
    } catch (e) {
      console.warn('Backend notification fetch fallback to local state:', e);
    }
  };

  const setUserRole = (role: UserRole) => {
    setUserRoleState(role);
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('ifms_user_role', role);
      } catch (e) {}
    }
    api.setRole(role, role === 'PAO_CHECK' ? 2 : role === 'PAO_MAKER' ? 3 : 1);
    fetchNotifications(role);

    // Auto-switch to first allowed route if the current screen is restricted for the new role
    const currentCap = ROUTE_CAPS[activeTab] || 'nav.dashboard';
    if (!can(role, currentCap)) {
      const targetRoute = firstAllowedRoute(role);
      setActiveTab(targetRoute);
    }

    const name = ROLE_NAMES[role] || role;
    showToast(`Active role: ${name}.`, 'info');
  };

  // Sync with browser URL hash change (back/forward buttons)
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const onHashChange = () => {
      const hash = window.location.hash.replace('#', '').trim();
      if (hash && ROUTE_CAPS[hash] && hash !== activeTab) {
        setActiveTabState(hash);
        try {
          localStorage.setItem('ifms_active_tab', hash);
        } catch (e) {}
      }
    };

    window.addEventListener('hashchange', onHashChange);
    // Ensure initial hash matches active tab
    if (!window.location.hash && activeTab) {
      window.location.hash = `#${activeTab}`;
    }

    return () => window.removeEventListener('hashchange', onHashChange);
  }, [activeTab]);


  const showToast = (
    text: string,
    type: 'success' | 'error' | 'info' | 'warning' | 'ok' | 'err' | 'warn' = 'ok'
  ) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, text }]);
    setTimeout(() => {
      removeToast(id);
    }, 4200);
  };


  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const triggerRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  const addNotification = async (
    title: string,
    text: string,
    level: 'ok' | 'warn' | 'err' | 'info' = 'info',
    targetRole?: string,
    actionModule?: string,
    referenceId?: string
  ) => {
    const id = `NTF-${Date.now().toString().slice(-5)}`;
    const newNtf: NotificationItem = {
      id,
      ts: formatNotificationTimestamp(),
      title,
      text,
      level,
      read: false,
    };
    setNotifications((prev) => [newNtf, ...prev]);

    try {
      await api.createNotification({
        title,
        text,
        level,
        target_role: targetRole,
        action_module: actionModule,
        reference_id: referenceId,
      });
    } catch (e) {
      console.warn('Could not persist notification to backend:', e);
    }
  };

  const markAllNotificationsRead = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try {
      await api.markNotificationsRead(undefined, userRole);
    } catch (e) {
      console.warn('Could not mark notifications read in backend:', e);
    }
    showToast('All notifications marked as read', 'info');
  };

  const refreshSystemConfig = async () => {
    try {
      const cfg = await api.getSystemConfig();
      setSystemConfig(cfg);
      if (cfg.demo_business_date) setBusinessDate(cfg.demo_business_date);
      if (cfg.current_financial_year) setFinancialYear(cfg.current_financial_year);
    } catch (e) {
      console.error('Failed to load system config', e);
    }
  };

  useEffect(() => {
    refreshSystemConfig();
    fetchNotifications(userRole);
  }, [userRole, refreshKey]);

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        userRole,
        setUserRole,
        financialYear,
        setFinancialYear,
        businessDate,
        setBusinessDate,
        toasts,
        showToast,
        removeToast,
        systemConfig,
        refreshSystemConfig,
        refreshKey,
        triggerRefresh,
        isQuickActionOpen,
        setIsQuickActionOpen,
        notifications,
        unreadNotificationsCount,
        isNotificationOpen,
        setIsNotificationOpen,
        addNotification,
        markAllNotificationsRead,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

