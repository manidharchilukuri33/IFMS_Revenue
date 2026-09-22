import React from 'react';
import { useApp } from '../context/AppContext';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useApp();

  if (toasts.length === 0) return null;

  return (
    <div id="toasts" aria-live="polite" aria-atomic="true">
      {toasts.map((toast) => {
        const kind =
          toast.type === 'success' || toast.type === 'ok'
            ? 'ok'
            : toast.type === 'error' || toast.type === 'err'
            ? 'err'
            : toast.type === 'warning' || toast.type === 'warn'
            ? 'warn'
            : 'info';

        const icon =
          kind === 'ok' ? '\u2714' : kind === 'err' ? '\u2716' : kind === 'warn' ? '\u26A0' : '\u2139';

        return (
          <div
            key={toast.id}
            className={`toast ${kind}`}
            role="alert"
            onClick={() => removeToast(toast.id)}
            title="Click to dismiss"
            style={{ cursor: 'pointer' }}
          >
            <span style={{ fontWeight: 700, flexShrink: 0, minWidth: '14px', textAlign: 'center', fontSize: '13px' }}>
              {icon}
            </span>
            <span style={{ flex: '1 1 auto', wordBreak: 'break-word', lineHeight: '1.4' }}>
              {toast.text}
            </span>
          </div>
        );
      })}
    </div>
  );
};

