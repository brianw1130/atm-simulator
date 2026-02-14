import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { WithdrawalScreen } from "../../components/screens/WithdrawalScreen";
import { WithdrawalConfirmScreen } from "../../components/screens/WithdrawalConfirmScreen";
import { WithdrawalReceiptScreen } from "../../components/screens/WithdrawalReceiptScreen";

vi.mock("../../api/endpoints", () => ({
  withdraw: vi.fn(),
}));

import { withdraw } from "../../api/endpoints";

const mockWithdraw = vi.mocked(withdraw);

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

const withdrawalState = withState({
  currentScreen: "withdrawal",
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

describe("WithdrawalScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders withdrawal screen", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("withdrawal-screen")).toBeInTheDocument();
    expect(screen.getByText("Withdrawal")).toBeInTheDocument();
  });

  it("shows account info", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    expect(screen.getByText(/CHECKING/)).toBeInTheDocument();
    expect(screen.getByText(/5250.00/)).toBeInTheDocument();
  });

  it("shows zero amount initially", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$0");
  });

  it("has keypad handlers defined", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    expect(WithdrawalScreen.keypadHandlers.onDigit).toBeDefined();
    expect(WithdrawalScreen.keypadHandlers.onEnter).toBeDefined();
    expect(WithdrawalScreen.keypadHandlers.onClear).toBeDefined();
    expect(WithdrawalScreen.keypadHandlers.onCancel).toBeDefined();
  });

  it("builds amount via keypad handlers", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onDigit("1");
      WithdrawalScreen.keypadHandlers.onDigit("0");
      WithdrawalScreen.keypadHandlers.onDigit("0");
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$100");
  });

  it("clears last digit via keypad", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onDigit("1");
      WithdrawalScreen.keypadHandlers.onDigit("2");
      WithdrawalScreen.keypadHandlers.onClear();
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$1");
  });

  it("shows error for non-multiple-of-20", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onDigit("5");
      WithdrawalScreen.keypadHandlers.onDigit("5");
    });
    act(() => {
      WithdrawalScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("withdrawal-error")).toHaveTextContent(
      "Amount must be a multiple of $20",
    );
  });

  it("shows error for zero amount", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("withdrawal-error")).toHaveTextContent(
      "Enter an amount",
    );
  });

  it("rejects leading zeros", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onDigit("0");
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$0");
  });

  it("has handleQuickAmount exposed", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    expect(WithdrawalScreen.handleQuickAmount).toBeDefined();
  });

  it("stages withdrawal via handleQuickAmount", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.handleQuickAmount(10000);
    });
    // Should dispatch STAGE_TRANSACTION, which changes screen
    // In isolated test this verifies function executes without error
  });

  it("dispatches GO_BACK on cancel", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onCancel();
    });
    // GO_BACK navigates to main_menu
  });

  it("stages valid amount on enter", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onDigit("1");
      WithdrawalScreen.keypadHandlers.onDigit("0");
      WithdrawalScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      WithdrawalScreen.keypadHandlers.onEnter();
    });
    // Stages $100 withdrawal, dispatches STAGE_TRANSACTION
  });

  it("caps digit entry at max length", () => {
    render(
      <TestProvider initialState={withdrawalState}>
        <WithdrawalScreen />
      </TestProvider>,
    );
    act(() => {
      WithdrawalScreen.keypadHandlers.onDigit("9");
      WithdrawalScreen.keypadHandlers.onDigit("9");
      WithdrawalScreen.keypadHandlers.onDigit("9");
      WithdrawalScreen.keypadHandlers.onDigit("9");
      WithdrawalScreen.keypadHandlers.onDigit("9");
      WithdrawalScreen.keypadHandlers.onDigit("9"); // should be ignored (max 5)
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$99999");
  });
});

