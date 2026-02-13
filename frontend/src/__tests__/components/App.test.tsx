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

  it("disables keypad on welcome screen", () => {
    renderApp();
    expect(screen.getByTestId("key-0")).toBeDisabled();
    expect(screen.getByTestId("key-enter")).toBeDisabled();
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
      expect(screen.getByTestId("placeholder-screen")).toBeInTheDocument();
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

  it("renders placeholder for unimplemented screens", () => {
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
    expect(screen.getByTestId("placeholder-screen")).toBeInTheDocument();
    expect(screen.getByText("Coming in Sprint 2")).toBeInTheDocument();
  });
});
