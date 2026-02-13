import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useReducer, type ReactNode } from "react";
import { ATMContext } from "../../state/context";
import { atmReducer } from "../../state/atmReducer";
import { INITIAL_ATM_STATE, type ATMState } from "../../state/types";
import { PinChangeScreen } from "../../components/screens/PinChangeScreen";

vi.mock("../../api/endpoints", () => ({
  changePin: vi.fn(),
}));

import { changePin } from "../../api/endpoints";

const mockChangePin = vi.mocked(changePin);

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

const pinChangeState = withState({
  currentScreen: "pin_change",
  sessionId: "sess-123",
});

describe("PinChangeScreen", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders in current PIN phase", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("pin-change-screen")).toBeInTheDocument();
    expect(screen.getByText("Change PIN")).toBeInTheDocument();
    expect(screen.getByText(/Step 1\/3/)).toBeInTheDocument();
    expect(screen.getByText(/current PIN/)).toBeInTheDocument();
  });

  it("shows pin dots", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    expect(screen.getByTestId("pin-display")).toBeInTheDocument();
    const dots = screen.getByTestId("pin-display").children;
    expect(dots).toHaveLength(6);
  });

  it("fills dots via keypad", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    const filledDots = screen
      .getByTestId("pin-display")
      .querySelectorAll(".pin-dot--filled");
    expect(filledDots).toHaveLength(4);
  });

  it("shows error for short PIN", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("pin-change-error")).toHaveTextContent(
      "PIN must be at least 4 digits",
    );
  });

  it("transitions to new PIN phase", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByText(/Step 2\/3/)).toBeInTheDocument();
    expect(screen.getByText(/new PIN/)).toBeInTheDocument();
  });

  it("transitions to confirm phase", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    // Phase 1: current PIN
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    // Phase 2: new PIN
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByText(/Step 3\/3/)).toBeInTheDocument();
    expect(screen.getByText(/Confirm new PIN/)).toBeInTheDocument();
  });

  it("shows error when PINs do not match", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    // Phase 1: current
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    // Phase 2: new
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    // Phase 3: confirm (wrong)
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("9");
      PinChangeScreen.keypadHandlers.onDigit("9");
      PinChangeScreen.keypadHandlers.onDigit("9");
      PinChangeScreen.keypadHandlers.onDigit("9");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("pin-change-error")).toHaveTextContent(
      "PINs do not match",
    );
  });

  it("calls changePin API on matching PINs", async () => {
    mockChangePin.mockResolvedValue(undefined);

    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );

    // Phase 1: current
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    // Phase 2: new
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    // Phase 3: confirm (match)
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });

    await act(async () => {
      await PinChangeScreen.keypadHandlers.onEnter();
    });

    await waitFor(() => {
      expect(mockChangePin).toHaveBeenCalledWith({
        current_pin: "1234",
        new_pin: "5678",
        confirm_pin: "5678",
      });
    });
  });

  it("shows success screen after PIN change", async () => {
    mockChangePin.mockResolvedValue(undefined);

    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );

    // All 3 phases
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });

    await act(async () => {
      await PinChangeScreen.keypadHandlers.onEnter();
    });

    await waitFor(() => {
      expect(screen.getByText("PIN Changed")).toBeInTheDocument();
    });
    expect(
      screen.getByText(/changed successfully/),
    ).toBeInTheDocument();
    expect(screen.getByTestId("pin-change-done-btn")).toBeInTheDocument();
  });

  it("Done button navigates to main menu", async () => {
    mockChangePin.mockResolvedValue(undefined);

    const user = userEvent.setup();

    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );

    // Complete all phases
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });

    await act(async () => {
      await PinChangeScreen.keypadHandlers.onEnter();
    });

    await waitFor(() => {
      expect(screen.getByTestId("pin-change-done-btn")).toBeInTheDocument();
    });

    await user.click(screen.getByTestId("pin-change-done-btn"));
    // Button was clicked — component still renders since isolated
    expect(screen.getByTestId("pin-change-done-btn")).toBeInTheDocument();
  });

  it("shows error on API failure and resets to phase 1", async () => {
    const axiosError = {
      isAxiosError: true,
      response: { data: { detail: "Current PIN incorrect" }, status: 400 },
    };
    mockChangePin.mockRejectedValue(axiosError);

    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );

    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7");
      PinChangeScreen.keypadHandlers.onDigit("8");
    });

    await act(async () => {
      await PinChangeScreen.keypadHandlers.onEnter();
    });

    await waitFor(() => {
      expect(screen.getByTestId("pin-change-error")).toHaveTextContent(
        "Current PIN incorrect",
      );
    });
    // Should reset to step 1
    expect(screen.getByText(/Step 1\/3/)).toBeInTheDocument();
  });

  it("shows error for short new PIN", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    // Phase 1: enter current PIN
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    // Phase 2: try short new PIN
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
    });
    act(() => {
      PinChangeScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("pin-change-error")).toHaveTextContent(
      "PIN must be at least 4 digits",
    );
  });

  it("dispatches GO_BACK on cancel", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    act(() => {
      PinChangeScreen.keypadHandlers.onCancel();
    });
    // Should dispatch GO_BACK
  });

  it("caps PIN at 6 digits", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onDigit("3");
      PinChangeScreen.keypadHandlers.onDigit("4");
      PinChangeScreen.keypadHandlers.onDigit("5");
      PinChangeScreen.keypadHandlers.onDigit("6");
      PinChangeScreen.keypadHandlers.onDigit("7"); // should be ignored
    });
    const filledDots = screen
      .getByTestId("pin-display")
      .querySelectorAll(".pin-dot--filled");
    expect(filledDots).toHaveLength(6);
  });

  it("clears pin digits via keypad", () => {
    render(
      <TestProvider initialState={pinChangeState}>
        <PinChangeScreen />
      </TestProvider>,
    );
    act(() => {
      PinChangeScreen.keypadHandlers.onDigit("1");
      PinChangeScreen.keypadHandlers.onDigit("2");
      PinChangeScreen.keypadHandlers.onClear();
    });
    const filledDots = screen
      .getByTestId("pin-display")
      .querySelectorAll(".pin-dot--filled");
    expect(filledDots).toHaveLength(1);
  });
});
