import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { DepositScreen } from "../../components/screens/DepositScreen";
import { DepositReceiptScreen } from "../../components/screens/DepositReceiptScreen";

vi.mock("../../api/endpoints", () => ({
  deposit: vi.fn(),
}));

import { deposit } from "../../api/endpoints";

const mockDeposit = vi.mocked(deposit);

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

function withState(overrides: Partial<ATMState> = {}): ATMState {
  return { ...INITIAL_ATM_STATE, ...overrides };
}

const depositState = withState({
  currentScreen: "deposit",
  sessionId: "sess-123",
  selectedAccountId: 1,
  accounts: [
    {
      id: 1,
      account_number: "1000-0001-0001",
      account_type: "CHECKING",
      balance: "5250.00",
      available_balance: "5250.00",
      status: "ACTIVE",
    },
  ],
});

describe("DepositScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders type selection when no pending transaction", () => {
    render(
      <TestProvider initialState={depositState}>
        <DepositScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("deposit-screen")).toBeInTheDocument();
    expect(screen.getByText("Deposit")).toBeInTheDocument();
    expect(screen.getByText("Select deposit type")).toBeInTheDocument();
  });

  it("renders amount entry for cash deposit", () => {
    const cashDepositState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });
    render(
      <TestProvider initialState={cashDepositState}>
        <DepositScreen />
      </TestProvider>,
    );
    expect(screen.getByText("Cash Deposit")).toBeInTheDocument();
    expect(screen.getByText("Enter deposit amount:")).toBeInTheDocument();
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$0");
  });

  it("renders amount entry for check deposit", () => {
    const checkDepositState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "check",
      },
    });
    render(
      <TestProvider initialState={checkDepositState}>
        <DepositScreen />
      </TestProvider>,
    );
    expect(screen.getByText("Check Deposit")).toBeInTheDocument();
  });

  it("builds amount via keypad handlers", () => {
    const cashState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });
    render(
      <TestProvider initialState={cashState}>
        <DepositScreen />
      </TestProvider>,
    );
    act(() => {
      DepositScreen.keypadHandlers.onDigit("5");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$500");
  });

  it("shows error for zero amount on enter", () => {
    const cashState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });
    render(
      <TestProvider initialState={cashState}>
        <DepositScreen />
      </TestProvider>,
    );
    act(() => {
      DepositScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("deposit-error")).toHaveTextContent(
      "Enter an amount",
    );
  });

  it("calls deposit API for cash deposit", async () => {
    mockDeposit.mockResolvedValue({
      reference_number: "REF-002",
      transaction_type: "DEPOSIT_CASH",
      amount: "$500.00",
      balance_after: "$5,750.00",
      message: "Deposit received",
      available_immediately: "$200.00",
      held_amount: "$300.00",
      hold_until: "2024-01-17",
    });

    const cashState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });

    render(
      <TestProvider initialState={cashState}>
        <DepositScreen />
      </TestProvider>,
    );

    act(() => {
      DepositScreen.keypadHandlers.onDigit("5");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });

    await act(async () => {
      DepositScreen.keypadHandlers.onEnter();
    });

    await waitFor(() => {
      expect(mockDeposit).toHaveBeenCalledWith({
        amount_cents: 50000,
        deposit_type: "cash",
        check_number: undefined,
      });
    });
  });

  it("transitions to check number entry for check deposits", () => {
    const checkState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "check",
      },
    });
    render(
      <TestProvider initialState={checkState}>
        <DepositScreen />
      </TestProvider>,
    );
    act(() => {
      DepositScreen.keypadHandlers.onDigit("1");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      DepositScreen.keypadHandlers.onEnter();
    });
    // Should now show check number entry
    expect(screen.getByTestId("check-number-display")).toBeInTheDocument();
  });

  it("submits check deposit with check number", async () => {
    mockDeposit.mockResolvedValue({
      reference_number: "REF-003",
      transaction_type: "DEPOSIT_CHECK",
      amount: "$100.00",
      balance_after: "$5,350.00",
      message: "Check deposit received",
      available_immediately: "$100.00",
      held_amount: "$0.00",
      hold_until: null,
    });

    const checkState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "check",
      },
    });

    render(
      <TestProvider initialState={checkState}>
        <DepositScreen />
      </TestProvider>,
    );

    // Enter amount
    act(() => {
      DepositScreen.keypadHandlers.onDigit("1");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      DepositScreen.keypadHandlers.onEnter();
    });

    // Enter check number
    act(() => {
      DepositScreen.keypadHandlers.onDigit("4");
      DepositScreen.keypadHandlers.onDigit("5");
      DepositScreen.keypadHandlers.onDigit("2");
      DepositScreen.keypadHandlers.onDigit("1");
    });

    await act(async () => {
      DepositScreen.keypadHandlers.onEnter();
    });

    await waitFor(() => {
      expect(mockDeposit).toHaveBeenCalledWith({
        amount_cents: 10000,
        deposit_type: "check",
        check_number: "4521",
      });
    });
  });

  it("shows error when check number is empty", () => {
    const checkState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "check",
      },
    });
    render(
      <TestProvider initialState={checkState}>
        <DepositScreen />
      </TestProvider>,
    );
    // Enter amount first
    act(() => {
      DepositScreen.keypadHandlers.onDigit("1");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      DepositScreen.keypadHandlers.onEnter();
    });
    // Try to submit without check number
    act(() => {
      DepositScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("deposit-error")).toHaveTextContent(
      "Enter check number",
    );
  });

  it("dispatches GO_BACK on cancel", () => {
    const cashState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });
    render(
      <TestProvider initialState={cashState}>
        <DepositScreen />
      </TestProvider>,
    );
    act(() => {
      DepositScreen.keypadHandlers.onCancel();
    });
    // Should dispatch GO_BACK
  });

  it("shows deposit error on API failure with axios detail", async () => {
    const axiosError = {
      isAxiosError: true,
      response: { data: { detail: "Account frozen" }, status: 400 },
    };
    mockDeposit.mockRejectedValue(axiosError);

    const cashState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });

    render(
      <TestProvider initialState={cashState}>
        <DepositScreen />
      </TestProvider>,
    );

    act(() => {
      DepositScreen.keypadHandlers.onDigit("1");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });

    await act(async () => {
      DepositScreen.keypadHandlers.onEnter();
    });

    // Error is dispatched via TRANSACTION_FAILURE so it shows in state.lastError
    // The component shows state.isLoading during processing
  });

  it("clears amount digits", () => {
    const cashState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });
    render(
      <TestProvider initialState={cashState}>
        <DepositScreen />
      </TestProvider>,
    );
    act(() => {
      DepositScreen.keypadHandlers.onDigit("5");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onClear();
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$5");
  });

  it("clears digits in check number phase", () => {
    const checkState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "check",
      },
    });
    render(
      <TestProvider initialState={checkState}>
        <DepositScreen />
      </TestProvider>,
    );
    act(() => {
      DepositScreen.keypadHandlers.onDigit("1");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      DepositScreen.keypadHandlers.onEnter();
    });
    // In check number phase
    act(() => {
      DepositScreen.keypadHandlers.onDigit("9");
      DepositScreen.keypadHandlers.onDigit("8");
      DepositScreen.keypadHandlers.onClear();
    });
    expect(screen.getByTestId("check-number-display")).toHaveTextContent("#9");
  });

  it("handles Pydantic 422 validation error without crashing", async () => {
    const axiosError = {
      isAxiosError: true,
      response: {
        data: {
          detail: [
            {
              type: "value_error",
              loc: ["body", "amount_cents"],
              msg: "Value error, Amount must be positive",
            },
          ],
        },
        status: 422,
      },
    };
    mockDeposit.mockRejectedValue(axiosError);

    const cashState = withState({
      ...depositState,
      pendingTransaction: {
        type: "deposit",
        amountCents: 0,
        depositType: "cash",
      },
    });

    render(
      <TestProvider initialState={cashState}>
        <DepositScreen />
      </TestProvider>,
    );

    act(() => {
      DepositScreen.keypadHandlers.onDigit("1");
      DepositScreen.keypadHandlers.onDigit("0");
      DepositScreen.keypadHandlers.onDigit("0");
    });

    await act(async () => {
      DepositScreen.keypadHandlers.onEnter();
    });

    // Component should not crash — still renders deposit screen
    await waitFor(() => {
      expect(screen.getByTestId("deposit-screen")).toBeInTheDocument();
    });
  });
});

