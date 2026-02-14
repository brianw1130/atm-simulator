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
] as const;
