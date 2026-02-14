import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useReducer, type ReactNode } from "react";
import { ATMProvider } from "../../state/ATMContext";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import App from "../../App";

// Mock API endpoints
vi.mock("../../api/endpoints", () => ({
  login: vi.fn(),
  logout: vi.fn().mockResolvedValue(undefined),
  listAccounts: vi.fn(),
  getBalance: vi.fn().mockReturnValue(new Promise(() => {})),
  refreshSession: vi.fn().mockResolvedValue({ message: "ok", timeout_seconds: "120" }),
}));

function renderApp() {
  return render(
    <ATMProvider>
      <App />
    </ATMProvider>,
  );
}

function TestProvider({
  children,
  initialState,
}: {
  children: ReactNode;
  initialState: ATMState;
}) {
  const [state, dispatch] = useReducer(atmReducer, initialState);
  return (
    <ATMContext.Provider value={{ state, dispatch }}>
      {children}
    </ATMContext.Provider>
  );
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the ATM frame with all housing components", () => {
    renderApp();
    expect(screen.getByTestId("atm-frame")).toBeInTheDocument();
    expect(screen.getByTestId("screen-bezel")).toBeInTheDocument();
    expect(screen.getByTestId("numeric-keypad")).toBeInTheDocument();
    expect(screen.getByTestId("card-slot")).toBeInTheDocument();
    expect(screen.getByTestId("cash-dispenser")).toBeInTheDocument();
    expect(screen.getByTestId("receipt-printer")).toBeInTheDocument();
  });

  it("starts on the welcome screen", () => {
    renderApp();
    expect(screen.getByTestId("welcome-screen")).toBeInTheDocument();
  });

  it("renders left and right side buttons", () => {
    renderApp();
    expect(screen.getByTestId("side-buttons-left")).toBeInTheDocument();
    expect(screen.getByTestId("side-buttons-right")).toBeInTheDocument();
  });

  it("transitions to pin entry when card is inserted", async () => {
    const user = userEvent.setup();
    renderApp();
    const input = screen.getByTestId("card-input");
    await user.type(input, "1000-0001-0001");
    await user.click(screen.getByTestId("insert-card-btn"));
    // AnimatePresence needs time to complete the exit/enter animation
    await waitFor(() => {
      expect(screen.getByTestId("pin-entry-screen")).toBeInTheDocument();
    });
  });

  it("enables keypad on welcome screen for card number entry", () => {
    renderApp();
    expect(screen.getByTestId("key-0")).toBeEnabled();
    expect(screen.getByTestId("key-enter")).toBeEnabled();
  });

  it("shows side buttons on main menu screen", () => {
    const mainMenuState: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "main_menu",
      sessionId: "sess-123",
      customerName: "Alice",
      accounts: [
        { id: 1, account_number: "1000-0001-0001", account_type: "CHECKING", balance: "5250.00", available_balance: "5250.00", status: "ACTIVE" },
      ],
      selectedAccountId: 1,
    };
    render(
      <TestProvider initialState={mainMenuState}>
        <App />
      </TestProvider>,
    );
    // Main menu should show labeled side buttons
    expect(screen.getByTestId("side-btn-left-balance")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left-withdraw")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left-deposit")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left-transfer")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-statement")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-pin-change")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-logout")).toBeInTheDocument();
  });

  it("navigates to withdrawal screen via side button", async () => {
    const user = userEvent.setup();
    const mainMenuState: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "main_menu",
      sessionId: "sess-123",
      customerName: "Alice",
      accounts: [],
      selectedAccountId: null,
    };
    render(
      <TestProvider initialState={mainMenuState}>
        <App />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("side-btn-left-withdraw"));
    await waitFor(() => {
      expect(screen.getByTestId("withdrawal-screen")).toBeInTheDocument();
    });
  });

  it("handles logout via side button", async () => {
    const user = userEvent.setup();
    const { logout: mockLogout } = await import("../../api/endpoints");
    const mainMenuState: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "main_menu",
      sessionId: "sess-123",
      customerName: "Alice",
      accounts: [],
      selectedAccountId: null,
    };
    render(
      <TestProvider initialState={mainMenuState}>
        <App />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("side-btn-right-logout"));
    expect(mockLogout).toHaveBeenCalled();
    await waitFor(() => {
      expect(screen.getByTestId("welcome-screen")).toBeInTheDocument();
    });
  });

  it("renders withdrawal screen", () => {
    const state: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "withdrawal",
      sessionId: "sess-123",
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("withdrawal-screen")).toBeInTheDocument();
  });

  it("renders balance inquiry screen", () => {
    const state: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "balance_inquiry",
      sessionId: "sess-123",
      selectedAccountId: 1,
      accounts: [
        { id: 1, account_number: "1000-0001-0001", account_type: "CHECKING", balance: "5250.00", available_balance: "5250.00", status: "ACTIVE" },
      ],
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("balance-inquiry-screen")).toBeInTheDocument();
  });

  it("renders error screen", () => {
    const state: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "error",
      sessionId: "sess-123",
      lastError: "Something went wrong",
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("error-screen")).toBeInTheDocument();
  });

  it("renders session timeout screen", () => {
    const state: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "session_timeout",
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("session-timeout-screen")).toBeInTheDocument();
  });

  it("renders maintenance screen", () => {
    const state: ATMState = {
      ...INITIAL_ATM_STATE,
      currentScreen: "maintenance",
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("maintenance-screen")).toBeInTheDocument();
  });

  // ── Side button coverage for non-main-menu screens ──────────────────

  const multiAccountState: ATMState = {
    ...INITIAL_ATM_STATE,
    sessionId: "sess-123",
    customerName: "Alice",
    accounts: [
      { id: 1, account_number: "1000-0001-0001", account_type: "CHECKING", balance: "5250.00", available_balance: "5250.00", status: "ACTIVE" },
      { id: 2, account_number: "1000-0001-0002", account_type: "SAVINGS", balance: "12500.00", available_balance: "12500.00", status: "ACTIVE" },
    ],
    selectedAccountId: 1,
    currentScreen: "main_menu",
  };

  it("shows account buttons and back on balance inquiry screen", () => {
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "balance_inquiry" }}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-left-checking")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left-savings")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-back")).toBeInTheDocument();
  });

  it("shows quick amounts and back on withdrawal screen", () => {
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "withdrawal" }}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-left--20")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left--40")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left--60")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left--100")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right--200")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-back")).toBeInTheDocument();
  });

  it("shows confirm and cancel on withdrawal confirm screen", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "withdrawal_confirm",
      pendingTransaction: { type: "withdrawal", amountCents: 10000 },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-right-confirm")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-cancel")).toBeInTheDocument();
  });

  it("shows another and done on receipt screens", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "withdrawal_receipt",
      lastReceipt: {
        receiptType: "withdrawal",
        reference_number: "REF-1",
        transaction_type: "WITHDRAWAL",
        amount: "$100.00",
        balance_after: "$5150.00",
        message: "OK",
        denominations: { twenties: 5, total_bills: 5, total_amount: "$100.00" },
      },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-right-another")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-done")).toBeInTheDocument();
  });

  it("shows deposit type selection buttons", () => {
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "deposit", pendingTransaction: null }}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-left-cash")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left-check")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-back")).toBeInTheDocument();
  });

  it("shows back button on deposit amount entry phase", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "deposit",
      pendingTransaction: { type: "deposit", amountCents: 0, depositType: "cash" },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-right-back")).toBeInTheDocument();
  });

  it("shows own account destinations on transfer screen", () => {
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "transfer" }}>
        <App />
      </TestProvider>,
    );
    // Current account is checking (id:1), so savings should appear as destination
    expect(screen.getByTestId("side-btn-left-savings")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-back")).toBeInTheDocument();
  });

  it("shows confirm and cancel on transfer confirm screen", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "transfer_confirm",
      pendingTransaction: { type: "transfer", amountCents: 50000, destinationAccount: "1000-0002-0001" },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-right-confirm")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-cancel")).toBeInTheDocument();
  });

  it("shows period buttons on statement screen", () => {
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "statement" }}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-left-7-days")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left-30-days")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-left-90-days")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-back")).toBeInTheDocument();
  });

  it("shows cancel on pin change screen", () => {
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "pin_change" }}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-right-cancel")).toBeInTheDocument();
  });

  it("renders deposit receipt screen with another/done buttons", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "deposit_receipt",
      lastReceipt: {
        receiptType: "deposit",
        reference_number: "REF-2",
        transaction_type: "DEPOSIT_CASH",
        amount: "$500.00",
        balance_after: "$5750.00",
        message: "OK",
        available_immediately: "$200.00",
        held_amount: "$300.00",
        hold_until: null,
      },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-right-another")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-done")).toBeInTheDocument();
  });

  it("renders transfer receipt screen with another/done buttons", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "transfer_receipt",
      lastReceipt: {
        receiptType: "transfer",
        reference_number: "REF-3",
        transaction_type: "TRANSFER_OUT",
        amount: "$200.00",
        balance_after: "$5050.00",
        message: "OK",
        destination_account: "1000-0002-0001",
      },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("side-btn-right-another")).toBeInTheDocument();
    expect(screen.getByTestId("side-btn-right-done")).toBeInTheDocument();
  });

  // ── Keypad handler wiring ───────────────────────────────────────────

  it("wires keypad digit to welcome screen handler", async () => {
    const user = userEvent.setup();
    renderApp();
    // Press '1' on keypad, card input should update
    await user.click(screen.getByTestId("key-1"));
    const input = screen.getByTestId("card-input");
    expect((input as HTMLInputElement).value).toBe("1");
  });

  it("wires keypad clear to welcome screen handler", async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByTestId("key-1"));
    await user.click(screen.getByTestId("key-2"));
    await user.click(screen.getByTestId("key-clear"));
    const input = screen.getByTestId("card-input");
    expect((input as HTMLInputElement).value).toBe("1");
  });

  it("wires keypad cancel to welcome screen handler", async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByTestId("key-1"));
    await user.click(screen.getByTestId("key-cancel"));
    const input = screen.getByTestId("card-input");
    expect((input as HTMLInputElement).value).toBe("");
  });

  it("wires keypad enter to welcome screen handler", async () => {
    const user = userEvent.setup();
    renderApp();
    // Press enter with no input should show error
    await user.click(screen.getByTestId("key-enter"));
    expect(screen.getByTestId("welcome-error")).toBeInTheDocument();
  });

  // ── Animation flag coverage ─────────────────────────────────────────

  it("renders withdrawal receipt with cash dispenser and receipt printer", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "withdrawal_receipt",
      lastReceipt: {
        receiptType: "withdrawal",
        reference_number: "REF-1",
        transaction_type: "WITHDRAWAL",
        amount: "$100.00",
        balance_after: "$5150.00",
        message: "OK",
        denominations: { twenties: 5, total_bills: 5, total_amount: "$100.00" },
      },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    // Cash dispenser and receipt printer components are rendered
    expect(screen.getByTestId("cash-dispenser")).toBeInTheDocument();
    expect(screen.getByTestId("receipt-printer")).toBeInTheDocument();
    // Card slot shows as active (card inserted)
    expect(screen.getByTestId("card-slot")).toBeInTheDocument();
  });

  it("renders deposit receipt with receipt printer", () => {
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "deposit_receipt",
      lastReceipt: {
        receiptType: "deposit",
        reference_number: "REF-2",
        transaction_type: "DEPOSIT_CASH",
        amount: "$500.00",
        balance_after: "$5750.00",
        message: "OK",
        available_immediately: "$200.00",
        held_amount: "$300.00",
        hold_until: null,
      },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("receipt-printer")).toBeInTheDocument();
    expect(screen.getByTestId("cash-dispenser")).toBeInTheDocument();
  });

  it("disables keypad when not on an input screen", () => {
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "balance_inquiry" }}>
        <App />
      </TestProvider>,
    );
    expect(screen.getByTestId("key-0")).toBeDisabled();
  });

  // ── Side button click behavior ──────────────────────────────────────

  it("navigates back from balance inquiry via side button", async () => {
    const user = userEvent.setup();
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "balance_inquiry" }}>
        <App />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("side-btn-right-back"));
    await waitFor(() => {
      expect(screen.getByTestId("main-menu-screen")).toBeInTheDocument();
    });
  });

  it("clicking deposit type Cash dispatches STAGE_TRANSACTION", async () => {
    const user = userEvent.setup();
    render(
      <TestProvider initialState={{ ...multiAccountState, currentScreen: "deposit", pendingTransaction: null }}>
        <App />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("side-btn-left-cash"));
    // After clicking Cash, deposit screen should show Cash Deposit form
    await waitFor(() => {
      expect(screen.getByText(/Cash Deposit/i)).toBeInTheDocument();
    });
  });

  it("clicking Another on receipt returns to main menu", async () => {
    const user = userEvent.setup();
    const state: ATMState = {
      ...multiAccountState,
      currentScreen: "withdrawal_receipt",
      lastReceipt: {
        receiptType: "withdrawal",
        reference_number: "REF-1",
        transaction_type: "WITHDRAWAL",
        amount: "$100.00",
        balance_after: "$5150.00",
        message: "OK",
        denominations: { twenties: 5, total_bills: 5, total_amount: "$100.00" },
      },
    };
    render(
      <TestProvider initialState={state}>
        <App />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("side-btn-right-another"));
    await waitFor(() => {
      expect(screen.getByTestId("main-menu-screen")).toBeInTheDocument();
    });
  });
});
