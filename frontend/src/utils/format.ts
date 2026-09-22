// Format and CSV export utilities matching prototype standards (DD-MM-YYYY date format)

export function money(val: number | string | null | undefined): string {
  if (val === null || val === undefined || val === '') return '₹ 0.00';
  const num = Number(val);
  if (isNaN(num)) return '₹ 0.00';
  return '₹ ' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function plain(val: number | string | null | undefined, dec = 2): string {
  if (val === null || val === undefined || val === '') return '0';
  const num = Number(val);
  if (isNaN(num)) return '0';
  return num.toFixed(dec);
}

export function cnt(val: number | string | null | undefined): string {
  if (val === null || val === undefined || val === '') return '0';
  const num = Number(val);
  if (isNaN(num)) return '0';
  return num.toLocaleString('en-IN');
}

export function compact(val: number | string | null | undefined): string {
  if (val === null || val === undefined || val === '') return '₹ 0.00';
  const num = Number(val);
  if (isNaN(num)) return '₹ 0.00';
  const abs = Math.abs(num);
  if (abs >= 10000000) {
    return '₹ ' + (num / 10000000).toFixed(2) + ' Cr';
  }
  if (abs >= 100000) {
    return '₹ ' + (num / 100000).toFixed(2) + ' L';
  }
  if (abs >= 1000) {
    return '₹ ' + (num / 1000).toFixed(2) + ' K';
  }
  return '₹ ' + num.toFixed(2);
}

/**
 * Formats any ISO date, timestamp, or date string into DD-MM-YYYY format.
 * Example: '2026-09-15' -> '15-09-2026'
 */
export function fmtDate(d: string | number | Date | null | undefined): string {
  if (!d) return '—';
  if (d instanceof Date) {
    if (isNaN(d.getTime())) return '—';
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}-${month}-${year}`;
  }

  const str = String(d).trim();
  if (!str || str === 'null' || str === 'undefined') return '—';

  // Match YYYY-MM-DD (optionally with time)
  const isoMatch = str.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (isoMatch) {
    const y = isoMatch[1];
    const m = isoMatch[2].padStart(2, '0');
    const day = isoMatch[3].padStart(2, '0');
    return `${day}-${m}-${y}`;
  }

  // Match DD-MM-YYYY or DD/MM/YYYY
  const dmyMatch = str.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/);
  if (dmyMatch) {
    const day = dmyMatch[1].padStart(2, '0');
    const m = dmyMatch[2].padStart(2, '0');
    const y = dmyMatch[3];
    return `${day}-${m}-${y}`;
  }

  // Fallback to Date parsing
  const parsed = new Date(str);
  if (!isNaN(parsed.getTime())) {
    const day = String(parsed.getDate()).padStart(2, '0');
    const month = String(parsed.getMonth() + 1).padStart(2, '0');
    const year = parsed.getFullYear();
    return `${day}-${month}-${year}`;
  }

  return str;
}

/**
 * Formats a date into DD-MM-YYYY format (alias for fmtDate).
 */
export function fmtDateDash(d: string | number | Date | null | undefined): string {
  return fmtDate(d);
}

/**
 * Formats timestamp into DD-MM-YYYY HH:mm:ss format.
 */
export function fmtStamp(s: string | number | Date | null | undefined): string {
  if (!s) return '—';
  if (s instanceof Date) {
    const dStr = fmtDate(s);
    const tStr = s.toTimeString().slice(0, 8);
    return `${dStr} ${tStr}`;
  }
  const str = String(s).trim();
  if (!str || str === 'null' || str === 'undefined') return '—';

  if (str.includes('T')) {
    const parts = str.split('T');
    const d = fmtDate(parts[0]);
    const t = parts[1].slice(0, 8);
    return `${d} ${t}`;
  }
  if (str.includes(' ')) {
    const parts = str.split(' ');
    const d = fmtDate(parts[0]);
    const t = (parts[1] || '').slice(0, 8);
    return `${d} ${t}`.trim();
  }

  return fmtDate(str);
}

export function badgeClass(status: string | null | undefined): string {
  if (!status) return 'badge b-grey';
  const s = String(status).toLowerCase();
  if (s.includes('match') || s.includes('approved') || s.includes('paid') || s.includes('validated') || s.includes('settled') || s.includes('closed') || s.includes('active') || s.includes('confirmed') || s.includes('remitted')) {
    return 'badge b-green';
  }
  if (s.includes('pending') || s.includes('suspend') || s.includes('scrutiny') || s.includes('bill') || s.includes('under') || s.includes('draft') || s.includes('issued') || s.includes('normal')) {
    return 'badge b-amber';
  }
  if (s.includes('mismatch') || s.includes('duplicate') || s.includes('reject') || s.includes('fail') || s.includes('critical') || s.includes('overdue') || s.includes('high') || s.includes('blocked') || s.includes('not received') || s.includes('not credited')) {
    return 'badge b-red';
  }
  if (s.includes('rat') || s.includes('judicial') || s.includes('outstanding') || s.includes('waived')) {
    return 'badge b-violet';
  }
  if (s.includes('portal') || s.includes('action') || s.includes('non-judicial')) {
    return 'badge b-blue';
  }
  return 'badge b-grey';
}

export function exportCSV(filename: string, headers: string[], rows: any[][], meta?: [string, string][]) {
  let content = '';
  if (meta && meta.length > 0) {
    meta.forEach(([k, v]) => {
      content += `# ${k}: ${v}\n`;
    });
    content += '\n';
  }
  content += headers.map(h => `"${String(h).replace(/"/g, '""')}"`).join(',') + '\n';
  rows.forEach(r => {
    content += r.map(cell => {
      if (cell === null || cell === undefined) return '""';
      const str = String(cell);
      return `"${str.replace(/"/g, '""')}"`;
    }).join(',') + '\n';
  });

  downloadText(filename, content);
}

export function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
