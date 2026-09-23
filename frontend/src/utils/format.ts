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

export interface PrintableLetterParams {
  letterNo?: string;
  date?: string;
  recipientName: string;
  recipientAddress: string;
  recipientType?: string;
  subject: string;
  body: string;
  challan: string;
  cin?: string;
  cpin?: string;
  payer: string;
  source: string;
  dept: string;
  pao: string;
  portalAmt: number;
  bankAmt: number;
  rbiAmt: number;
  diff: number;
  slaDelay?: number;
  penal?: number;
  revId: string;
}

export function printOfficialLetter(params: PrintableLetterParams) {
  const printWindow = window.open('', '_blank', 'width=900,height=1000');
  if (!printWindow) {
    window.print();
    return;
  }

  const dateStr = params.date ? fmtDate(params.date) : fmtDate(new Date());
  const refNo = params.letterNo || `LTR-DISC-${new Date().toISOString().slice(0, 10).replace(/[^0-9]/g, '')}-000001`;

  // Clean body text by stripping redundant To/Subject prefixes if present
  let cleanBody = params.body || '';
  cleanBody = cleanBody.replace(/^To,[\s\S]*?Sir \/ Madam,\n\n/i, '');
  cleanBody = cleanBody.replace(/^--- RECEIPT TRANSACTION[\s\S]*?--- DETAILED DISCREPANCY BREAKDOWN ---\n/i, '');
  cleanBody = cleanBody.replace(/^--- EXCEPTION TRANSACTION[\s\S]*?--- DETAILED DISCREPANCY BREAKDOWN ---\n/i, '');
  cleanBody = cleanBody.replace(/\n\nYours faithfully,[\s\S]*$/i, '');

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${refNo} - Official Discrepancy Notice</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 18mm 16mm 18mm 16mm;
    }
    * {
      box-sizing: border-box;
    }
    body {
      font-family: "Times New Roman", Times, Georgia, serif;
      font-size: 11.5pt;
      line-height: 1.55;
      color: #111111;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }
    .letterhead {
      text-align: center;
      border-bottom: 2px solid #222222;
      padding-bottom: 10px;
      margin-bottom: 18px;
    }
    .letterhead h1 {
      font-size: 14pt;
      font-weight: bold;
      text-transform: uppercase;
      margin: 0 0 3px 0;
      letter-spacing: 0.5px;
    }
    .letterhead h2 {
      font-size: 12pt;
      font-weight: 600;
      text-transform: uppercase;
      margin: 0 0 3px 0;
    }
    .letterhead .subtext {
      font-size: 9.5pt;
      color: #333333;
    }
    .meta-bar {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
      font-size: 11pt;
      font-weight: bold;
    }
    .recipient-block {
      margin-bottom: 14px;
      font-size: 11.5pt;
      line-height: 1.45;
    }
    .subject-block {
      font-weight: bold;
      margin: 14px 0;
      font-size: 11.5pt;
      line-height: 1.4;
      text-decoration: underline;
    }
    .salutation {
      margin-bottom: 10px;
      font-weight: 500;
    }
    p {
      margin: 0 0 10px 0;
      text-align: justify;
    }
    .spec-table {
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0;
      font-size: 10pt;
    }
    .spec-table th, .spec-table td {
      border: 1px solid #333333;
      padding: 5px 8px;
      vertical-align: top;
    }
    .spec-table th {
      background-color: #f1f5f9;
      font-weight: bold;
      text-align: left;
    }
    .spec-table .num {
      text-align: right;
      font-family: "Courier New", Courier, monospace;
      font-weight: bold;
    }
    .body-content {
      white-space: pre-wrap;
      font-size: 11pt;
      line-height: 1.55;
      text-align: justify;
      margin: 12px 0;
    }
    .directive-box {
      border: 1px solid #475569;
      background-color: #f8fafc;
      padding: 9px 12px;
      margin: 14px 0;
      font-size: 10.5pt;
    }
    .sig-section {
      margin-top: 32px;
      display: flex;
      justify-content: flex-end;
      page-break-inside: avoid;
    }
    .sig-block {
      width: 280px;
      text-align: center;
      font-size: 11pt;
      line-height: 1.4;
    }
    .copy-to {
      margin-top: 36px;
      border-top: 1px dashed #666666;
      padding-top: 8px;
      font-size: 9.5pt;
      line-height: 1.4;
      color: #333333;
      page-break-inside: avoid;
    }
    @media print {
      body {
        padding: 0;
      }
    }
  </style>
</head>
<body>
  <div class="letterhead">
    <h1>GOVERNMENT OF NATIONAL CAPITAL TERRITORY OF DELHI</h1>
    <h2>DIRECTORATE OF ACCOUNTS / PRINCIPAL ACCOUNTS OFFICE</h2>
    <div class="subtext">
      Revenue Reconciliation, Discrepancy Redressal & Statutory Recovery Wing<br/>
      Vikas Bhawan, I.P. Estate, New Delhi – 110002 &middot; Integrated Financial Management System (IFMS)
    </div>
  </div>

  <div class="meta-bar">
    <div>Ref. No.: <u>${refNo}</u></div>
    <div>Date: <u>${dateStr}</u></div>
  </div>

  <div class="recipient-block">
    To,<br/>
    <strong>${params.recipientName}</strong><br/>
    ${params.recipientAddress}
  </div>

  <div class="subject-block">
    Subject: ${params.subject}
  </div>

  <div class="salutation">Sir / Madam,</div>

  <p>
    During the automated three-way revenue reconciliation between Departmental Portal Filings, Agency Bank Collection Scrolls, and RBI CAS Nagpur Settlement Credits for Government Account, the following discrepancy has been officially observed and flagged for immediate resolution:
  </p>

  <table class="spec-table">
    <thead>
      <tr>
        <th style="width: 25%;">Audit / Accounting Field</th>
        <th style="width: 35%;">Transaction Attribute</th>
        <th style="width: 20%;">Reconciliation Leg</th>
        <th style="width: 20%; text-align: right;">Amount (INR)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>IFMS Revenue Txn ID</strong></td>
        <td><code>${params.revId}</code></td>
        <td><strong>1. Portal Filing</strong></td>
        <td class="num">₹ ${params.portalAmt.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      </tr>
      <tr>
        <td><strong>Challan Reference No</strong></td>
        <td><strong>${params.challan}</strong> ${params.cin ? `(CIN: ${params.cin})` : ''}</td>
        <td><strong>2. Bank Scroll Leg</strong></td>
        <td class="num">₹ ${params.bankAmt.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      </tr>
      <tr>
        <td><strong>Taxpayer / Remitter</strong></td>
        <td>${params.payer}</td>
        <td><strong>3. RBI Luggage Credit</strong></td>
        <td class="num">₹ ${params.rbiAmt.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      </tr>
      <tr>
        <td><strong>Department / PAO</strong></td>
        <td>${params.source} &mdash; Dept of ${params.dept} (${params.pao})</td>
        <td><strong>Disputed Variance</strong></td>
        <td class="num" style="color: #991b1b;">₹ ${params.diff.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
      </tr>
      ${params.slaDelay ? `<tr><td><strong>SLA Remittance Delay</strong></td><td colspan="3">${params.slaDelay} calendar days beyond permissible SLA &middot; Penal Interest accrued: <strong>₹ ${params.penal?.toFixed(2) || '0.00'}</strong></td></tr>` : ''}
    </tbody>
  </table>

  <div class="body-content">${cleanBody.trim()}</div>

  <div class="directive-box">
    <strong>Statutory Notice:</strong> In accordance with the IFMS Revenue Management Rules and RBI Agency Bank Remittance Guidelines, you are hereby requested to investigate this discrepancy, submit the rectification scroll / missing UTR credit confirmation, and transmit a compliance report within <strong>7 working days</strong> from the receipt of this notice.
  </div>

  <div class="sig-section">
    <div class="sig-block">
      <br/><br/>
      <strong>(Authorized Signatory)</strong><br/>
      Pay &amp; Accounts Officer / Treasury Officer<br/>
      Directorate of Accounts, Government of NCT of Delhi
    </div>
  </div>

  <div class="copy-to">
    <strong>Copy forwarded for information and necessary compliance to:</strong><br/>
    1. The Controller of Accounts, Directorate of Accounts, GNCTD, Vikas Bhawan, New Delhi.<br/>
    2. The Drawing &amp; Disbursing Officer (DDO), Department of ${params.dept}, GNCTD.<br/>
    3. Statutory Discrepancy &amp; Audit Trail Ledger (Recorded in <code>ifms_budget.rev_exception_letter</code>).
  </div>
</body>
</html>`;

  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.focus();
  setTimeout(() => {
    printWindow.print();
  }, 400);
}

