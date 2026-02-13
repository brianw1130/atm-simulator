import { describe, it, expect, beforeEach, vi } from "vitest";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, SESSION_TIMEOUT_MS, type ATMState } from "../../state/types";

// Mock sessionStorage
const mockSessionStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
Object.defineProperty(window, "sessionStorage", { value: mockSessionStorage });

describe("atmReducer", () => {
  let state: ATMState;

  beforeEach(() => {
    state = { ...INITIAL_ATM_STATE };
    vi.clearAllMocks();
  });

  describe("INSERT_CARD", () => {
    it("transitions to pin_entry and stores card number", () => {
      const result = atmReducer(state, {
        type: "INSERT_CARD",
        cardNumber: "1000-0001-0001",
      });
      expect(result.currentScreen).toBe("pin_entry");
      expect(result.cardNumber).toBe("1000-0001-0001");
      expect(result.screenHistory).toEqual(["welcome"]);
      expect(result.lastError).toBeNull();
    });
  });

  describe("LOGIN_SUCCESS", () => {
    it("transitions to main_menu with session data", () => {
      state = { ...state, currentScreen: "pin_entry", cardNumber: "1000-0001-0001" };
      const accounts = [
        { id: 1, account_number: "1000-0001-0001", account_type: "CHECKING" as const, balance: "5250.00", available_balance: "5250.00", status: "ACTIVE" as const },
      ];
      const result = atmReducer(state, {
        type: "LOGIN_SUCCESS",
        payload: {
          session_id: "sess-123",
          customer_name: "Alice Johnson",
          account_number: "1000-0001-0001",
          message: "Login successful",
        },
        accounts,
      });
      expect(result.currentScreen).toBe("main_menu");
      expect(result.sessionId).toBe("sess-123");
      expect(result.customerName).toBe("Alice Johnson");
      expect(result.accounts).toEqual(accounts);
      expect(result.selectedAccountId).toBe(1);
      expect(result.isLoading).toBe(false);
      expect(result.lastError).toBeNull();
      expect(result.sessionExpiresAt).toBeGreaterThan(0);
    });

    it("handles empty accounts list", () => {
      const result = atmReducer(state, {
        type: "LOGIN_SUCCESS",
        payload: {
          session_id: "sess-123",
          customer_name: "Alice",
          account_number: "1000-0001-0001",
          message: "Login successful",
        },
        accounts: [],
      });
      expect(result.selectedAccountId).toBeNull();
    });
  });

  describe("LOGIN_FAILURE", () => {
    it("sets error and stops loading", () => {
      state = { ...state, isLoading: true };
      const result = atmReducer(state, {
        type: "LOGIN_FAILURE",
        error: "Invalid PIN",
      });
      expect(result.lastError).toBe("Invalid PIN");
      expect(result.isLoading).toBe(false);
    });
  });

  describe("NAVIGATE", () => {
    it("changes screen and pushes history", () => {
      state = { ...state, currentScreen: "main_menu" };
      const result = atmReducer(state, {
        type: "NAVIGATE",
        screen: "withdrawal",
      });
      expect(result.currentScreen).toBe("withdrawal");
      expect(result.screenHistory).toEqual(["main_menu"]);
      expect(result.lastError).toBeNull();
    });
  });

  describe("GO_BACK", () => {
    it("pops history and returns to previous screen", () => {
      state = {
        ...state,
        currentScreen: "withdrawal",
        screenHistory: ["main_menu"],
      };
      const result = atmReducer(state, { type: "GO_BACK" });
      expect(result.currentScreen).toBe("main_menu");
      expect(result.screenHistory).toEqual([]);
      expect(result.pendingTransaction).toBeNull();
    });

    it("falls back to main_menu when history is empty", () => {
      state = { ...state, currentScreen: "withdrawal", screenHistory: [] };
      const result = atmReducer(state, { type: "GO_BACK" });
      expect(result.currentScreen).toBe("main_menu");
    });
  });

  describe("SELECT_ACCOUNT", () => {
    it("updates selected account ID", () => {
      const result = atmReducer(state, {
        type: "SELECT_ACCOUNT",
        accountId: 42,
      });
      expect(result.selectedAccountId).toBe(42);
    });
  });

  describe("SET_ACCOUNTS", () => {
    it("replaces accounts list", () => {
      const accounts = [
        { id: 1, account_number: "1000-0001-0001", account_type: "CHECKING" as const, balance: "100.00", available_balance: "100.00", status: "ACTIVE" as const },
      ];
      const result = atmReducer(state, { type: "SET_ACCOUNTS", accounts });
      expect(result.accounts).toEqual(accounts);
    });
  });

  describe("STAGE_TRANSACTION", () => {
    it("stages withdrawal and navigates to confirm screen", () => {
      state = { ...state, currentScreen: "withdrawal" };
      const result = atmReducer(state, {
        type: "STAGE_TRANSACTION",
        transaction: { type: "withdrawal", amountCents: 10000 },
      });
      expect(result.pendingTransaction).toEqual({ type: "withdrawal", amountCents: 10000 });
      expect(result.currentScreen).toBe("withdrawal_confirm");
    });

    it("stages transfer and navigates to confirm screen", () => {
      state = { ...state, currentScreen: "transfer" };
      const result = atmReducer(state, {
        type: "STAGE_TRANSACTION",
        transaction: { type: "transfer", amountCents: 5000, destinationAccount: "1000-0002-0001" },
      });
      expect(result.currentScreen).toBe("transfer_confirm");
    });

    it("stages deposit without confirm screen", () => {
      state = { ...state, currentScreen: "deposit" };
      const result = atmReducer(state, {
        type: "STAGE_TRANSACTION",
        transaction: { type: "deposit", amountCents: 20000, depositType: "cash" },
      });
      expect(result.currentScreen).toBe("deposit");
    });
  });

  describe("TRANSACTION_SUCCESS", () => {
    it("navigates to withdrawal receipt", () => {
      state = { ...state, currentScreen: "withdrawal_confirm" };
      const receipt = {
        receiptType: "withdrawal" as const,
        reference_number: "REF-123",
        transaction_type: "WITHDRAWAL",
        amount: "100.00",
        balance_after: "5150.00",
        message: "Withdrawal successful",
        denominations: { twenties: 5, total_bills: 5, total_amount: "100.00" },
      };
      const result = atmReducer(state, {
        type: "TRANSACTION_SUCCESS",
        receipt,
      });
      expect(result.currentScreen).toBe("withdrawal_receipt");
      expect(result.lastReceipt).toEqual(receipt);
      expect(result.pendingTransaction).toBeNull();
      expect(result.isLoading).toBe(false);
    });

    it("navigates to deposit receipt", () => {
      const receipt = {
        receiptType: "deposit" as const,
        reference_number: "REF-456",
        transaction_type: "DEPOSIT_CASH",
        amount: "500.00",
        balance_after: "1350.75",
        message: "Deposit successful",
        available_immediately: "200.00",
        held_amount: "300.00",
        hold_until: "2026-02-13T00:00:00Z",
      };
      const result = atmReducer(state, {
        type: "TRANSACTION_SUCCESS",
        receipt,
      });
      expect(result.currentScreen).toBe("deposit_receipt");
    });

    it("navigates to transfer receipt", () => {
      const receipt = {
        receiptType: "transfer" as const,
        reference_number: "REF-789",
        transaction_type: "TRANSFER_OUT",
        amount: "200.00",
        balance_after: "5050.00",
        message: "Transfer successful",
        source_account: "1000-0001-0001",
        destination_account: "1000-0002-0001",
      };
      const result = atmReducer(state, {
        type: "TRANSACTION_SUCCESS",
        receipt,
      });
      expect(result.currentScreen).toBe("transfer_receipt");
    });
  });

  describe("TRANSACTION_FAILURE", () => {
    it("sets error and clears pending transaction", () => {
      state = { ...state, isLoading: true, pendingTransaction: { type: "withdrawal", amountCents: 10000 } };
      const result = atmReducer(state, {
        type: "TRANSACTION_FAILURE",
        error: "Insufficient funds",
      });
      expect(result.lastError).toBe("Insufficient funds");
      expect(result.isLoading).toBe(false);
      expect(result.pendingTransaction).toBeNull();
    });
  });

  describe("SET_LOADING", () => {
    it("sets loading state", () => {
      const result = atmReducer(state, { type: "SET_LOADING", loading: true });
      expect(result.isLoading).toBe(true);
    });
  });

  describe("SESSION_TIMEOUT", () => {
    it("resets to initial state on timeout screen", () => {
      state = { ...state, sessionId: "sess-123", currentScreen: "main_menu" };
      const result = atmReducer(state, { type: "SESSION_TIMEOUT" });
      expect(result.currentScreen).toBe("session_timeout");
      expect(result.sessionId).toBeNull();
      expect(result.customerName).toBeNull();
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith("atm_session_id");
    });
  });

  describe("MAINTENANCE_MODE", () => {
    it("navigates to maintenance screen", () => {
      const result = atmReducer(state, { type: "MAINTENANCE_MODE" });
      expect(result.currentScreen).toBe("maintenance");
    });
  });

  describe("LOGOUT", () => {
    it("resets to initial state", () => {
      state = { ...state, sessionId: "sess-123", customerName: "Alice", currentScreen: "main_menu" };
      const result = atmReducer(state, { type: "LOGOUT" });
      expect(result.currentScreen).toBe("welcome");
      expect(result.sessionId).toBeNull();
      expect(result.customerName).toBeNull();
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith("atm_session_id");
    });
  });

  describe("CLEAR_ERROR", () => {
    it("clears the last error", () => {
      state = { ...state, lastError: "Some error" };
      const result = atmReducer(state, { type: "CLEAR_ERROR" });
      expect(result.lastError).toBeNull();
    });
  });

  describe("REFRESH_SESSION_TIMER", () => {
    it("extends session expiry", () => {
      const before = Date.now();
      const result = atmReducer(state, { type: "REFRESH_SESSION_TIMER" });
      expect(result.sessionExpiresAt).toBeGreaterThanOrEqual(before + SESSION_TIMEOUT_MS);
    });
  });

  describe("default case", () => {
    it("returns state unchanged for unknown action", () => {
      const result = atmReducer(state, { type: "UNKNOWN" } as unknown as Parameters<typeof atmReducer>[1]);
      expect(result).toBe(state);
    });
  });
});
