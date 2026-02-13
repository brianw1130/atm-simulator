import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { BalanceInquiryScreen } from "../../components/screens/BalanceInquiryScreen";

vi.mock("../../api/endpoints", () => ({
  getBalance: vi.fn(),
}));

import { getBalance } from "../../api/endpoints";

const mockGetBalance = vi.mocked(getBalance);

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

const balanceState = withState({
  currentScreen: "balance_inquiry",
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

describe("BalanceInquiryScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state initially", () => {
    mockGetBalance.mockReturnValue(new Promise(() => {}));
    render(
      <TestProvider initialState={balanceState}>
        <BalanceInquiryScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("balance-inquiry-screen")).toBeInTheDocument();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("displays balance after API call", async () => {
    mockGetBalance.mockResolvedValue({
      account: {
        id: 1,
        account_number: "1000-0001-0001",
        account_type: "CHECKING",
        balance: "5250.00",
        available_balance: "5250.00",
        status: "ACTIVE",
      },
      recent_transactions: [],
    });

    await act(async () => {
      render(
        <TestProvider initialState={balanceState}>
          <BalanceInquiryScreen />
        </TestProvider>,
      );
    });

    await waitFor(() => {
      expect(screen.getAllByText("$5250.00")).toHaveLength(2);
    });
    expect(screen.getByText(/CHECKING/)).toBeInTheDocument();
  });

  it("shows mini-statement with transactions", async () => {
    mockGetBalance.mockResolvedValue({
      account: {
        id: 1,
        account_number: "1000-0001-0001",
        account_type: "CHECKING",
        balance: "5250.00",
        available_balance: "5250.00",
        status: "ACTIVE",
      },
      recent_transactions: [
        {
          date: "2024-01-15",
          description: "ATM Withdrawal",
          amount: "-$100.00",
          balance_after: "$5,250.00",
        },
      ],
    });

    await act(async () => {
      render(
        <TestProvider initialState={balanceState}>
          <BalanceInquiryScreen />
        </TestProvider>,
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("mini-statement")).toBeInTheDocument();
    });
    expect(screen.getByText("ATM Withdrawal")).toBeInTheDocument();
  });

  it("shows error on API failure", async () => {
    mockGetBalance.mockRejectedValue(new Error("Network error"));

    await act(async () => {
      render(
        <TestProvider initialState={balanceState}>
          <BalanceInquiryScreen />
        </TestProvider>,
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Failed to retrieve balance")).toBeInTheDocument();
    });
  });

  it("does not fetch when no selectedAccountId", () => {
    render(
      <TestProvider initialState={withState({ selectedAccountId: null })}>
        <BalanceInquiryScreen />
      </TestProvider>,
    );
    expect(mockGetBalance).not.toHaveBeenCalled();
  });
});
