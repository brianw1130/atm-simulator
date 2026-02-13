import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { StatementScreen } from "../../components/screens/StatementScreen";

vi.mock("../../api/endpoints", () => ({
  generateStatement: vi.fn(),
}));

import { generateStatement } from "../../api/endpoints";

const mockGenerateStatement = vi.mocked(generateStatement);

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

const statementState = withState({
  currentScreen: "statement",
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

describe("StatementScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders statement screen with period selection", () => {
    render(
      <TestProvider initialState={statementState}>
        <StatementScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("statement-screen")).toBeInTheDocument();
    expect(screen.getByText("Account Statement")).toBeInTheDocument();
    expect(screen.getByText(/side buttons/)).toBeInTheDocument();
  });

  it("shows account info", () => {
    render(
      <TestProvider initialState={statementState}>
        <StatementScreen />
      </TestProvider>,
    );
    expect(screen.getByText(/CHECKING/)).toBeInTheDocument();
  });

  it("generates statement on handleGenerate call", async () => {
    mockGenerateStatement.mockResolvedValue({
      file_path: "/app/statements/stmt_2024.pdf",
      period: "Jan 1 - Jan 7, 2024",
      transaction_count: 5,
      opening_balance: "$5,000.00",
      closing_balance: "$5,250.00",
    });

    render(
      <TestProvider initialState={statementState}>
        <StatementScreen />
      </TestProvider>,
    );

    await act(async () => {
      await StatementScreen.handleGenerate(7);
    });

    await waitFor(() => {
      expect(mockGenerateStatement).toHaveBeenCalledWith({ days: 7 });
    });
  });

  it("shows result after generation", async () => {
    mockGenerateStatement.mockResolvedValue({
      file_path: "/app/statements/stmt_2024.pdf",
      period: "Jan 1 - Jan 7, 2024",
      transaction_count: 5,
      opening_balance: "$5,000.00",
      closing_balance: "$5,250.00",
    });

    render(
      <TestProvider initialState={statementState}>
        <StatementScreen />
      </TestProvider>,
    );

    await act(async () => {
      await StatementScreen.handleGenerate(7);
    });

    await waitFor(() => {
      expect(screen.getByText("Statement Ready")).toBeInTheDocument();
    });
    expect(screen.getByText("Jan 1 - Jan 7, 2024")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("$5,000.00")).toBeInTheDocument();
    expect(screen.getByText("$5,250.00")).toBeInTheDocument();
  });

  it("shows download button after generation", async () => {
    mockGenerateStatement.mockResolvedValue({
      file_path: "/app/statements/stmt_2024.pdf",
      period: "Jan 1 - Jan 7, 2024",
      transaction_count: 5,
      opening_balance: "$5,000.00",
      closing_balance: "$5,250.00",
    });

    render(
      <TestProvider initialState={statementState}>
        <StatementScreen />
      </TestProvider>,
    );

    await act(async () => {
      await StatementScreen.handleGenerate(7);
    });

    await waitFor(() => {
      expect(screen.getByTestId("download-btn")).toBeInTheDocument();
    });
  });

  it("opens download URL on download click", async () => {
    const windowOpen = vi.spyOn(window, "open").mockImplementation(() => null);

    mockGenerateStatement.mockResolvedValue({
      file_path: "/app/statements/stmt_2024.pdf",
      period: "Jan 1 - Jan 7, 2024",
      transaction_count: 5,
      opening_balance: "$5,000.00",
      closing_balance: "$5,250.00",
    });

    const user = userEvent.setup();

    render(
      <TestProvider initialState={statementState}>
        <StatementScreen />
      </TestProvider>,
    );

    await act(async () => {
      await StatementScreen.handleGenerate(7);
    });

    await waitFor(() => {
      expect(screen.getByTestId("download-btn")).toBeInTheDocument();
    });

    await user.click(screen.getByTestId("download-btn"));
    expect(windowOpen).toHaveBeenCalledWith(
      "/api/v1/statements/download/stmt_2024.pdf",
      "_blank",
    );

    windowOpen.mockRestore();
  });

  it("shows error on generation failure", async () => {
    mockGenerateStatement.mockRejectedValue(new Error("Server error"));

    render(
      <TestProvider initialState={statementState}>
        <StatementScreen />
      </TestProvider>,
    );

    await act(async () => {
      await StatementScreen.handleGenerate(7);
    });

    await waitFor(() => {
      expect(screen.getByTestId("statement-error")).toHaveTextContent(
        "Failed to generate statement",
      );
    });
  });
});
