import type {
  AccountSummary,
  WithdrawalResponse,
  DepositResponse,
  TransferResponse,
  LoginResponse,
} from "../api/types";

/** All possible ATM screen states. */
export type ATMScreen =
  | "welcome"
  | "pin_entry"
  | "main_menu"
  | "balance_inquiry"
  | "withdrawal"
  | "withdrawal_confirm"
  | "withdrawal_receipt"
  | "deposit"
  | "deposit_receipt"
  | "transfer"
  | "transfer_confirm"
  | "transfer_receipt"
  | "statement"
  | "pin_change"
  | "session_timeout"
  | "error"
  | "maintenance";

/** Pending transaction staged for a confirmation screen. */
export interface PendingTransaction {
  type: "withdrawal" | "deposit" | "transfer";
  amountCents: number;
  depositType?: "cash" | "check";
  checkNumber?: string;
  destinationAccount?: string;
}

/** Receipt data shown after a completed transaction. */
export type TransactionReceipt =
  | (WithdrawalResponse & { receiptType: "withdrawal" })
  | (DepositResponse & { receiptType: "deposit" })
  | (TransferResponse & { receiptType: "transfer" });

/** Complete ATM application state. */
export interface ATMState {
  currentScreen: ATMScreen;
  screenHistory: ATMScreen[];
  sessionId: string | null;
  customerName: string | null;
  accountNumber: string | null;
  cardNumber: string | null;
  accounts: AccountSummary[];
  selectedAccountId: number | null;
  lastError: string | null;
  isLoading: boolean;
  pendingTransaction: PendingTransaction | null;
  lastReceipt: TransactionReceipt | null;
  sessionExpiresAt: number | null;
}

/** All actions the ATM state machine can process. */
export type ATMAction =
  | { type: "INSERT_CARD"; cardNumber: string }
  | { type: "LOGIN_SUCCESS"; payload: LoginResponse; accounts: AccountSummary[] }
  | { type: "LOGIN_FAILURE"; error: string }
  | { type: "NAVIGATE"; screen: ATMScreen }
  | { type: "GO_BACK" }
  | { type: "SELECT_ACCOUNT"; accountId: number }
  | { type: "SET_ACCOUNTS"; accounts: AccountSummary[] }
  | { type: "STAGE_TRANSACTION"; transaction: PendingTransaction }
  | { type: "TRANSACTION_SUCCESS"; receipt: TransactionReceipt }
  | { type: "TRANSACTION_FAILURE"; error: string }
  | { type: "SET_LOADING"; loading: boolean }
  | { type: "SESSION_TIMEOUT" }
  | { type: "MAINTENANCE_MODE" }
  | { type: "LOGOUT" }
  | { type: "CLEAR_ERROR" }
  | { type: "REFRESH_SESSION_TIMER" };

/** Initial state for a fresh ATM session. */
export const INITIAL_ATM_STATE: ATMState = {
  currentScreen: "welcome",
  screenHistory: [],
  sessionId: null,
  customerName: null,
  accountNumber: null,
  cardNumber: null,
  accounts: [],
  selectedAccountId: null,
  lastError: null,
  isLoading: false,
  pendingTransaction: null,
  lastReceipt: null,
  sessionExpiresAt: null,
};

/** Session timeout in milliseconds. */
export const SESSION_TIMEOUT_MS = 120_000;