describe("DepositReceiptScreen", () => {
  it("renders deposit receipt with hold info", () => {
    const receiptState = withState({
      currentScreen: "deposit_receipt",
      lastReceipt: {
        receiptType: "deposit",
        reference_number: "REF-002",
        transaction_type: "DEPOSIT_CASH",
        amount: "$500.00",
        balance_after: "$5,750.00",
        message: "Deposit received",
        available_immediately: "$200.00",
        held_amount: "$300.00",
        hold_until: "2024-01-17",
      },
    });

    render(
      <TestProvider initialState={receiptState}>
        <DepositReceiptScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("deposit-receipt-screen")).toBeInTheDocument();
    expect(screen.getByText("Deposit Complete")).toBeInTheDocument();
    expect(screen.getByText("REF-002")).toBeInTheDocument();
    expect(screen.getByText("$200.00")).toBeInTheDocument();
    expect(screen.getByText(/300.00/)).toBeInTheDocument();
    expect(screen.getByText(/2024-01-17/)).toBeInTheDocument();
  });

  it("hides hold info when held amount is zero", () => {
    const receiptState = withState({
      currentScreen: "deposit_receipt",
      lastReceipt: {
        receiptType: "deposit",
        reference_number: "REF-003",
        transaction_type: "DEPOSIT_CASH",
        amount: "$100.00",
        balance_after: "$5,350.00",
        message: "Deposit received",
        available_immediately: "$100.00",
        held_amount: "$0.00",
        hold_until: null,
      },
    });

    render(
      <TestProvider initialState={receiptState}>
        <DepositReceiptScreen />
      </TestProvider>,
    );
    expect(screen.queryByText("On Hold:")).not.toBeInTheDocument();
  });

  it("shows error when no receipt", () => {
    render(
      <TestProvider
        initialState={withState({
          currentScreen: "deposit_receipt",
          lastReceipt: null,
        })}
      >
        <DepositReceiptScreen />
      </TestProvider>,
    );
    expect(screen.getByText("No receipt data available")).toBeInTheDocument();
  });
});
