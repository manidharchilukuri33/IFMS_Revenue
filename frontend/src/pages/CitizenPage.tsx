import React, { useState } from 'react';
import { api } from '../api/client';
import { money, fmtDate, badgeClass } from '../utils/format';

export const CitizenPage: React.FC = () => {
  const [caseNo, setCaseNo] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseNo.trim()) return;
    try {
      setLoading(true);
      setSearched(true);
      const res = await api.getRefundCases({ limit: 50 });
      const found = (res.items || []).find(
        (x: any) =>
          (x.case_number || x.refund_case_no || '').toLowerCase() === caseNo.trim().toLowerCase() ||
          (x.applicant_id || '').toLowerCase() === caseNo.trim().toLowerCase()
      );
      setResult(found || null);
    } catch (e) {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Breadcrumb */}
      <div className="crumb">
        <span>IFMS</span>
        <span>Revenue Management</span>
        <span className="cur">Refund Status Tracking</span>
      </div>

      {/* Pagehead */}
      <div className="pagehead">
        <div>
          <h2>Refund Status Tracking</h2>
          <div className="sub">
            Enter your refund case number to view the current stage of your application. No other information is visible in the citizen view.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-b">
          <form onSubmit={handleSearch} className="flex gap8 max-w-lg mb16 items-end flex-wrap">
            <div className="fld grow" style={{ maxWidth: 340, marginBottom: 0 }}>
              <label>Refund case number</label>
              <input
                className="inp"
                placeholder="e.g. REF-NJ-2026-0001"
                value={caseNo}
                onChange={e => setCaseNo(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-p" disabled={loading}>
              {loading ? 'Searching...' : 'Track my refund'}
            </button>
          </form>

          {searched && (
            <div>
              {result ? (
                <div className="box info">
                  <h4>Application Status: {result.case_number || result.refund_case_no || caseNo}</h4>
                  <dl className="kv mt12">
                    <dt>Applicant Name</dt>
                    <dd>{result.applicant_name}</dd>
                    <dt>Refund Type</dt>
                    <dd>{result.refund_type}</dd>
                    <dt>Claim Amount</dt>
                    <dd className="strong">{money(result.refund_claim_amount || result.claim_amount)}</dd>
                    <dt>Original Challan</dt>
                    <dd className="mono">{result.original_challan_no}</dd>
                    <dt>Application Date</dt>
                    <dd>{fmtDate(result.application_date)}</dd>
                    <dt>Current Processing Status</dt>
                    <dd>
                      <span className={badgeClass(result.status)}>{result.status}</span>
                    </dd>
                    <dt>Pending At Office</dt>
                    <dd>{result.pending_at || 'Divisional Scrutiny Officer'}</dd>
                    <dt>Payment Mandate Status</dt>
                    <dd>{result.payment_status || 'Under Process'}</dd>
                  </dl>
                </div>
              ) : (
                <div className="errbar">
                  No refund case was found with the number "{caseNo}". Please check the case number printed on your acknowledgement.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* What the stages mean card */}
      <div className="card">
        <div className="card-h">
          <h3>What the stages mean</h3>
        </div>
        <div className="card-b">
          <div className="grid g2">
            <div>
              <h4 className="mb8">Non-judicial stamp refund</h4>
              <ol className="small">
                <li>Citizen application submitted</li>
                <li>Divisional Office document scrutiny</li>
                <li>SHCIL stamp validity verification</li>
                <li>Deficiency memo / return to applicant</li>
                <li>Stamp cancellation confirmation</li>
                <li>DDO refund-bill preparation</li>
                <li>PAO scrutiny and approval</li>
                <li>E-payment instruction</li>
                <li>Bank payment confirmation</li>
                <li>Case closure / archival</li>
              </ol>
            </div>
            <div>
              <h4 className="mb8">Judicial (court-ordered) stamp refund</h4>
              <ol className="small">
                <li>Citizen / court-initiated request</li>
                <li>Court refund order captured</li>
                <li>Finance Department forwards the order</li>
                <li>DDO refund-bill preparation</li>
                <li>PAO scrutiny and approval</li>
                <li>E-payment instruction</li>
                <li>Bank confirmation and closure</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default CitizenPage;
