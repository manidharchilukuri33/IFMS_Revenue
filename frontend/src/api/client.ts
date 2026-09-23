import {
  DashboardSummary,
  UploadBatch,
  PortalStagingItem,
  BankScrollStagingItem,
  RbiLuggageStagingItem,
  ReconResult,
  ReconDetail,
  ReconRunSummary,
  RevException,
  ExceptionLetter,
  PenalClaim,
  RefundCase,
  RefundTimeline,
  DevolutionClaim,
  ReceiptVoucher,
  SuspenseItem,
  ReportMetadata,
  ReportDataset,
  AgencyBank,
  AgencyBankBranch,
  RevenuePortal,
  RevenueSource,
  SlaRule,
  LocalBody,
  DevolutionRule,
  SystemConfig,
  AuditLog,
  TestSuiteSummary,
  UserRole,
} from '../types';

const BASE_URL = '/api';

const getSavedClientRole = (): UserRole => {
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

const initialClientRole = getSavedClientRole();

class ApiClient {
  private currentRole: UserRole = initialClientRole;
  private currentUserId: number = initialClientRole === 'PAO_CHECK' ? 2 : initialClientRole === 'PAO_MAKER' ? 3 : 1;

  public setRole(role: UserRole, userId: number = 1) {
    this.currentRole = role;
    this.currentUserId = userId;
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('ifms_user_role', role);
      } catch (e) {}
    }
  }

  public getRole(): UserRole {
    return this.currentRole;
  }

  public getUserId(): number {
    return this.currentUserId;
  }


  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-User-Role': this.currentRole,
      'X-User-Id': String(this.currentUserId),
      ...(options.headers as Record<string, string>),
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMsg = errorData.detail;
          } else if (errorData.detail.message) {
            errorMsg = errorData.detail.message;
          } else {
            errorMsg = JSON.stringify(errorData.detail);
          }
        }
      } catch (e) {
        // use default error message
      }
      throw new Error(errorMsg);
    }

    return response.json();
  }

  // 1. Auth & Session
  async getSession() {
    return this.request<any>('/auth/me');
  }

  // 2. Dashboard
  async getDashboardSummary(fromDate?: string, toDate?: string) {
    let q = '';
    const params = new URLSearchParams();
    if (fromDate) params.append('from_date', fromDate);
    if (toDate) params.append('to_date', toDate);
    if (params.toString()) q = `?${params.toString()}`;
    return this.request<DashboardSummary>(`/dashboard/summary${q}`);
  }

  // 3. Collection
  async getCollectionTransactions(params?: {
    search?: string;
    source_id?: number;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }) {
    const qp = new URLSearchParams();
    if (params?.search) qp.append('search', params.search);
    if (params?.source_id) qp.append('source_id', String(params.source_id));
    if (params?.from_date) qp.append('from_date', params.from_date);
    if (params?.to_date) qp.append('to_date', params.to_date);
    if (params?.limit) qp.append('limit', String(params.limit));
    if (params?.offset) qp.append('offset', String(params.offset));
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ total: number; items: PortalStagingItem[] }>(`/collection/transactions${qs}`);
  }

  async createManualReceipt(data: any) {
    return this.request<PortalStagingItem>('/collection/manual-receipt', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // 4. Upload & Staging
  async getUploadBatches(batchType?: string) {
    const q = batchType ? `?batch_type=${batchType}` : '';
    return this.request<UploadBatch[]>(`/upload/batches${q}`);
  }

  async getBatchDetails(batchId: number) {
    return this.request<{
      batch: UploadBatch;
      portal_items: PortalStagingItem[];
      bank_items: BankScrollStagingItem[];
      rbi_items: RbiLuggageStagingItem[];
    }>(`/upload/batches/${batchId}`);
  }

  async uploadPortalFile(fileOrPayload: File | { filename: string; csv_content: string }, sourceCode: string = 'GST', deptId: number = 1, paoId: number = 1) {
    if (fileOrPayload instanceof File) {
      const text = await fileOrPayload.text();
      return this.request<UploadBatch>('/upload/portal', {
        method: 'POST',
        body: JSON.stringify({ filename: fileOrPayload.name, csv_content: text }),
      });
    }
    return this.request<UploadBatch>('/upload/portal', {
      method: 'POST',
      body: JSON.stringify(fileOrPayload),
    });
  }

  async uploadBankScrollFile(fileOrPayload: File | { filename: string; bank_code: string; csv_content: string }, bankId: number = 1) {
    if (fileOrPayload instanceof File) {
      const text = await fileOrPayload.text();
      return this.request<UploadBatch>('/upload/bank-scroll', {
        method: 'POST',
        body: JSON.stringify({ filename: fileOrPayload.name, bank_code: 'SBI', csv_content: text }),
      });
    }
    return this.request<UploadBatch>('/upload/bank-scroll', {
      method: 'POST',
      body: JSON.stringify(fileOrPayload),
    });
  }

  async uploadBankScroll(fileOrPayload: any, bankId?: number) {
    return this.uploadBankScrollFile(fileOrPayload, bankId);
  }

  async uploadRbiFile(fileOrPayload: File | { filename: string; csv_content: string }, bankId: number = 1) {
    if (fileOrPayload instanceof File) {
      const text = await fileOrPayload.text();
      return this.request<UploadBatch>('/upload/rbi-luggage', {
        method: 'POST',
        body: JSON.stringify({ filename: fileOrPayload.name, csv_content: text }),
      });
    }
    return this.request<UploadBatch>('/upload/rbi-luggage', {
      method: 'POST',
      body: JSON.stringify(fileOrPayload),
    });
  }

  async uploadRbiLuggage(fileOrPayload: any, bankId?: number) {
    return this.uploadRbiFile(fileOrPayload, bankId);
  }

  async approveBatch(batchId: number, remarks: string = 'Approved via UI') {
    return this.request<UploadBatch>(`/upload/batches/${batchId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ remarks }),
    });
  }

  async deleteBatch(batchId: number) {
    return this.request<{ status: string; message: string }>(`/upload/batches/${batchId}`, {
      method: 'DELETE',
    });
  }


  // 5. 3-Way Reconciliation
  async runReconciliation(payload?: any) {
    return this.request<ReconRunSummary>('/recon/run', {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  }

  async getReconResults(params?: {
    status?: string;
    source?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }) {
    const qp = new URLSearchParams();
    if (params?.status && params.status !== 'ALL') qp.append('status', params.status);
    if (params?.source && params.source !== 'ALL') qp.append('source', params.source);
    if (params?.search) qp.append('search', params.search);
    if (params?.limit) qp.append('limit', String(params.limit));
    if (params?.offset) qp.append('offset', String(params.offset));
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ total: number; items: ReconResult[] }>(`/recon/results${qs}`);
  }

  async getReconciliationResults(params?: any) {
    return this.getReconResults(params);
  }

  async getReconSummary() {
    return this.request<{
      control_totals: {
        portal: { count: number; amount: number };
        bank: { count: number; amount: number };
        rbi: { count: number; amount: number };
      };
      status_breakdown: Record<string, {
        count: number;
        gross_amount: number;
        variance_amount: number;
        penal_amount: number;
      }>;
      total_penal_interest: number;
    }>('/recon/summary');
  }

  async resetReconciliation() {
    return this.request<{ status: string; message: string }>('/recon/reset', {
      method: 'POST',
    });
  }

  async getReconDetail(reconId: number) {
    return this.request<ReconDetail>(`/recon/results/${reconId}`);
  }

  async proposeOverride(payload: { recon_id: number; proposed_status: string; justification: string }) {
    return this.request<any>('/recon/override/propose', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async decideOverride(payload: { override_id: number; decision: 'APPROVED' | 'REJECTED'; remarks?: string }) {
    return this.request<any>('/recon/override/decide', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async traceReconResult(reconId: number) {
    return this.request<any>(`/recon/results/${reconId}/trace`, {
      method: 'POST',
    });
  }

  async solveReconDiscrepancy(reconId: number, payload: {
    resolution_type: string;
    target_status?: string;
    remarks: string;
    reference_no?: string;
    suspense_head_code?: string;
    adjust_amount?: number;
  }) {
    return this.request<any>(`/recon/results/${reconId}/solve`, {
      method: 'POST',
      body: JSON.stringify({ recon_id: reconId, ...payload }),
    });
  }

  // 6. Exception Management
  async getExceptions(params?: any) {
    const qp = new URLSearchParams();
    if (typeof params === 'object') {
      if (params.category && params.category !== 'ALL') qp.append('category', params.category);
      if (params.severity && params.severity !== 'ALL') qp.append('severity', params.severity);
      if (params.status && params.status !== 'ALL') qp.append('status', params.status);
      if (params.search) qp.append('search', params.search);
      if (params.limit) qp.append('limit', String(params.limit));
    }
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ items: RevException[] } | RevException[]>(`/exceptions${qs}`).then(res => {
      if (Array.isArray(res)) return { items: res };
      return res;
    });
  }

  async getExceptionDetail(exceptionId: number) {
    return this.request<{
      exception: RevException;
      notes: any[];
      letters: ExceptionLetter[];
      recon?: ReconResult;
    }>(`/exceptions/${exceptionId}`);
  }

  async resolveException(exceptionId: number, payload: { resolution_reason: string; resolution_remarks: string }) {
    return this.request<RevException>(`/exceptions/${exceptionId}/resolve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async issueExceptionLetter(exceptionId: number, payload: {
    recipient_type: string;
    recipient_name: string;
    recipient_address?: string;
    letter_subject: string;
    letter_body: string;
  }) {
    return this.request<ExceptionLetter>(`/exceptions/${exceptionId}/issue-letter`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async assignExceptionsBulk(exceptionIds: number[], assignedUserId: number) {
    return this.request<any>('/exceptions/assign-bulk', {
      method: 'POST',
      body: JSON.stringify({ exception_ids: exceptionIds, assigned_user_id: assignedUserId }),
    });
  }

  // 7. SLA & Penal Interest
  async getPenalClaims(statusOrParams?: any, bankId?: number) {
    const qp = new URLSearchParams();
    if (typeof statusOrParams === 'object') {
      if (statusOrParams.status) qp.append('status', statusOrParams.status);
      if (statusOrParams.bank_id) qp.append('bank_id', String(statusOrParams.bank_id));
      if (statusOrParams.limit) qp.append('limit', String(statusOrParams.limit));
    } else if (typeof statusOrParams === 'string') {
      if (statusOrParams !== 'ALL') qp.append('status', statusOrParams);
      if (bankId) qp.append('bank_id', String(bankId));
    }
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ items: PenalClaim[] } | PenalClaim[]>(`/sla/claims${qs}`).then(res => {
      if (Array.isArray(res)) return { items: res };
      return res;
    });
  }

  async issueDemandLetter(claimId: number, payload: { recipient_name: string; recipient_address?: string; remarks?: string }) {
    return this.request<any>(`/sla/claims/${claimId}/issue-demand`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async recordBankResponse(claimId: number, payload: { recovered_amount: number; bank_reference_no: string; remittance_date: string; remarks?: string }) {
    return this.request<PenalClaim>(`/sla/claims/${claimId}/record-response`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async approvePenaltyWaiver(claimId: number, payload: { waived_amount: number; waiver_ground: string; sanction_order_ref: string; waiver_remarks: string }) {
    return this.request<any>(`/sla/claims/${claimId}/waiver`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async proposeWaiver(claimId: number, payload: { waiver_amount: number; justification: string }) {
    return this.request<PenalClaim>(`/sla/claims/${claimId}/waiver/propose`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async approveWaiver(claimId: number, payload: { remarks: string }) {
    return this.request<PenalClaim>(`/sla/claims/${claimId}/waiver/approve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // 8. Refund Management
  async getRefunds(refundTypeOrParams?: any, status?: string) {
    const qp = new URLSearchParams();
    if (typeof refundTypeOrParams === 'object') {
      if (refundTypeOrParams.refund_type) qp.append('refund_type', refundTypeOrParams.refund_type);
      if (refundTypeOrParams.status) qp.append('status', refundTypeOrParams.status);
      if (refundTypeOrParams.limit) qp.append('limit', String(refundTypeOrParams.limit));
    } else if (typeof refundTypeOrParams === 'string') {
      if (refundTypeOrParams !== 'ALL') qp.append('refund_type', refundTypeOrParams);
      if (status && status !== 'ALL') qp.append('status', status);
    }
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ items: RefundCase[] } | RefundCase[]>(`/refunds${qs}`).then(res => {
      if (Array.isArray(res)) return { items: res };
      return res;
    });
  }

  async getRefundCases(params?: any) {
    return this.getRefunds(params);
  }

  async getRefundDetail(refundId: number) {
    return this.request<{ refund: RefundCase; timeline: RefundTimeline[]; recon?: ReconResult }>(`/refunds/${refundId}`);
  }

  async createRefundCase(payload: any) {
    return this.request<RefundCase>('/refunds', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async verifyShcil(refundId: number, certificateNo: string) {
    return this.request<RefundCase>(`/refunds/${refundId}/verify-shcil`, {
      method: 'POST',
      body: JSON.stringify({ certificate_no: certificateNo }),
    });
  }

  async prepareRefundBill(refundId: number, refundableAmount: number) {
    return this.request<RefundCase>(`/refunds/${refundId}/prepare-bill`, {
      method: 'POST',
      body: JSON.stringify({ refundable_amount: refundableAmount }),
    });
  }

  async approveRefundPao(refundId: number, remarks: string = 'Approved by PAO') {
    return this.request<RefundCase>(`/refunds/${refundId}/approve-pao`, {
      method: 'POST',
      body: JSON.stringify({ remarks }),
    });
  }

  async instructPayment(refundId: number, payload: { bank_account_no: string; ifsc_code: string }) {
    return this.request<RefundCase>(`/refunds/${refundId}/instruct-payment`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async markRefundPaid(refundId: number, ePaymentRef: string) {
    return this.request<RefundCase>(`/refunds/${refundId}/mark-paid`, {
      method: 'POST',
      body: JSON.stringify({ e_payment_ref: ePaymentRef }),
    });
  }

  async advanceRefundStage(refundId: number, payload: { action: string; remarks?: string; verification_type?: string; verification_result?: string; authority_name?: string }) {
    return this.request<RefundCase>(`/refunds/${refundId}/advance`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async rejectRefundCase(refundId: number, remarks: string = 'Rejected in scrutiny') {
    return this.request<RefundCase>(`/refunds/${refundId}/advance`, {
      method: 'POST',
      body: JSON.stringify({ action: 'REJECT', remarks }),
    });
  }

  async raiseRefundDeficiency(refundId: number, remarks: string) {
    return this.request<RefundCase>(`/refunds/${refundId}/advance`, {
      method: 'POST',
      body: JSON.stringify({ action: 'RAISE_DEFICIENCY', remarks }),
    });
  }

  // 9. Citizen Public Portal
  async trackCitizenRefund(caseNo: string) {
    return this.request<{ refund: RefundCase; timeline: RefundTimeline[] }>(`/citizen/track/${caseNo}`);
  }

  // 10. Local Body Devolution
  async getDevolutionClaims(params?: any) {
    return this.request<{ items: DevolutionClaim[] } | DevolutionClaim[]>('/devolution/claims').then(res => {
      if (Array.isArray(res)) return { items: res };
      return res;
    });
  }

  async computeDevolution(payload: { local_body_id: number; source_id: number; period_from: string; period_to: string }) {
    return this.request<DevolutionClaim>('/devolution/compute', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async createDevolutionClaim(payload: any) {
    return this.request<DevolutionClaim>('/devolution/claims', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async approveDevolution(claimId: number, payload: { approved_amount: number; debit_head_id?: number; scrutiny_remarks?: string }) {
    return this.request<any>(`/devolution/claims/${claimId}/approve`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async issueDevolutionAdvice(claimId: number, approvedAmount: number) {
    return this.request<DevolutionClaim>(`/devolution/claims/${claimId}/issue-advice`, {
      method: 'POST',
      body: JSON.stringify({ approved_amount: approvedAmount }),
    });
  }

  // 11. Accounting & Vouchers
  async getVouchers(status?: string, paoCode?: string) {
    const qp = new URLSearchParams();
    if (status && status !== 'ALL') qp.append('status', status);
    if (paoCode) qp.append('pao_code', paoCode);
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ total: number; items: ReceiptVoucher[]; summary?: any } | ReceiptVoucher[]>(`/accounting/vouchers${qs}`).then(res => {
      if (Array.isArray(res)) return { total: res.length, items: res, summary: {} };
      return res;
    });
  }

  async getReceiptVouchers(params?: any) {
    return this.getVouchers(params?.status, params?.pao_code);
  }

  async createSingleVoucher(reconId: number, narration?: string) {
    return this.request<any>('/accounting/vouchers/create', {
      method: 'POST',
      body: JSON.stringify({ recon_id: reconId, narration }),
    });
  }

  async generateVouchersBulk(paoCode: string = 'PAO21') {
    return this.request<any>('/accounting/vouchers/generate-bulk', {
      method: 'POST',
      body: JSON.stringify({ pao_code: paoCode }),
    });
  }

  async approveVouchersBulk(remarks: string = 'Approved and posted') {
    return this.request<any>('/accounting/vouchers/approve-bulk', {
      method: 'POST',
      body: JSON.stringify({ remarks }),
    });
  }

  async approveSingleVoucher(voucherId: number, remarks: string = 'Approved by PAO Checker') {
    return this.request<any>(`/accounting/vouchers/${voucherId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ remarks }),
    });
  }

  async getSuspenseItems(suspenseType?: string, status?: string) {
    const qp = new URLSearchParams();
    if (suspenseType && suspenseType !== 'ALL') qp.append('suspense_type', suspenseType);
    if (status && status !== 'ALL') qp.append('status', status);
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ total: number; items: SuspenseItem[]; summary?: any } | SuspenseItem[]>(`/accounting/suspense${qs}`).then(res => {
      if (Array.isArray(res)) return { total: res.length, items: res, summary: {} };
      return res;
    });
  }

  async clearSuspense(suspenseId: number, payload: { clear_amount: number; transfer_to_head: string; remarks?: string }) {
    return this.request<SuspenseItem>(`/accounting/suspense/${suspenseId}/clear`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // 12. Reports
  async getReportsList() {
    return this.request<ReportMetadata[]>('/reports/list');
  }

  async generateReport(reportId: string, params?: { from_date?: string; to_date?: string; source_id?: number; bank_id?: number; pao_code?: string }) {
    const qp = new URLSearchParams();
    if (params?.from_date) qp.append('from_date', params.from_date);
    if (params?.to_date) qp.append('to_date', params.to_date);
    if (params?.source_id) qp.append('source_id', String(params.source_id));
    if (params?.bank_id) qp.append('bank_id', String(params.bank_id));
    if (params?.pao_code) qp.append('pao_code', params.pao_code);
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<ReportDataset>(`/reports/${reportId}${qs}`);
  }

  // 13. Masters
  async getAgencyBanks() {
    return this.request<AgencyBank[]>('/masters/banks');
  }

  async getAgencyBankBranches(bankId?: number) {
    const q = bankId ? `?bank_id=${bankId}` : '';
    return this.request<AgencyBankBranch[]>(`/masters/branches${q}`);
  }

  async getRevenuePortals() {
    return this.request<RevenuePortal[]>('/masters/portals');
  }

  async getRevenueSources() {
    return this.request<RevenueSource[]>('/masters/sources');
  }

  async getPaos() {
    return this.request<any[]>('/masters/paos').catch(() => [
      { code: 'PAO21', name: 'PAO-21 Trade & Taxes', dept: 'TT' },
      { code: 'PAO10', name: 'PAO-10 Excise', dept: 'EXCISE' },
      { code: 'PAO11', name: 'PAO-11 Transport', dept: 'TRANSPORT' },
      { code: 'PAO12', name: 'PAO-12 Stamps & Registration', dept: 'STAMPREG' },
      { code: 'PAO06', name: 'PAO-06 DVAT', dept: 'DVAT' },
      { code: 'PAO15', name: 'PAO-15 General / Non-Tax', dept: 'GAD' },
    ]);
  }

  async getReceiptHeads() {
    return this.request<any[]>('/masters/heads').catch(() => [
      { code: '0040-00-102-01-00-01', major: '0040', desc: 'SGST Receipts', source: 'GST' },
      { code: '0039-00-105-01-00-01', major: '0039', desc: 'State Excise Licence Fee', source: 'EXCISE' },
      { code: '0041-00-101-01-00-01', major: '0041', desc: 'Vehicle Registration Fee', source: 'TRANSPORT' },
      { code: '0030-00-102-01-00-01', major: '0030', desc: 'Non-Judicial Stamp Duty', source: 'STAMP' },
      { code: '0030-00-103-01-00-01', major: '0030', desc: 'Judicial Stamps (Court Fees)', source: 'STAMP' },
      { code: '0040-00-101-01-00-01', major: '0040', desc: 'DVAT / Sales Tax Receipts', source: 'DVAT' },
      { code: '0070-60-800-01-00-01', major: '0070', desc: 'Other Non-Tax Service Fees', source: 'NONTAX' },
    ]);
  }

  async getReconciliationRules() {
    return this.request<any[]>('/masters/rules').catch(() => [
      { id: 'RR-01', rule_code: 'RR-01', priority: 1, primary: 'REVENUE_SOURCE + CIN', outcome_status: 'Matched', matching_mode: 'THREE_WAY_EXACT' },
      { id: 'RR-02', rule_code: 'RR-02', priority: 2, primary: 'CHALLAN_NO / CIN group', outcome_status: 'Matched (One-to-Many)', matching_mode: 'ONE_TO_MANY' },
      { id: 'RR-03', rule_code: 'RR-03', priority: 3, primary: 'PORTAL present, RBI absent', outcome_status: 'Suspend', matching_mode: 'SLA_AGEING' },
      { id: 'RR-04', rule_code: 'RR-04', priority: 4, primary: 'RBI / bank present, portal absent', outcome_status: 'RAT', matching_mode: 'ORPHAN_CREDIT' },
      { id: 'RR-05', rule_code: 'RR-05', priority: 5, primary: 'Repeated unique source reference', outcome_status: 'Duplicate', matching_mode: 'DUPLICATE_SCAN' },
      { id: 'RR-06', rule_code: 'RR-06', priority: 6, primary: 'Matched keys, amount variance', outcome_status: 'Mismatch', matching_mode: 'AMOUNT_VARIANCE' },
    ]);
  }

  async getSlaRules() {
    return this.request<SlaRule[]>('/masters/sla-rules');
  }

  async getLocalBodies() {
    return this.request<LocalBody[]>('/masters/local-bodies');
  }

  async getDevolutionRules() {
    return this.request<DevolutionRule[]>('/masters/devolution-rules');
  }

  async getSystemConfig() {
    return this.request<SystemConfig>('/masters/config');
  }

  async updateSystemConfig(payload: Partial<SystemConfig>) {
    return this.request<SystemConfig>('/masters/config', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  }

  // 14. Audit Trail
  async getAuditLogs(tableNameOrParams?: any, limit: number = 50) {
    const qp = new URLSearchParams();
    if (typeof tableNameOrParams === 'object') {
      if (tableNameOrParams.table_name) qp.append('table_name', tableNameOrParams.table_name);
      if (tableNameOrParams.limit) qp.append('limit', String(tableNameOrParams.limit));
    } else if (typeof tableNameOrParams === 'string') {
      qp.append('table_name', tableNameOrParams);
      qp.append('limit', String(limit));
    }
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ items: AuditLog[] } | AuditLog[]>(`/audit${qs}`).then(res => {
      if (Array.isArray(res)) return { items: res };
      return res;
    });
  }

  // 15. Test Suite
  async runTestSuite() {
    return this.request<TestSuiteSummary>('/testsuite/run', {
      method: 'POST',
    });
  }

  // 16. System Notifications
  async getNotifications(role?: string, unreadOnly: boolean = false, limit: number = 40) {
    const qp = new URLSearchParams();
    if (role) qp.append('role', role);
    if (unreadOnly) qp.append('unread_only', 'true');
    qp.append('limit', String(limit));
    const qs = qp.toString() ? `?${qp.toString()}` : '';
    return this.request<{ unread_count: number; total: number; notifications: any[] }>(`/notifications${qs}`);
  }

  async markNotificationsRead(notificationId?: number, role?: string) {
    return this.request<{ status: string; message: string }>('/notifications/mark-read', {
      method: 'POST',
      body: JSON.stringify({
        notification_id: notificationId,
        role: role,
        all: !notificationId,
      }),
    });
  }

  async createNotification(payload: { title: string; text: string; level?: string; target_role?: string; action_module?: string; reference_id?: string }) {
    return this.request<any>('/notifications', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // 17. Demo Data Reset
  async resetDemoData() {
    return this.request<{ status: string; message: string; recon_summary: any }>('/config/reset-demo', {
      method: 'POST',
    });
  }
}

export const api = new ApiClient();
