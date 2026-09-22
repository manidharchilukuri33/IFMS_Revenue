import React from 'react';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const getStyle = (st: string) => {
    switch (st) {
      // Recon statuses
      case 'Matched':
      case 'APPROVED':
      case 'PROCESSED':
      case 'Approved':
      case 'Paid':
      case 'Settled':
      case 'PASS':
      case 'Posted':
      case 'CLEARED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20';

      case 'Pending':
      case 'PENDING_APPROVAL':
      case 'Submitted':
      case 'Under Verification':
      case 'Bill Prepared':
      case 'Pending PAO Approval':
      case 'Payment Instructed':
      case 'Open':
      case 'Draft':
      case 'COMPUTED':
      case 'DEMAND_ISSUED':
      case 'HELD':
        return 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-600/20';

      case 'Suspend':
      case 'RAT':
      case 'Assigned':
      case 'Escalated':
      case 'Deficiency Raised':
      case 'DISPUTED':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200 ring-indigo-600/20';

      case 'Mismatch':
      case 'Duplicate':
      case 'REJECTED':
      case 'Rejected':
      case 'FAIL':
      case 'Critical':
      case 'High':
        return 'bg-rose-50 text-rose-700 border-rose-200 ring-rose-600/20';

      case 'Medium':
      case 'Low':
      case 'Under Investigation':
      case 'Partially Matched':
      case 'Resolved':
      case 'Closed':
      case 'WAIVED':
      case 'REMITTED':
      case 'TRANSFERRED':
        return 'bg-slate-50 text-slate-700 border-slate-200 ring-slate-600/20';

      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ring-1 ring-inset ${getStyle(
        status
      )} ${className}`}
    >
      {status}
    </span>
  );
};
