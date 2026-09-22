import React from 'react';

interface MoneyTextProps {
  amount: number | string | null | undefined;
  currency?: boolean;
  className?: string;
  decimals?: number;
}

export const formatIndianRupees = (val: number | string | null | undefined, decimals = 2): string => {
  if (val === null || val === undefined || isNaN(Number(val))) {
    return '0.00';
  }
  const num = Number(val);
  return num.toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const MoneyText: React.FC<MoneyTextProps> = ({
  amount,
  currency = true,
  className = '',
  decimals = 2,
}) => {
  const formatted = formatIndianRupees(amount, decimals);
  return (
    <span className={`font-mono font-medium ${className}`}>
      {currency ? '₹ ' : ''}
      {formatted}
    </span>
  );
};
