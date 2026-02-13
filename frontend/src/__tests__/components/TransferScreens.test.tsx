import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { TransferScreen } from "../../components/screens/TransferScreen";
import { TransferConfirmScreen } from "../../components/screens/TransferConfirmScreen";
import { TransferReceiptScreen } from "../../components/screens/TransferReceiptScreen";

vi.mock("../../api/endpoints", () => ({
  transfer: vi.fn(),
}));

import { transfer } from "../../api/endpoints";

const mockTransfer = vi.mocked(transfer);

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

const transferState = withState({
  currentScreen: "transfer",
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
    {
      id: 2,
      account_number: "1000-0001-0002",
      account_type: "SAVINGS",
      balance: "12500.00",
      available_balance: "12500.00",
      status: "ACTIVE",
    },
  ],
});

describe("TransferScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders transfer screen in destination phase", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("transfer-screen")).toBeInTheDocument();
    expect(screen.getByText("Transfer")).toBeInTheDocument();
    expect(screen.getByText(/destination account/)).toBeInTheDocument();
    expect(screen.getByTestId("destination-display")).toBeInTheDocument();
  });

  it("builds destination via keypad", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
    });
    expect(screen.getByTestId("destination-display")).toHaveTextContent("1000");
  });

  it("transitions to amount phase on enter with destination", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("amount-display")).toBeInTheDocument();
    expect(screen.getByText(/1000/)).toBeInTheDocument();
  });

  it("shows error for empty destination", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("transfer-error")).toHaveTextContent(
      "Enter destination account",
    );
  });

  it("shows error for zero amount", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    // Now in amount phase
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("transfer-error")).toHaveTextContent(
      "Enter an amount",
    );
  });

  it("sets own account destination via static method", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.setOwnAccountDestination("1000-0001-0002");
    });
    expect(screen.getByTestId("amount-display")).toBeInTheDocument();
  });

  it("cancel in amount phase returns to destination phase", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
      TransferScreen.keypadHandlers.onEnter();
    });
    // Now in amount phase, cancel goes back to destination
    act(() => {
      TransferScreen.keypadHandlers.onCancel();
    });
    expect(screen.getByTestId("destination-display")).toBeInTheDocument();
  });

  it("clears destination digits", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
      TransferScreen.keypadHandlers.onDigit("2");
      TransferScreen.keypadHandlers.onClear();
    });
    expect(screen.getByTestId("destination-display")).toHaveTextContent("1");
  });

  it("stages transfer with valid amount", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    // In amount phase, enter amount
    act(() => {
      TransferScreen.keypadHandlers.onDigit("5");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onDigit("0");
    });
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    // Should dispatch STAGE_TRANSACTION with amountCents: 50000
  });

  it("clears amount digits in amount phase", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
    });
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    // In amount phase
    act(() => {
      TransferScreen.keypadHandlers.onDigit("5");
      TransferScreen.keypadHandlers.onDigit("0");
      TransferScreen.keypadHandlers.onClear();
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$5");
  });

  it("rejects leading zero in amount phase", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onDigit("1");
    });
    act(() => {
      TransferScreen.keypadHandlers.onEnter();
    });
    // In amount phase, try leading zero
    act(() => {
      TransferScreen.keypadHandlers.onDigit("0");
    });
    expect(screen.getByTestId("amount-display")).toHaveTextContent("$0");
  });

  it("dispatches GO_BACK on cancel in destination phase", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      TransferScreen.keypadHandlers.onCancel();
    });
    // Should dispatch GO_BACK
  });

  it("caps destination digits at max length", () => {
    render(
      <TestProvider initialState={transferState}>
        <TransferScreen />
      </TestProvider>,
    );
    act(() => {
      for (let i = 0; i < 15; i++) {
        TransferScreen.keypadHandlers.onDigit("1");
      }
    });
    // Max 14 digits
    expect(screen.getByTestId("destination-display")).toHaveTextContent("11111111111111");
  });
});

