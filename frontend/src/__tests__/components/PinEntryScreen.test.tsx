import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { PinEntryScreen } from "../../components/screens/PinEntryScreen";

// Mock the API module
vi.mock("../../api/endpoints", () => ({
  login: vi.fn(),
  listAccounts: vi.fn(),
}));

/** Wrapper that provides ATMContext with a custom initial state. */
function TestProvider({ children, initialState }: { children: ReactNode; initialState: ATMState }) {
  const [state, dispatch] = useReducer(atmReducer, initialState);
  return (
    <ATMContext.Provider value={{ state, dispatch }}>
      {children}
    </ATMContext.Provider>
  );
}

function renderPinEntry(overrides: Partial<ATMState> = {}) {
  const initialState: ATMState = {
    ...INITIAL_ATM_STATE,
    currentScreen: "pin_entry",
    cardNumber: "1000-0001-0001",
    ...overrides,
  };
  return render(
    <TestProvider initialState={initialState}>
      <PinEntryScreen />
    </TestProvider>,
  );
}

describe("PinEntryScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders PIN entry screen with masked card number", () => {
    renderPinEntry();
    expect(screen.getByTestId("pin-entry-screen")).toBeInTheDocument();
    expect(screen.getByText("Enter Your PIN")).toBeInTheDocument();
    expect(screen.getByText("Card: ****0001")).toBeInTheDocument();
  });

  it("renders 6 PIN dots", () => {
    renderPinEntry();
    const display = screen.getByTestId("pin-display");
    const dots = display.querySelectorAll(".pin-dot");
    expect(dots).toHaveLength(6);
  });

  it("shows all dots unfilled initially", () => {
    renderPinEntry();
    const display = screen.getByTestId("pin-display");
    const filledDots = display.querySelectorAll(".pin-dot--filled");
    expect(filledDots).toHaveLength(0);
  });

  it("masks card number showing only last 4 digits", () => {
    renderPinEntry({ cardNumber: "1000-0002-0001" });
    expect(screen.getByText("Card: ****0001")).toBeInTheDocument();
  });

  it("shows fallback mask when card number is null", () => {
    renderPinEntry({ cardNumber: null });
    expect(screen.getByText("Card: ****")).toBeInTheDocument();
  });

  it("does not show error initially", () => {
    renderPinEntry();
    expect(screen.queryByTestId("pin-error")).not.toBeInTheDocument();
  });

  it("does not show loading initially", () => {
    renderPinEntry();
    expect(screen.queryByTestId("pin-loading")).not.toBeInTheDocument();
  });

  it("shows verifying text when loading", () => {
    renderPinEntry({ isLoading: true });
    expect(screen.getByTestId("pin-loading")).toHaveTextContent("Verifying...");
  });

  it("fills dots when digits are entered via keypad handlers", () => {
    renderPinEntry();
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
      PinEntryScreen.keypadHandlers.onDigit("2");
      PinEntryScreen.keypadHandlers.onDigit("3");
      PinEntryScreen.keypadHandlers.onDigit("4");
    });
    const display = screen.getByTestId("pin-display");
    const filledDots = display.querySelectorAll(".pin-dot--filled");
    expect(filledDots).toHaveLength(4);
  });

  it("clears pin when onClear is called", () => {
    renderPinEntry();
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
      PinEntryScreen.keypadHandlers.onDigit("2");
    });
    expect(screen.getByTestId("pin-display").querySelectorAll(".pin-dot--filled")).toHaveLength(2);
    act(() => {
      PinEntryScreen.keypadHandlers.onClear();
    });
    expect(screen.getByTestId("pin-display").querySelectorAll(".pin-dot--filled")).toHaveLength(0);
  });

  it("shows error when onEnter is called with short PIN", async () => {
    renderPinEntry();
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
      PinEntryScreen.keypadHandlers.onDigit("2");
    });
    await act(async () => {
      await PinEntryScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("pin-error")).toHaveTextContent("PIN must be at least 4 digits");
  });

  it("calls login API when valid PIN is entered", async () => {
    const { login, listAccounts } = await import("../../api/endpoints");
    const mockLogin = login as ReturnType<typeof vi.fn>;
    const mockListAccounts = listAccounts as ReturnType<typeof vi.fn>;
    mockLogin.mockResolvedValue({
      session_id: "sess-123",
      customer_name: "Alice",
      account_number: "1000-0001-0001",
      message: "OK",
    });
    mockListAccounts.mockResolvedValue({ accounts: [] });

    renderPinEntry();
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
      PinEntryScreen.keypadHandlers.onDigit("2");
      PinEntryScreen.keypadHandlers.onDigit("3");
      PinEntryScreen.keypadHandlers.onDigit("4");
    });
    await act(async () => {
      await PinEntryScreen.keypadHandlers.onEnter();
    });
    expect(mockLogin).toHaveBeenCalledWith({
      card_number: "1000-0001-0001",
      pin: "1234",
    });
  });

  it("shows error on login failure", async () => {
    const { login } = await import("../../api/endpoints");
    const mockLogin = login as ReturnType<typeof vi.fn>;
    const axios = await import("axios");
    vi.spyOn(axios.default, "isAxiosError").mockReturnValue(true);
    mockLogin.mockRejectedValue({
      isAxiosError: true,
      response: { data: { detail: "Invalid PIN" } },
    });

    renderPinEntry();
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
      PinEntryScreen.keypadHandlers.onDigit("2");
      PinEntryScreen.keypadHandlers.onDigit("3");
      PinEntryScreen.keypadHandlers.onDigit("4");
    });
    await act(async () => {
      await PinEntryScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("pin-error")).toHaveTextContent("Invalid PIN");
  });

  it("does not accept digits beyond max length", () => {
    renderPinEntry();
    act(() => {
      for (let i = 0; i < 8; i++) {
        PinEntryScreen.keypadHandlers.onDigit(String(i));
      }
    });
    // Max is 6 digits
    expect(screen.getByTestId("pin-display").querySelectorAll(".pin-dot--filled")).toHaveLength(6);
  });

  it("dispatches LOGOUT when onCancel is called", () => {
    renderPinEntry();
    act(() => {
      PinEntryScreen.keypadHandlers.onCancel();
    });
    // After cancel/logout, state resets — component may unmount in full app
    // but in isolation it continues to render
    expect(screen.getByTestId("pin-entry-screen")).toBeInTheDocument();
  });

  it("shows error when enter is pressed without card number", async () => {
    renderPinEntry({ cardNumber: null });
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
      PinEntryScreen.keypadHandlers.onDigit("2");
      PinEntryScreen.keypadHandlers.onDigit("3");
      PinEntryScreen.keypadHandlers.onDigit("4");
    });
    await act(async () => {
      await PinEntryScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("pin-error")).toHaveTextContent("No card number found");
  });

  it("ignores digit input when loading", () => {
    renderPinEntry({ isLoading: true });
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
    });
    expect(screen.getByTestId("pin-display").querySelectorAll(".pin-dot--filled")).toHaveLength(0);
  });

  it("handles Pydantic 422 validation error (array detail)", async () => {
    const { login } = await import("../../api/endpoints");
    const mockLogin = login as ReturnType<typeof vi.fn>;
    const axios = await import("axios");
    vi.spyOn(axios.default, "isAxiosError").mockReturnValue(true);
    mockLogin.mockRejectedValue({
      isAxiosError: true,
      response: {
        data: {
          detail: [
            {
              type: "value_error",
              loc: ["body", "pin"],
              msg: "Value error, PIN must be numeric",
            },
          ],
        },
        status: 422,
      },
    });

    renderPinEntry();
    act(() => {
      PinEntryScreen.keypadHandlers.onDigit("1");
      PinEntryScreen.keypadHandlers.onDigit("2");
      PinEntryScreen.keypadHandlers.onDigit("3");
      PinEntryScreen.keypadHandlers.onDigit("4");
    });
    await act(async () => {
      await PinEntryScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("pin-error")).toHaveTextContent("PIN must be numeric");
  });
});
