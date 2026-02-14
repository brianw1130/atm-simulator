export interface AdminAccount {
  id: number;
  account_number: string;
  account_type: "CHECKING" | "SAVINGS";
  balance: string;
  available_balance: string;
  status: "ACTIVE" | "FROZEN" | "CLOSED";
  customer_name: string;
}

export interface AuditLogEntry {
  id: number;
  event_type: string;
  account_id: number | null;
  ip_address: string | null;
  session_id: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface MaintenanceStatus {
  enabled: boolean;
  reason: string | null;
}

export interface AdminCard {
  id: number;
  card_number: string;
  is_active: boolean;
  failed_attempts: number;
  is_locked: boolean;
}

export interface AdminAccountDetail {
  id: number;
  account_number: string;
  account_type: "CHECKING" | "SAVINGS";
  balance: string;
  available_balance: string;
  status: "ACTIVE" | "FROZEN" | "CLOSED";
  cards: AdminCard[];
}

export interface AdminCustomer {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  date_of_birth: string;
  is_active: boolean;
  account_count: number;
}

export interface AdminCustomerDetail extends AdminCustomer {
  accounts: AdminAccountDetail[];
}

export interface CustomerCreateData {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  email: string;
  phone?: string;
}

export interface CustomerUpdateData {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  email?: string;
  phone?: string;
}

export interface AccountCreateData {
  account_type: "CHECKING" | "SAVINGS";
  initial_balance_cents: number;
}

export interface DashboardStats {
  total_customers: number;
  active_customers: number;
  total_accounts: number;
  active_accounts: number;
  frozen_accounts: number;
  closed_accounts: number;
  total_balance_formatted: string;
}

export const AUDIT_EVENT_TYPES = [
  "AUTH_SUCCESS",
  "AUTH_FAILURE",
  "AUTH_LOCKOUT",
  "SESSION_CREATED",
  "SESSION_EXPIRED",
  "SESSION_TIMEOUT",
  "WITHDRAWAL_SUCCESS",
  "WITHDRAWAL_FAILED",
  "DEPOSIT_SUCCESS",
  "DEPOSIT_FAILED",
  "TRANSFER_SUCCESS",
  "TRANSFER_FAILED",
  "PIN_CHANGE_SUCCESS",
  "PIN_CHANGE_FAILED",
  "ACCOUNT_FROZEN",
  "ACCOUNT_UNFROZEN",
  "MAINTENANCE_ENABLED",
  "MAINTENANCE_DISABLED",
  "CUSTOMER_CREATED",
  "CUSTOMER_UPDATED",
  "CUSTOMER_DEACTIVATED",
  "CUSTOMER_ACTIVATED",
  "ACCOUNT_CREATED",
  "ACCOUNT_UPDATED",
  "ACCOUNT_CLOSED",
  "PIN_RESET_ADMIN",
  "DATA_EXPORTED",
  "DATA_IMPORTED",
] as const;
