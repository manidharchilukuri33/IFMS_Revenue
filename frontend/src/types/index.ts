// User Roles
export type UserRole = 
  | 'SYSADMIN' 
  | 'TRE_ADMIN' 
  | 'PAO_MAKER' 
  | 'PAO_CHECK' 
  | 'DDO' 
  | 'FINANCE' 
  | 'BANK_OPS' 
  | 'AUDITOR' 
  | 'CITIZEN';

export interface UserSession {
  user_id: number;
  username: string;
  display_name: string;
  role: UserRole;
  pao_code?: string;
  dept_code?: string;
  organization_id?: number;
  org_branch_id?: number;
  workflow_status?: string;
}

// Master Entities
export interface Department {
  department_id: number;
  department_code: string;
  department_name: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface AgencyBank {
  bank_id: number;
  bank_code: string;
  bank_name: string;
  ifsc_prefix?: string;
  clearing_account_no?: string;
  nodal_officer_name?: string;
  nodal_officer_email?: string;
  nodal_officer_phone?: string;
  is_active: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface AgencyBankBranch {
  branch_id: number;
  bank_id: number;
  branch_code: string;
  branch_name: string;
  ifsc_code: string;
  city?: string;
  is_active: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface RevenuePortal {
  portal_id: number;
  portal_code: string;
  portal_name: string;
  department_id?: number;
  source_type?: string;
  api_endpoint?: string;
  technical_contact?: string;
  is_active: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface RevenueSource {
  source_id: number;
  source_code: string;
  source_name: string;
  department_id?: number;
  default_pao_code?: string;
  portal_id?: number;
  default_receipt_head_id?: number;
  tax_type?: string;
  default_receipt_head?: string;
  allowed_payment_modes?: string[];
  match_key_precedence?: string[];
  sla_rule_id?: number;
  is_tax_revenue?: boolean;
  is_active: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface SlaRule {
  sla_rule_id: number;
  rule_code?: string;
  rule_name?: string;
  payment_mode: string;
  allowed_remittance_days?: number;
  grace_days?: number;
  annual_penal_rate_pct?: number;
  calculation_basis?: string;
  base_date_type?: string;
  min_recovery_threshold?: number;
  t_plus_days?: number;
  penal_interest_rate_pct?: number;
  calendar_basis?: string;
  is_active: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface LocalBody {
  local_body_id: number;
  local_body_code?: string;
  body_type: string;
  local_body_name: string;
  treasury_code?: string;
  bank_account_no: string;
  bank_name?: string;
  ifsc_code: string;
  is_active: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface DevolutionRule {
  dev_rule_id?: number;
  devolution_rule_id?: number;
  rule_code?: string;
  local_body_id?: number;
  source_id?: number;
  revenue_source_id?: number;
  receipt_head_id?: number;
  local_body_type?: string;
  share_basis?: string;
  share_value?: number;
  share_percentage?: number;
  statutory_order_ref?: string;
  valid_from?: string;
  valid_to?: string;
  effective_from?: string;
  is_active: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface SystemConfig {
  config_id: number;
  demo_business_date: string;
  current_financial_year: string;
  amount_tolerance: number;
  date_tolerance_days: number;
  default_penal_rate_pct?: number;
  penal_day_basis?: number;
  exception_escalation_days?: number;
  suspense_head_id?: number;
  rat_suspense_head_id?: number;
  bank_clearing_head_id?: number;
  refund_deduct_head_id?: number;
  devolution_expenditure_head_id?: number;
  penal_interest_head_id?: number;
  penalty_head_id?: number;
  suspenseHead?: string;
  ratHead?: string;
  clearingAccount?: string;
  refundHead?: string;
  penalInterestHead?: string;
  penaltyHead?: string;
  bizDate?: string;
  fy?: string;
  amtTolerance?: number;
  dateTolerance?: number;
  penalRate?: number;
  penalDayBasis?: number;
  escalationDays?: number;
  system_mode?: string;
  allow_manual_override?: boolean;
  auto_escalate_days?: number;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

// Upload & Staging
export interface UploadBatch {
  batch_id: number;
  batch_no: string;
  batch_type: 'PORTAL' | 'BANK_SCROLL' | 'RBI_LUGGAGE' | 'MANUAL_ENTRY';
  source_filename: string;
  file_size_bytes?: number;
  data_date?: string;
  revenue_source_code?: string;
  department_id?: number;
  pao_code?: string;
  bank_id?: number;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  duplicate_records: number;
  control_total: number;
  uploaded_by: number;
  status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'PROCESSED' | 'DELETED';
  created_at: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface PortalStagingItem {
  portal_item_id: number;
  batch_id: number;
  portal_name?: string;
  challan_no: string;
  cpin?: string;
  cin?: string;
  payer_id?: string;
  payment_date: string;
  service_date?: string;
  amount: number;
  revenue_source: string;
  dept_code: string;
  pao_code: string;
  ddo_code?: string;
  receipt_head: string;
  payer_name?: string;
  payment_mode: string;
  penalty_amount?: number;
  portal_status?: string;
  dept_validated?: boolean;
  is_valid: boolean;
  is_duplicate?: boolean;
  validation_error?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface BankScrollStagingItem {
  scroll_item_id: number;
  batch_id: number;
  bank_code: string;
  branch_code?: string;
  scroll_no: string;
  scroll_date: string;
  challan_no?: string;
  cin?: string;
  cpin?: string;
  bank_reference_no?: string;
  utr_no?: string;
  payer_id?: string;
  payer_name?: string;
  payment_mode: string;
  payment_received_date?: string;
  amount: number;
  receipt_head?: string;
  bank_remittance_date?: string;
  bank_status?: string;
  is_valid: boolean;
  is_duplicate?: boolean;
  validation_error?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface RbiLuggageStagingItem {
  rbi_item_id: number;
  batch_id: number;
  file_reference_no?: string;
  luggage_date?: string;
  rbi_reference_no: string;
  settlement_date?: string;
  rbi_credit_date?: string;
  bank_code: string;
  govt_account_no?: string;
  amount: number;
  receipt_head?: string;
  challan_no?: string;
  cin?: string;
  cpin?: string;
  utr_no?: string;
  rbi_status?: string;
  is_valid: boolean;
  is_duplicate?: boolean;
  validation_error?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

// 3-Way Reconciliation
export interface ReconResult {
  recon_id: number;
  rev_transaction_id: string;
  run_id: number;
  group_key: string;
  match_key_type: string;
  challan_no?: string;
  cpin?: string;
  cin?: string;
  revenue_source: string;
  dept_code: string;
  pao_code: string;
  receipt_head: string;
  payer_name?: string;
  portal_total: number;
  bank_total: number;
  rbi_total: number;
  amount_difference: number;
  date_variance_days: number;
  sla_delay_days: number;
  penal_interest_amount: number;
  rule_applied: string;
  match_type: string;
  status: 'Matched' | 'Pending' | 'Suspend' | 'RAT' | 'Mismatch' | 'Duplicate' | 'Under Investigation' | 'Resolved' | 'Rejected' | 'Refunded' | string;
  flags: string[];
  match_reason: string;
  booking_status: string;
  is_manual_override: boolean;
  machine_status?: string;
  created_at: string;
  updated_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface ReconLegLinkage {
  link_id: number;
  recon_id: number;
  leg_type: 'PORTAL' | 'BANK_SCROLL' | 'RBI_CREDIT';
  portal_item_id?: number;
  scroll_item_id?: number;
  rbi_item_id?: number;
  leg_amount: number;
  leg_reference_no?: string;
  created_at: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface ReconDetail {
  recon: ReconResult;
  linkages: ReconLegLinkage[];
  portal_legs: PortalStagingItem[];
  bank_legs: BankScrollStagingItem[];
  rbi_legs: RbiLuggageStagingItem[];
}

export interface ReconRunSummary {
  run_id: number;
  run_no: string;
  business_date: string;
  total_processed: number;
  matched_count: number;
  pending_count: number;
  suspend_count: number;
  rat_count: number;
  mismatch_count: number;
  duplicate_count: number;
  under_investigation_count?: number;
  total_reconciled_amount: number;
  total_penal_interest: number;
  executed_by?: number;
  executed_at: string;
  is_current?: boolean;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

// Exceptions
export interface RevException {
  exception_id: number;
  exception_no: string;
  recon_id?: number;
  category: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  status: 'Open' | 'Assigned' | 'Escalated' | 'Resolved' | 'Closed';
  ownership_type: string;
  assigned_user_id?: number;
  due_date: string;
  exception_detail: string;
  resolution_reason?: string;
  resolution_remarks?: string;
  resolved_by?: number;
  resolved_at?: string;
  escalation_count: number;
  last_escalated_at?: string;
  created_at: string;
  updated_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface ExceptionLetter {
  letter_id: number;
  letter_no: string;
  exception_id: number;
  recipient_type: string;
  recipient_name: string;
  recipient_address?: string;
  letter_subject: string;
  letter_body: string;
  issued_date: string;
  issued_by?: number;
  status: string;
  created_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface ExceptionNote {
  note_id: number;
  exception_id: number;
  action_type: string;
  note_text: string;
  attachment_metadata?: any;
  created_by: number;
  created_at: string;
  organization_id?: number;
  org_branch_id?: number;
  updated_by?: number;
  workflow_status?: string;
}

// SLA & Penal Interest
export interface PenalClaim {
  claim_id: number;
  claim_no: string;
  bank_id: number;
  bank_name?: string;
  recon_id?: number;
  scroll_item_id?: number;
  principal_amount: number;
  payment_mode: string;
  base_date: string;
  base_date_type?: string;
  bank_remittance_date: string;
  permitted_days: number;
  actual_days: number;
  delay_days: number;
  annual_rate_pct: number;
  penal_interest_computed: number;
  penal_interest_recovered: number;
  penal_interest_waived: number;
  penal_interest_outstanding: number;
  letter_id?: number;
  letter_no?: string;
  status: 'COMPUTED' | 'DEMAND_ISSUED' | 'DISPUTED' | 'REMITTED' | 'WAIVED' | 'CLOSED' | 'PARTIALLY_RECOVERED' | 'RECOVERED';
  remarks?: string;
  created_at?: string;
  updated_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

// Refund Management
export interface RefundCase {
  refund_id: number;
  case_no: string;
  refund_type: 'NON_JUDICIAL_STAMP' | 'JUDICIAL_STAMP' | 'NON_JUDICIAL' | 'JUDICIAL' | string;
  applicant_name: string;
  applicant_id_proof?: string;
  applicant_bank_acc?: string;
  applicant_ifsc?: string;
  original_challan_no: string;
  recon_id?: number;
  reconciled_original_amount: number;
  claimed_amount: number;
  refundable_amount: number;
  is_amount_override?: boolean;
  override_reason?: string;
  e_stamp_cert_no?: string;
  shcil_certificate_no?: string;
  shcil_verified?: boolean;
  court_order_no?: string;
  current_stage?: number;
  stage_name: string;
  pending_role: string;
  status: 'Submitted' | 'Under Verification' | 'Deficiency Raised' | 'Bill Prepared' | 'Pending PAO Approval' | 'Approved' | 'Payment Instructed' | 'Paid' | 'Rejected' | 'Closed' | string;
  refund_bill_no?: string;
  bill_prepared_by?: number;
  bill_prepared_at?: string;
  pao_approved_by?: number;
  pao_approved_at?: string;
  pao_approval_ref?: string;
  pao_remarks?: string;
  epay_ref_no?: string;
  epay_instructed_at?: string;
  paid_at?: string;
  bank_account_no?: string;
  ifsc_code?: string;
  created_at: string;
  updated_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface RefundTimeline {
  timeline_id: number;
  refund_id: number;
  stage_name: string;
  action_taken: string;
  remarks?: string;
  action_by: number;
  action_at: string;
}

// Local Body Devolution
export interface DevolutionClaim {
  claim_id: number;
  claim_no: string;
  local_body_id: number;
  local_body_name?: string;
  source_id: number;
  source_code?: string;
  receipt_head_id?: number;
  dev_rule_id?: number;
  period_from: string;
  period_to: string;
  eligible_collections: number;
  share_pct: number;
  computed_entitlement: number;
  claimed_amount: number;
  variance_amount: number;
  approved_amount: number;
  status: 'Draft' | 'Computed' | 'Verified' | 'Approved' | 'Settled' | 'Claim Received' | 'Bill Generated' | 'Rejected' | string;
  scrutiny_remarks?: string;
  bill_no?: string;
  advice_no?: string;
  epay_ref_no?: string;
  settled_at?: string;
  created_at?: string;
  updated_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

// Accounting & Vouchers (Unified account_voucher schema)
export interface VoucherItem {
  item_id?: number;
  voucher_id: number;
  entry_type?: string;
  coa_id: number;
  coa_code?: string;
  coa_name?: string;
  head_code?: string;
  head_description?: string;
  dr_cr?: 'DR' | 'CR';
  amount: number;
  narration?: string;
  created_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

export interface ReceiptVoucher {
  voucher_id: number;
  sr_no?: number;
  voucher_no: string;
  recon_id?: number;
  voucher_date: string;
  voucher_type?: string;
  financial_year: string;
  pao_code: string;
  amount: number;
  debit_coa_id: number;
  credit_coa_id: number;
  debit_coa_code?: string;
  debit_coa_name?: string;
  credit_coa_code?: string;
  credit_coa_name?: string;
  demand_id?: number;
  department_id?: number;
  department_name?: string;
  ddo_id?: number;
  office_id?: number;
  scheme_id?: number;
  project_id?: number;
  bill_no?: string;
  bill_date?: string;
  payee_name?: string;
  narration?: string;
  status: 'Draft' | 'Verified' | 'Approved' | 'Rejected' | 'Posted' | 'Cancelled' | string;
  prepared_by?: number;
  prepared_at?: string;
  checker_user_id?: number;
  checker_remarks?: string;
  approved_at?: string;
  remarks?: string;
  created_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
  items?: VoucherItem[];
}

export type AccountVoucher = ReceiptVoucher;

export interface SuspenseItem {
  suspense_id: number;
  recon_id?: number;
  suspense_type: 'UNRECONCILED_SUSPENSE' | 'RAT_SUSPENSE' | 'AMOUNT_MISMATCH_SUSPENSE' | 'DUPLICATE_SUSPENSE' | string;
  suspense_head_id?: number;
  suspense_head_code?: string;
  suspense_head_name?: string;
  reference_no?: string;
  receipt_head?: string;
  amount: number;
  ageing_days?: number;
  status: 'OPEN' | 'HELD' | 'CLEARED' | 'TRANSFERRED' | 'WRITTEN_OFF' | string;
  cleared_amount?: number;
  balance_amount?: number;
  cleared_at?: string;
  clearing_remarks?: string;
  created_at?: string;
  updated_at?: string;
  organization_id?: number;
  org_branch_id?: number;
  created_by?: number;
  updated_by?: number;
  workflow_status?: string;
}

// Reports
export interface ReportMetadata {
  id: string;
  group: string;
  name: string;
  desc: string;
}

export interface ReportDataset {
  report_id: string;
  report_name: string;
  report_group: string;
  description: string;
  headers: string[];
  rows: any[][];
  money_columns: number[];
  total_records: number;
}

// Dashboard KPIs
export interface DashboardKPIs {
  gross_collections: number;
  total_receipts: number;
  matched_amount: number;
  matched_count: number;
  unmatched_amount: number;
  unmatched_count: number;
  match_rate: number;
  open_exceptions_count: number;
  open_exceptions_amount: number;
  penal_interest_computed: number;
  penal_interest_recovered: number;
  penal_interest_outstanding: number;
  pending_refunds_count: number;
  pending_refunds_amount: number;
  devolution_payable: number;
  draft_vouchers_count: number;
  draft_vouchers_amount: number;
}

export interface DashboardSourceItem {
  source_code: string;
  source_name: string;
  total_amount: number;
  matched_amount: number;
}

export interface DashboardTrendItem {
  date: string;
  gross: number;
  matched: number;
}

export interface DashboardSummary {
  kpis: DashboardKPIs;
  source_breakdown: DashboardSourceItem[];
  daily_trend: DashboardTrendItem[];
}

// Audit Trail
export interface AuditLog {
  audit_id: number;
  table_name: string;
  row_pk?: number;
  operation: 'INSERT' | 'UPDATE' | 'DELETE' | 'I' | 'U' | 'D';
  old_data?: Record<string, any>;
  new_data?: Record<string, any>;
  changed_by?: number;
  changed_at: string;
  workflow_status?: string;
}

// Test Suite
export interface TestCaseResult {
  test_id: string;
  name: string;
  status: 'PASS' | 'FAIL';
  details: string;
}

export interface TestSuiteSummary {
  total_tests: number;
  passed: number;
  failed: number;
  executed_at: string;
  results: TestCaseResult[];
}

// System Notifications
export interface NotificationItem {
  id: string;
  ts: string;
  title: string;
  text: string;
  level: 'ok' | 'warn' | 'err' | 'info';
  read: boolean;
  organization_id?: number;
  org_branch_id?: number;
  workflow_status?: string;
}
