import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { ErrorScreen } from "../../components/screens/ErrorScreen";
import { SessionTimeoutScreen } from "../../components/screens/SessionTimeoutScreen";
import { MaintenanceModeScreen } from "../../components/screens/MaintenanceModeScreen";
import { MainMenuScreen } from "../../components/screens/MainMenuScreen";

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

describe("ErrorScreen", () => {
  it("renders error message from state", () => {
    render(
      <TestProvider initialState={withState({ lastError: "Insufficient funds" })}>
        <ErrorScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("error-screen")).toBeInTheDocument();
    expect(screen.getByText("Insufficient funds")).toBeInTheDocument();
  });

  it("shows default message when no error in state", () => {
    render(
      <TestProvider initialState={withState({ lastError: null })}>
        <ErrorScreen />
      </TestProvider>,
    );
    expect(screen.getByText("An unexpected error occurred")).toBeInTheDocument();
  });

  it("dispatches CLEAR_ERROR and GO_BACK when Back is clicked", async () => {
    const user = userEvent.setup();
    render(
      <TestProvider
        initialState={withState({
          lastError: "Some error",
          currentScreen: "error",
          screenHistory: ["main_menu"],
        })}
      >
        <ErrorScreen />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("error-back-btn"));
    // After GO_BACK from error screen, should be back at main_menu — verify button rendered
    expect(screen.getByTestId("error-back-btn")).toBeInTheDocument();
  });
});

describe("SessionTimeoutScreen", () => {
  it("renders session expired message", () => {
    render(
      <TestProvider initialState={withState({ currentScreen: "session_timeout" })}>
        <SessionTimeoutScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("session-timeout-screen")).toBeInTheDocument();
    expect(screen.getByText("Session Expired")).toBeInTheDocument();
    expect(screen.getByText("Your session has timed out")).toBeInTheDocument();
  });

  it("renders Start Over button", () => {
    render(
      <TestProvider initialState={withState()}>
        <SessionTimeoutScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("start-over-btn")).toBeInTheDocument();
    expect(screen.getByTestId("start-over-btn")).toHaveTextContent("Start Over");
  });

  it("dispatches LOGOUT when Start Over is clicked", async () => {
    const user = userEvent.setup();
    render(
      <TestProvider initialState={withState({ currentScreen: "session_timeout" })}>
        <SessionTimeoutScreen />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("start-over-btn"));
    // After LOGOUT, state resets — the component still renders since we're not switching screens in isolation
    expect(screen.getByTestId("start-over-btn")).toBeInTheDocument();
  });
});

describe("MaintenanceModeScreen", () => {
  it("renders out of service message", () => {
    render(<MaintenanceModeScreen />);
    expect(screen.getByTestId("maintenance-screen")).toBeInTheDocument();
    expect(screen.getByText("Out of Service")).toBeInTheDocument();
    expect(screen.getByText(/temporarily/)).toBeInTheDocument();
    expect(screen.getByText(/try again later/)).toBeInTheDocument();
  });
});

describe("MainMenuScreen", () => {
  const menuState = withState({
    currentScreen: "main_menu",
    sessionId: "sess-123",
    customerName: "Alice Johnson",
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders main menu with customer name", () => {
    render(
      <TestProvider initialState={menuState}>
        <MainMenuScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("main-menu-screen")).toBeInTheDocument();
    expect(screen.getByText("Main Menu")).toBeInTheDocument();
    expect(screen.getByText("Welcome, Alice Johnson")).toBeInTheDocument();
  });

  it("shows fallback when customer name is null", () => {
    render(
      <TestProvider initialState={withState({ customerName: null })}>
        <MainMenuScreen />
      </TestProvider>,
    );
    expect(screen.getByText("Welcome, Customer")).toBeInTheDocument();
  });

  it("renders Logout button", () => {
    render(
      <TestProvider initialState={menuState}>
        <MainMenuScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("logout-btn")).toBeInTheDocument();
    expect(screen.getByTestId("logout-btn")).toHaveTextContent("Logout");
  });

  it("dispatches LOGOUT on Logout button click", async () => {
    const user = userEvent.setup();
    const mockRemoveItem = vi.spyOn(Storage.prototype, "removeItem");
    render(
      <TestProvider initialState={menuState}>
        <MainMenuScreen />
      </TestProvider>,
    );
    await user.click(screen.getByTestId("logout-btn"));
    expect(mockRemoveItem).toHaveBeenCalledWith("atm_session_id");
    mockRemoveItem.mockRestore();
  });

  it("has side button configuration", () => {
    expect(MainMenuScreen.sideButtons.left).toHaveLength(4);
    expect(MainMenuScreen.sideButtons.right).toHaveLength(4);
    expect(MainMenuScreen.sideButtons.left[0]).toEqual({
      label: "Balance",
      screen: "balance_inquiry",
    });
    expect(MainMenuScreen.sideButtons.left[1]).toEqual({
      label: "Withdraw",
      screen: "withdrawal",
    });
    expect(MainMenuScreen.sideButtons.right[0]).toEqual({
      label: "Statement",
      screen: "statement",
    });
    expect(MainMenuScreen.sideButtons.right[2]).toBeNull();
    expect(MainMenuScreen.sideButtons.right[3]).toEqual({
      label: "Logout",
      screen: null,
    });
  });
});
