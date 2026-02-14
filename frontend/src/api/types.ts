/** TypeScript interfaces matching backend Pydantic schemas. */

// --- Auth ---

export interface LoginRequest {
  card_number: string;
  pin: string;
}

export interface LoginResponse {
  session_id: string;
  account_number: string;
  customer_name: string;
  message: string;
}

export interface PinChangeRequest {
  current_pin: string;
  new_pin: string;
  confirm_pin: string;
}

export interface SessionRefreshResponse {
  message: string;
  timeout_seconds: string;
}

// --- Accounts ---

export interface AccountSummary {
  id: number;
  account_number: string;
  account_type: "CHECKING" | "SAVINGS";
  balance: string;
  available_balance: string;
  status: "ACTIVE" | "FROZEN" | "CLOSED";
}

export interface MiniStatementEntry {
  date: string;
  description: string;
  amount: string;
  balance_after: string;
}

export interface BalanceInquiryResponse {
  account: AccountSummary;
  recent_transactions: MiniStatementEntry[];
}

export interface AccountListResponse {
  accounts: AccountSummary[];
}

// --- Transactions ---

export interface WithdrawalRequest {
  amount_cents: number;
}

export interface DenominationBreakdown {
  twenties: number;
  total_bills: number;
  total_amount: string;
}

export interface WithdrawalResponse {
  reference_number: string;
  transaction_type: string;
  amount: string;
  balance_after: string;
  message: string;
  denominations: DenominationBreakdown;
}

export interface DepositRequest {
  amount_cents: number;
  deposit_type: "cash" | "check";
  check_number?: string;
}

export interface DepositResponse {
  reference_number: string;
  transaction_type: string;
  amount: string;
  balance_after: string;
  message: string;
  available_immediately: string;
  held_amount: string;
  hold_until: string | null;
}

export interface TransferRequest {
  destination_account_number: string;
  amount_cents: number;
}

export interface TransferResponse {
  reference_number: string;
  transaction_type: string;
  amount: string;
  balance_after: string;
  message: string;
  source_account: string;
  destination_account: string;
}

// --- Statements ---

export interface StatementRequest {
  days?: number;
  start_date?: string;
  end_date?: string;
}

export interface StatementResponse {
  file_path: string;
  period: string;
  transaction_count: number;
  opening_balance: string;
  closing_balance: string;
}

export interface AsyncStatementResponse {
  task_id: string;
  status: string;
}

export interface StatementStatusResponse {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  result?: StatementResponse;
  error?: string;
}

// --- Errors ---

export interface ErrorResponse {
  detail: string;
  error?: string;
  error_code?: string;
}
