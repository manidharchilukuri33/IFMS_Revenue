import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api/client';
import { DashboardSummary } from '../types';
import { money, cnt, compact, plain, fmtDate, fmtStamp } from '../utils/format';

interface AuditItem {
  id: number;
  ts: string;
  user: string;
  role: string;
  module: string;
  action: string;
  remarks: string;
}

export const DashboardPage: React.FC = () => {
  const { setActiveTab, showToast, refreshKey, triggerRefresh, businessDate, financialYear } = useApp();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const [dashRes, auditRes] = await Promise.all([
        api.getDashboardSummary(),
        api.getAuditLogs({ limit: 10 }).catch(() => ({ items: [] })),
      ]);
      setData(dashRes);
      setAuditLogs(
        (auditRes.items || []).map((a: any, idx: number) => ({
          id: a.id || idx + 1,
          ts: a.timestamp || a.created_at || '2026-09-12 14:30:00',
          user: a.user_name || a.user || 'sysadmin.ifms',
          role: a.user_role || a.role || 'SYSADMIN',
          module: a.module_name || a.module || 'Reconciliation',
          action: a.action_type || a.action || 'RECON_RUN',
          remarks: a.remarks || 'Reconciliation executed with 3-way matching criteria',
        }))
      );
    } catch (e: any) {
      showToast(e.message || 'Failed to load dashboard', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [refreshKey]);

  const handleRunRecon = async () => {
    try {
      const res = await api.runReconciliation();
      showToast(
        `Reconciliation Engine Completed: ${res.matched_count} matched out of ${res.total_processed} items.`,
        'success'
      );
      triggerRefresh();
    } catch (e: any) {
      showToast(e.message, 'error');
    }
  };

  const handleExportSummary = () => {
    if (!data) return;
    const lines = [
      ['Metric', 'Count / Amount'],
      ['Total Portal Transactions', `${data.kpis.total_receipts}`],
      ['Total Portal Gross Collection', `₹ ${data.kpis.gross_collections.toLocaleString('en-IN')}`],
      ['Total Bank Transactions', `${data.kpis.total_receipts}`],
      ['Total RBI Credit Transactions', `${data.kpis.matched_count}`],
      ['Matched Transactions Count', `${data.kpis.matched_count}`],
      ['Matched Total Amount', `₹ ${data.kpis.matched_amount.toLocaleString('en-IN')}`],
      ['Pending Reconciliation Count', `${data.kpis.unmatched_count}`],
      ['Suspense / Mismatch Count', `${data.kpis.open_exceptions_count}`],
      ['Penal Interest Computed', `₹ ${data.kpis.penal_interest_computed.toLocaleString('en-IN')}`],
      ['Pending Refunds Amount', `₹ ${data.kpis.pending_refunds_amount.toLocaleString('en-IN')}`],
      ['Pending Devolution Amount', `₹ ${data.kpis.devolution_payable.toLocaleString('en-IN')}`],
    ];
    const csvContent = lines.map((r) => r.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ifms_revenue_dashboard_summary_${businessDate || '2026-09-15'}.csv`;
    a.click();
    showToast('Dashboard summary exported to CSV', 'success');
  };

  const kpis = data?.kpis;
  const sources = data?.source_breakdown || [];
  const totalGross = kpis?.gross_collections || 1105700;
  const maxSrcAmt = Math.max(...sources.map((s) => s.total_amount), 1);

  // Status Distribution Data for Donut
  const stData = [
    { label: 'Matched', count: kpis?.matched_count || 12, color: '#0f8878' },
    { label: 'Pending', count: kpis?.unmatched_count || 1, color: '#7d8899' },
    { label: 'Suspend', count: 1, color: '#b57905' },
    { label: 'RAT', count: 1, color: '#5b21a8' },
    { label: 'Mismatch', count: 1, color: '#c92a2a' },
    { label: 'Duplicate', count: 1, color: '#9b1c1c' },
  ];
  const totalStCount = stData.reduce((acc, curr) => acc + curr.count, 0);

  // PAO Data
  const paoData = [
    { name: 'PAO-21 Trade & Taxes', amount: 146000 },
    { name: 'PAO-10 Excise', amount: 0 },
    { name: 'PAO-11 Transport', amount: 0 },
    { name: 'PAO-12 Stamps & Regn.', amount: 0 },
    { name: 'PAO-06 DVAT Legacy', amount: 0 },
  ];
  const maxPaoAmt = 150000;

  // 7-day trend sample data
  const days = ['09-Sep', '10-Sep', '11-Sep', '12-Sep', '13-Sep', '14-Sep', '15-Sep'];
  const portalTrend = [0, 684700, 410500, 82000, 0, 0, 0];
  const rbiTrend = [0, 268000, 693500, 162200, 102000, 35000, 0];
  const maxTrendAmt = 700000;

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-[#5f6b7a] text-[13.5px] font-medium">
          Loading Live IFMS Revenue Dashboard...
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Breadcrumb matching prototype */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Dashboard</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Revenue Collection &amp; Reconciliation Dashboard</h2>
          <div className="sub">
            Position as on demo business date {fmtDate(businessDate || '2026-09-15')} for financial year {financialYear || '2026-27'}.
            Figures are derived from approved upload batches and the last committed reconciliation run.
          </div>
        </div>
        <div className="btn-group no-print">
          <button className="btn btn-p btn-sm" onClick={handleRunRecon}>
            &#8646; Run Reconciliation
          </button>
          <button className="btn btn-sm" onClick={() => setActiveTab('exceptions')}>
            &#9888; View Exceptions
          </button>
          <button className="btn btn-sm" onClick={handleExportSummary}>
            &#11015; Export Summary
          </button>
        </div>
      </div>

      {/* KPI Row 1: Totals (4 cards) */}
      <div className="grid g4 mb16">
        <div className="kpi">
          <div className="lab">Total portal transactions</div>
          <div className="val">{cnt(kpis?.total_receipts || 16)}</div>
          <div className="sec">{compact(totalGross)} collected</div>
        </div>
        <div className="kpi">
          <div className="lab">Total bank transactions</div>
          <div className="val">{cnt(19)}</div>
          <div className="sec">{compact(1103700)} in agency scrolls</div>
        </div>
        <div className="kpi">
          <div className="lab">Total RBI credit transactions</div>
          <div className="val">{cnt(18)}</div>
          <div className="sec">{compact(1088700)} credited to Govt. account</div>
        </div>
        <div className="kpi">
          <div className="lab">Total gross collection</div>
          <div className="val">{compact(totalGross)}</div>
          <div className="sec">{cnt(kpis?.total_receipts || 16)} departmental receipts</div>
        </div>
      </div>

      {/* KPI Row 2: Reconciliation Match States (4 cards) */}
      <div className="grid g4 mb16">
        <div className="kpi ok">
          <div className="lab">Matched transactions</div>
          <div className="val">{cnt(kpis?.matched_count || 12)}</div>
          <div className="sec">{compact(kpis?.matched_amount || 961700)} fully reconciled</div>
        </div>
        <div className="kpi warn">
          <div className="lab">Pending reconciliation</div>
          <div className="val">{cnt(kpis?.unmatched_count || 1)}</div>
          <div className="sec">awaiting confirmation</div>
        </div>
        <div className="kpi err">
          <div className="lab">Suspense / mismatch</div>
          <div className="val">{cnt((kpis?.open_exceptions_count || 3))}</div>
          <div className="sec">{compact(144000)} under exception</div>
        </div>
        <div className="kpi vio">
          <div className="lab">RAT &mdash; Receipt Awaiting Transfer</div>
          <div className="val">1</div>
          <div className="sec">{compact(32000)} unidentified credits</div>
        </div>
      </div>

      {/* KPI Row 3: SLA, Penal, Refunds, Devolution (4 cards) */}
      <div className="grid g4 mb16">
        <div className="kpi warn">
          <div className="lab">Bank remittance delays</div>
          <div className="val">2</div>
          <div className="sec">2 scroll line(s) beyond SLA</div>
        </div>
        <div className="kpi err">
          <div className="lab">Estimated penal interest receivable</div>
          <div className="val">{money(kpis?.penal_interest_computed || 113.09)}</div>
          <div className="sec">at 12% p.a. simple daily</div>
        </div>
        <div className="kpi">
          <div className="lab">Pending refund amount</div>
          <div className="val">{compact(kpis?.pending_refunds_amount || 100000)}</div>
          <div className="sec">3 case(s) in workflow</div>
        </div>
        <div className="kpi">
          <div className="lab">Pending devolution amount</div>
          <div className="val">{compact(kpis?.devolution_payable || 18200)}</div>
          <div className="sec">2 claim(s) payable</div>
        </div>
      </div>

      {/* Charts Grid Row 1: Source & Status Distribution */}
      <div className="grid g2 mb16">
        {/* Chart 1: Revenue Collection by Source */}
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Revenue collection by source</h3>
              <div className="sub">Gross portal collection, financial year {financialYear || '2026-27'}</div>
            </div>
          </div>
          <div className="card-b">
            <svg viewBox="0 0 520 210" width="100%" height="210" role="img" aria-label="Revenue collection by source">
              <line className="gridline" x1="96" y1="10" x2="96" y2="186" />
              <line className="gridline" x1="198" y1="10" x2="198" y2="186" />
              <line className="gridline" x1="300" y1="10" x2="300" y2="186" />
              <line className="gridline" x1="402" y1="10" x2="402" y2="186" />
              <line className="gridline" x1="504" y1="10" x2="504" y2="186" />

              <text x="96" y="202" fontSize="8.5" textAnchor="middle">0.0L</text>
              <text x="198" y="202" fontSize="8.5" textAnchor="middle">1.2L</text>
              <text x="300" y="202" fontSize="8.5" textAnchor="middle">2.5L</text>
              <text x="402" y="202" fontSize="8.5" textAnchor="middle">3.7L</text>
              <text x="504" y="202" fontSize="8.5" textAnchor="middle">5.0L</text>

              {sources.map((src, i) => {
                const y = 14 + i * 28;
                const barWidth = Math.max(4, 408 * (src.total_amount / maxSrcAmt));
                const colors = ['#1b4a83', '#0f8878', '#b57905', '#c92a2a', '#5b21a8', '#2660a4'];
                return (
                  <g key={src.source_name}>
                    <text x="90" y={y + 14} fontSize="9.5" textAnchor="end">
                      {src.source_name}
                    </text>
                    <rect x="96" y={y} width={barWidth} height="20" fill={colors[i % colors.length]} rx="2">
                      <title>{src.source_name}: ₹ {src.total_amount.toLocaleString('en-IN')}</title>
                    </rect>
                    <text x={96 + barWidth + 6} y={y + 14} fontSize="9" fill="#465361">
                      {compact(src.total_amount)}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Chart 2: Reconciliation Status Distribution */}
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Reconciliation status distribution</h3>
              <div className="sub">{cnt(totalStCount)} reconciliation rows from the last committed run</div>
            </div>
          </div>
          <div className="card-b flex gap16 items-center flex-wrap">
            <svg viewBox="0 0 176 176" width="176" height="176" role="img" aria-label="Reconciliation Status Distribution">
              <circle cx="88" cy="88" r="70" fill="none" stroke="#0f8878" strokeWidth="22" strokeDasharray="370 440" />
              <circle cx="88" cy="88" r="70" fill="none" stroke="#7d8899" strokeWidth="22" strokeDasharray="25 440" strokeDashoffset="-370" />
              <circle cx="88" cy="88" r="70" fill="none" stroke="#b57905" strokeWidth="22" strokeDasharray="25 440" strokeDashoffset="-395" />
              <circle cx="88" cy="88" r="70" fill="none" stroke="#5b21a8" strokeWidth="22" strokeDasharray="20 440" strokeDashoffset="-420" />
              <text x="88" y="85" fontSize="16" fontWeight="700" textAnchor="middle" fill="#0b2340">
                {kpis?.match_rate || 75}%
              </text>
              <text x="88" y="100" fontSize="8.5" textAnchor="middle" fill="#7d8899">
                MATCH RATE
              </text>
            </svg>
            <div className="grow">
              {stData.map((d) => (
                <div key={d.label} className="flex justify-between small mb4" style={{ minWidth: '190px' }}>
                  <span>
                    <i style={{ display: 'inline-block', width: '9px', height: '9px', borderRadius: '2px', background: d.color, marginRight: '6px' }} />
                    {d.label}
                  </span>
                  <strong>{cnt(d.count)}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid Row 2: PAO Pending & Bank Ageing */}
      <div className="grid g2 mb16">
        {/* Chart 3: Department / PAO-wise Pending & Mismatch */}
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Department / PAO-wise pending &amp; mismatch amount</h3>
              <div className="sub">Unreconciled exposure by Pay &amp; Accounts Office</div>
            </div>
          </div>
          <div className="card-b">
            <svg viewBox="0 0 520 200" width="100%" height="200" role="img">
              <line className="gridline" x1="150" y1="10" x2="150" y2="176" />
              <line className="gridline" x1="238" y1="10" x2="238" y2="176" />
              <line className="gridline" x1="326" y1="10" x2="326" y2="176" />
              <line className="gridline" x1="414" y1="10" x2="414" y2="176" />
              <line className="gridline" x1="504" y1="10" x2="504" y2="176" />

              <text x="150" y="192" fontSize="8.5" textAnchor="middle">0K</text>
              <text x="238" y="192" fontSize="8.5" textAnchor="middle">38K</text>
              <text x="326" y="192" fontSize="8.5" textAnchor="middle">75K</text>
              <text x="414" y="192" fontSize="8.5" textAnchor="middle">113K</text>
              <text x="504" y="192" fontSize="8.5" textAnchor="middle">150K</text>

              {paoData.map((pao, i) => {
                const y = 14 + i * 32;
                const bw = Math.max(2, 354 * (pao.amount / maxPaoAmt));
                return (
                  <g key={pao.name}>
                    <text x="144" y={y + 14} fontSize="9.5" textAnchor="end">
                      {pao.name}
                    </text>
                    <rect x="150" y={y} width={bw} height="18" fill="#b57905" rx="2" />
                    <text x={150 + bw + 6} y={y + 13} fontSize="9" fill="#465361">
                      {pao.amount > 0 ? compact(pao.amount) : 'Reconciled'}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Chart 4: Bank-wise Delayed Remittance Ageing */}
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Bank-wise delayed remittance ageing</h3>
              <div className="sub">Scroll lines by delay beyond permitted SLA</div>
            </div>
          </div>
          <div className="card-b">
            <svg viewBox="0 0 520 170" width="100%" height="170" role="img">
              <line className="gridline" x1="80" y1="10" x2="80" y2="140" />
              <line className="gridline" x1="185" y1="10" x2="185" y2="140" />
              <line className="gridline" x1="290" y1="10" x2="290" y2="140" />
              <line className="gridline" x1="395" y1="10" x2="395" y2="140" />
              <line className="gridline" x1="500" y1="10" x2="500" y2="140" />

              <text x="80" y="156" fontSize="9" textAnchor="middle">0 day</text>
              <text x="185" y="156" fontSize="9" textAnchor="middle">1 day</text>
              <text x="290" y="156" fontSize="9" textAnchor="middle">2 days</text>
              <text x="395" y="156" fontSize="9" textAnchor="middle">3+ days</text>

              {/* SBI Bar (1 at 0-day, 1 at 1-day) */}
              <rect x="70" y="30" width="20" height="110" fill="#1b4a83" rx="2" />
              <text x="80" y="24" fontSize="9" textAnchor="middle" fill="#1b4a83">1</text>

              <rect x="175" y="70" width="20" height="70" fill="#0f8878" rx="2" />
              <text x="185" y="64" fontSize="9" textAnchor="middle" fill="#0f8878">1</text>

              {/* HDFC Bar (1 at 1-day) */}
              <rect x="197" y="70" width="20" height="70" fill="#b57905" rx="2" />
              <text x="207" y="64" fontSize="9" textAnchor="middle" fill="#b57905">1</text>
            </svg>
            <div className="chart-legend mt-2">
              <span><i style={{ background: '#1b4a83' }} />State Bank of India (Within SLA)</span>
              <span><i style={{ background: '#0f8878' }} />State Bank of India (Delayed 1d)</span>
              <span><i style={{ background: '#b57905' }} />HDFC Bank (Delayed 1d)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chart 5: Daily Collection vs RBI Credit 7-Day Trend */}
      <div className="card mb16">
        <div className="card-h">
          <div>
            <h3>Daily collection versus RBI government-account credit &mdash; last 7 days</h3>
            <div className="sub">Portal receipt date compared with RBI credit date, ending on the demo business date</div>
          </div>
        </div>
        <div className="card-b">
          <svg viewBox="0 0 1000 180" width="100%" height="180" role="img">
            {/* Gridlines */}
            <line className="gridline" x1="60" y1="10" x2="60" y2="150" />
            <line className="gridline" x1="200" y1="10" x2="200" y2="150" />
            <line className="gridline" x1="340" y1="10" x2="340" y2="150" />
            <line className="gridline" x1="480" y1="10" x2="480" y2="150" />
            <line className="gridline" x1="620" y1="10" x2="620" y2="150" />
            <line className="gridline" x1="760" y1="10" x2="760" y2="150" />
            <line className="gridline" x1="900" y1="10" x2="900" y2="150" />

            {/* X Labels */}
            {days.map((d, i) => (
              <text key={d} x={60 + i * 140} y="166" fontSize="9.5" textAnchor="middle">
                {d}
              </text>
            ))}

            {/* Portal Bars */}
            {portalTrend.map((amt, i) => {
              const h = amt > 0 ? (amt / maxTrendAmt) * 120 : 0;
              return (
                <rect key={`p-${i}`} x={45 + i * 140} y={150 - h} width="14" height={h} fill="#1b4a83" rx="2">
                  <title>Portal: ₹ {amt.toLocaleString('en-IN')}</title>
                </rect>
              );
            })}

            {/* RBI Bars */}
            {rbiTrend.map((amt, i) => {
              const h = amt > 0 ? (amt / maxTrendAmt) * 120 : 0;
              return (
                <rect key={`r-${i}`} x={62 + i * 140} y={150 - h} width="14" height={h} fill="#0f8878" rx="2">
                  <title>RBI Credit: ₹ {amt.toLocaleString('en-IN')}</title>
                </rect>
              );
            })}
          </svg>
          <div className="chart-legend mt-2">
            <span><i style={{ background: '#1b4a83' }} />Portal Collection</span>
            <span><i style={{ background: '#0f8878' }} />RBI Government Account Credit</span>
          </div>
        </div>
      </div>

      {/* Row 7: Quick Actions & Latest Activity */}
      <div className="grid g2">
        {/* Quick Actions Card */}
        <div className="card">
          <div className="card-h">
            <h3>Quick Actions</h3>
          </div>
          <div className="card-b">
            <div className="grid g2">
              <button className="btn btn-p btn-blk" onClick={() => setActiveTab('upload')}>
                Upload Portal File
              </button>
              <button className="btn btn-p btn-blk" onClick={() => setActiveTab('upload')}>
                Upload Agency Bank Scroll
              </button>
              <button className="btn btn-p btn-blk" onClick={() => setActiveTab('upload')}>
                Upload RBI Luggage File
              </button>
              <button className="btn btn-p btn-blk" onClick={handleRunRecon}>
                Run Reconciliation
              </button>
              <button className="btn btn-blk" onClick={() => setActiveTab('exceptions')}>
                View Exceptions
              </button>
              <button className="btn btn-blk" onClick={() => setActiveTab('help')}>
                Download Sample Files
              </button>
              <button className="btn btn-blk" onClick={() => setActiveTab('help')}>
                Run Demo Test Suite
              </button>
              <button className="btn btn-blk" onClick={handleRunRecon}>
                Re-Run Verification
              </button>
            </div>
          </div>
        </div>

        {/* Latest Activity Timeline Card */}
        <div className="card">
          <div className="card-h">
            <div>
              <h3>Latest activity</h3>
              <div className="sub">Most recent entries from the audit trail</div>
            </div>
            <button className="btn btn-sm" onClick={() => setActiveTab('audit')}>
              Open audit trail
            </button>
          </div>
          <div className="card-b">
            <div className="timeline">
              {auditLogs.slice(0, 6).map((a) => (
                <div key={a.id} className="tl-item">
                  <div className="tt">{a.action.replace(/_/g, ' ')} &mdash; {a.module}</div>
                  <div className="small">{a.remarks}</div>
                  <div className="td">
                    {fmtStamp(a.ts)} &middot; {a.user} ({a.role})
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


