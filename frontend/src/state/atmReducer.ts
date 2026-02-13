import {
  INITIAL_ATM_STATE,
  SESSION_TIMEOUT_MS,
  type ATMAction,
  type ATMState,
} from "./types";

/** ATM state machine reducer. */
export function atmReducer(state: ATMState, action: ATMAction): ATMState {
  switch (action.type) {
    case "INSERT_CARD":
      return {
        ...state,
        cardNumber: action.cardNumber,
        currentScreen: "pin_entry",
        screenHistory: [...state.screenHistory, state.currentScreen],
        lastError: null,
      };

    case "LOGIN_SUCCESS":
      return {
        ...state,
        sessionId: action.payload.session_id,
        customerName: action.payload.customer_name,
        accountNumber: action.payload.account_number,
        accounts: action.accounts,
        selectedAccountId: action.accounts[0]?.id ?? null,
        currentScreen: "main_menu",
        screenHistory: [],
        lastError: null,
        isLoading: false,
        sessionExpiresAt: Date.now() + SESSION_TIMEOUT_MS,
      };

    case "LOGIN_FAILURE":
      return {
        ...state,
        lastError: action.error,
        isLoading: false,
      };

    case "NAVIGATE":
      return {
        ...state,
        currentScreen: action.screen,
        screenHistory: [...state.screenHistory, state.currentScreen],
        lastError: null,
      };

    case "GO_BACK": {
      const history = [...state.screenHistory];
      const previous = history.pop() ?? "main_menu";
      return {
        ...state,
        currentScreen: previous,
        screenHistory: history,
        lastError: null,
        pendingTransaction: null,
      };
    }

    case "SELECT_ACCOUNT":
      return {
        ...state,
        selectedAccountId: action.accountId,
      };

    case "SET_ACCOUNTS":
      return {
        ...state,
        accounts: action.accounts,
      };

    case "STAGE_TRANSACTION":
      return {
        ...state,
        pendingTransaction: action.transaction,
        currentScreen:
          action.transaction.type === "deposit"
            ? "deposit" // Deposits go straight through (no confirm screen)
            : action.transaction.type === "withdrawal"
              ? "withdrawal_confirm"
              : "transfer_confirm",
        screenHistory: [...state.screenHistory, state.currentScreen],
      };

    case "TRANSACTION_SUCCESS":
      return {
        ...state,
        lastReceipt: action.receipt,
        pendingTransaction: null,
        isLoading: false,
        currentScreen:
          action.receipt.receiptType === "withdrawal"
            ? "withdrawal_receipt"
            : action.receipt.receiptType === "deposit"
              ? "deposit_receipt"
              : "transfer_receipt",
        screenHistory: [...state.screenHistory, state.currentScreen],
      };

    case "TRANSACTION_FAILURE":
      return {
        ...state,
        lastError: action.error,
        isLoading: false,
        pendingTransaction: null,
      };

    case "SET_LOADING":
      return {
        ...state,
        isLoading: action.loading,
      };

    case "SESSION_TIMEOUT":
      sessionStorage.removeItem("atm_session_id");
      return {
        ...INITIAL_ATM_STATE,
        currentScreen: "session_timeout",
      };

    case "MAINTENANCE_MODE":
      return {
        ...state,
        currentScreen: "maintenance",
      };

    case "LOGOUT":
      sessionStorage.removeItem("atm_session_id");
      return { ...INITIAL_ATM_STATE };

    case "CLEAR_ERROR":
      return {
        ...state,
        lastError: null,
      };

    case "REFRESH_SESSION_TIMER":
      return {
        ...state,
        sessionExpiresAt: Date.now() + SESSION_TIMEOUT_MS,
      };

    default:
      return state;
  }
}