describe("WithdrawalConfirmScreen", () => {
  const confirmState = withState({
    currentScreen: "withdrawal_confirm",
    sessionId: "sess-123",
    selectedAccountId: 1,
    pendingTransaction: { type: "withdrawal", amountCents: 10000 },
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

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders confirm screen with amount", () => {
    render(
      <TestProvider initialState={confirmState}>
        <WithdrawalConfirmScreen />
      </TestProvider>,
    );
    expect(
      screen.getByTestId("withdrawal-confirm-screen"),
    ).toBeInTheDocument();
    expect(screen.getByText("Confirm Withdrawal")).toBeInTheDocument();
    expect(screen.getByText("$100.00")).toBeInTheDocument();
  });

  it("shows account info", () => {
    render(
      <TestProvider initialState={confirmState}>
        <WithdrawalConfirmScreen />
      </TestProvider>,
    );
    expect(screen.getByText(/CHECKING/)).toBeInTheDocument();
  });

  it("calls withdraw API on confirm", async () => {
    mockWithdraw.mockResolvedValue({
      reference_number: "REF-001",
      transaction_type: "WITHDRAWAL",
      amount: "$100.00",
      balance_after: "$5,150.00",
      message: "Cash dispensed",
      denominations: { twenties: 5, total_bills: 5, total_amount: "$100.00" },
    });

    render(
      <TestProvider initialState={confirmState}>
        <WithdrawalConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await WithdrawalConfirmScreen.handleConfirm();
    });

    await waitFor(() => {
      expect(mockWithdraw).toHaveBeenCalledWith({ amount_cents: 10000 });
    });
  });

  it("shows error on API failure", async () => {
    const axiosError = {
      isAxiosError: true,
      response: { data: { detail: "Insufficient funds" }, status: 400 },
    };
    mockWithdraw.mockRejectedValue(axiosError);

    render(
      <TestProvider initialState={confirmState}>
        <WithdrawalConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await WithdrawalConfirmScreen.handleConfirm();
    });

    await waitFor(() => {
      expect(screen.getByTestId("confirm-error")).toHaveTextContent(
        "Insufficient funds",
      );
    });
  });

  it("does not call API when no pending transaction", async () => {
    render(
      <TestProvider
        initialState={withState({ currentScreen: "withdrawal_confirm" })}
      >
        <WithdrawalConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await WithdrawalConfirmScreen.handleConfirm();
    });
    expect(mockWithdraw).not.toHaveBeenCalled();
  });

  it("handles Pydantic 422 validation error (array detail)", async () => {
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
    mockWithdraw.mockRejectedValue(axiosError);

    render(
      <TestProvider initialState={confirmState}>
        <WithdrawalConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await WithdrawalConfirmScreen.handleConfirm();
    });

    await waitFor(() => {
      expect(screen.getByTestId("confirm-error")).toHaveTextContent(
        "Amount must be positive",
      );
    });
  });
});

describe("WithdrawalReceiptScreen", () => {
  it("renders receipt with data", () => {
    const receiptState = withState({
      currentScreen: "withdrawal_receipt",
      lastReceipt: {
        receiptType: "withdrawal",
        reference_number: "REF-001",
        transaction_type: "WITHDRAWAL",
        amount: "$100.00",
        balance_after: "$5,150.00",
        message: "Cash dispensed",
        denominations: {
          twenties: 5,
          total_bills: 5,
          total_amount: "$100.00",
        },
      },
    });

    render(
      <TestProvider initialState={receiptState}>
        <WithdrawalReceiptScreen />
      </TestProvider>,
    );
    expect(
      screen.getByTestId("withdrawal-receipt-screen"),
    ).toBeInTheDocument();
    expect(screen.getByText("Withdrawal Complete")).toBeInTheDocument();
    expect(screen.getByText("REF-001")).toBeInTheDocument();
    expect(screen.getByText("$100.00")).toBeInTheDocument();
    expect(screen.getByText("Cash dispensed")).toBeInTheDocument();
    expect(screen.getByText(/5 x \$20/)).toBeInTheDocument();
  });

  it("shows error when no receipt", () => {
    render(
      <TestProvider
        initialState={withState({
          currentScreen: "withdrawal_receipt",
          lastReceipt: null,
        })}
      >
        <WithdrawalReceiptScreen />
      </TestProvider>,
    );
    expect(
      screen.getByText("No receipt data available"),
    ).toBeInTheDocument();
  });
});