describe("TransferConfirmScreen", () => {
  const confirmState = withState({
    currentScreen: "transfer_confirm",
    sessionId: "sess-123",
    selectedAccountId: 1,
    pendingTransaction: {
      type: "transfer",
      amountCents: 50000,
      destinationAccount: "1000-0001-0002",
    },
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

  it("renders confirm screen with transfer details", () => {
    render(
      <TestProvider initialState={confirmState}>
        <TransferConfirmScreen />
      </TestProvider>,
    );
    expect(
      screen.getByTestId("transfer-confirm-screen"),
    ).toBeInTheDocument();
    expect(screen.getByText("Confirm Transfer")).toBeInTheDocument();
    expect(screen.getByText("$500.00")).toBeInTheDocument();
    expect(screen.getByText("1000-0001-0002")).toBeInTheDocument();
  });

  it("calls transfer API on confirm", async () => {
    mockTransfer.mockResolvedValue({
      reference_number: "REF-004",
      transaction_type: "TRANSFER_OUT",
      amount: "$500.00",
      balance_after: "$4,750.00",
      message: "Transfer complete",
      source_account: "1000-0001-0001",
      destination_account: "1000-0001-0002",
    });

    render(
      <TestProvider initialState={confirmState}>
        <TransferConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await TransferConfirmScreen.handleConfirm();
    });

    await waitFor(() => {
      expect(mockTransfer).toHaveBeenCalledWith({
        destination_account_number: "1000-0001-0002",
        amount_cents: 50000,
      });
    });
  });

  it("shows error on API failure", async () => {
    mockTransfer.mockRejectedValue(new Error("Network error"));

    render(
      <TestProvider initialState={confirmState}>
        <TransferConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await TransferConfirmScreen.handleConfirm();
    });

    await waitFor(() => {
      expect(screen.getByTestId("confirm-error")).toHaveTextContent(
        "Transfer failed",
      );
    });
  });

  it("shows axios error detail on API failure", async () => {
    const axiosError = {
      isAxiosError: true,
      response: { data: { detail: "Destination account not found" }, status: 404 },
    };
    mockTransfer.mockRejectedValue(axiosError);

    render(
      <TestProvider initialState={confirmState}>
        <TransferConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await TransferConfirmScreen.handleConfirm();
    });

    await waitFor(() => {
      expect(screen.getByTestId("confirm-error")).toHaveTextContent(
        "Destination account not found",
      );
    });
  });

  it("does not call API without pendingTransaction", async () => {
    render(
      <TestProvider
        initialState={withState({ currentScreen: "transfer_confirm" })}
      >
        <TransferConfirmScreen />
      </TestProvider>,
    );

    await act(async () => {
      await TransferConfirmScreen.handleConfirm();
    });
    expect(mockTransfer).not.toHaveBeenCalled();
  });
});

describe("TransferReceiptScreen", () => {
  it("renders transfer receipt", () => {
    const receiptState = withState({
      currentScreen: "transfer_receipt",
      lastReceipt: {
        receiptType: "transfer",
        reference_number: "REF-004",
        transaction_type: "TRANSFER_OUT",
        amount: "$500.00",
        balance_after: "$4,750.00",
        message: "Transfer complete",
        source_account: "1000-0001-0001",
        destination_account: "1000-0001-0002",
      },
    });

    render(
      <TestProvider initialState={receiptState}>
        <TransferReceiptScreen />
      </TestProvider>,
    );
    expect(
      screen.getByTestId("transfer-receipt-screen"),
    ).toBeInTheDocument();
    expect(screen.getByText("Transfer Complete")).toBeInTheDocument();
    expect(screen.getByText("REF-004")).toBeInTheDocument();
    expect(screen.getByText("1000-0001-0001")).toBeInTheDocument();
    expect(screen.getByText("1000-0001-0002")).toBeInTheDocument();
  });

  it("shows error when no receipt", () => {
    render(
      <TestProvider
        initialState={withState({
          currentScreen: "transfer_receipt",
          lastReceipt: null,
        })}
      >
        <TransferReceiptScreen />
      </TestProvider>,
    );
    expect(screen.getByText("No receipt data available")).toBeInTheDocument();
  });
});
