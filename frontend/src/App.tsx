import React from 'react';
import { useApp } from './context/AppContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ToastContainer } from './components/ToastContainer';
import { QuickActionModal } from './components/QuickActionModal';
import { NotificationModal } from './components/NotificationModal';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { CollectionPage } from './pages/CollectionPage';
import { UploadPage } from './pages/UploadPage';
import { ReconPage } from './pages/ReconPage';
import { ExceptionsPage } from './pages/ExceptionsPage';
import { SlaPenalPage } from './pages/SlaPenalPage';
import { RefundsPage } from './pages/RefundsPage';
import { CitizenPage } from './pages/CitizenPage';
import { DevolutionPage } from './pages/DevolutionPage';
import { AccountingPage } from './pages/AccountingPage';
import { ReportsPage } from './pages/ReportsPage';
import { MastersPage } from './pages/MastersPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { HelpTestPage } from './pages/HelpTestPage';

export const App: React.FC = () => {
  const { activeTab, userRole } = useApp();

  const renderActivePage = () => {
    // If citizen role is active and user is on refund/citizen tab, show citizen tracker
    if (userRole === 'CITIZEN' && (activeTab === 'refunds' || activeTab === 'citizen')) {
      return <CitizenPage />;
    }

    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'collection':
        return <CollectionPage />;
      case 'upload':
        return <UploadPage />;
      case 'recon':
        return <ReconPage />;
      case 'exceptions':
        return <ExceptionsPage />;
      case 'sla':
        return <SlaPenalPage />;
      case 'refund':
      case 'refunds':
        return <RefundsPage />;
      case 'citizen':
        return <CitizenPage />;
      case 'devolution':
        return <DevolutionPage />;
      case 'accounting':
        return <AccountingPage />;
      case 'reports':
        return <ReportsPage />;
      case 'masters':
        return <MastersPage />;
      case 'audit':
        return <AuditTrailPage />;
      case 'help':
        return <HelpTestPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="min-h-screen bg-[#eef2f7] flex font-sans text-[#1f2730] text-[13.5px]">
      {/* Fixed Left Sidebar (250px) */}
      <Sidebar />

      {/* Main Content Area with Left Margin 250px */}
      <div className="flex-1 flex flex-col min-w-0 ml-[250px] min-h-screen">
        {/* Top Header Fixed */}
        <Header />

        {/* Page Content */}
        <main className="flex-1 p-[16px_18px_48px] overflow-y-auto">
          {renderActivePage()}
        </main>
      </div>

      <ToastContainer />
      <QuickActionModal />
      <NotificationModal />
    </div>
  );
};
export default App;

