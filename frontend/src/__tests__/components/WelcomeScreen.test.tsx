import { describe, it, expect } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ATMProvider } from "../../state/ATMContext";
import { WelcomeScreen } from "../../components/screens/WelcomeScreen";

function renderWithProvider() {
  return render(
    <ATMProvider>
      <WelcomeScreen />
    </ATMProvider>,
  );
}

describe("WelcomeScreen", () => {
  it("renders welcome message and card input", () => {
    renderWithProvider();
    expect(screen.getByText("Welcome")).toBeInTheDocument();
    expect(screen.getByTestId("card-input")).toBeInTheDocument();
    expect(screen.getByTestId("insert-card-btn")).toBeInTheDocument();
  });

  it("shows error when submitting empty card number", async () => {
    const user = userEvent.setup();
    renderWithProvider();
    await user.click(screen.getByTestId("insert-card-btn"));
    expect(screen.getByTestId("welcome-error")).toHaveTextContent(
      "Please enter your card number",
    );
  });

  it("does not show error initially", () => {
    renderWithProvider();
    expect(screen.queryByTestId("welcome-error")).not.toBeInTheDocument();
  });

  it("accepts card number input", async () => {
    const user = userEvent.setup();
    renderWithProvider();
    const input = screen.getByTestId("card-input");
    await user.type(input, "1000-0001-0001");
    expect(input).toHaveValue("1000-0001-0001");
  });

  it("has a placeholder showing expected format", () => {
    renderWithProvider();
    expect(screen.getByTestId("card-input")).toHaveAttribute(
      "placeholder",
      "1000-0001-0001",
    );
  });

  it("handleDigit appends digit to card number", () => {
    renderWithProvider();
    act(() => {
      WelcomeScreen.keypadHandlers.onDigit("1");
      WelcomeScreen.keypadHandlers.onDigit("0");
      WelcomeScreen.keypadHandlers.onDigit("0");
      WelcomeScreen.keypadHandlers.onDigit("0");
    });
    const input = screen.getByTestId("card-input");
    expect((input as HTMLInputElement).value).toBe("1000");
  });

  it("handleClear removes last digit", () => {
    renderWithProvider();
    act(() => {
      WelcomeScreen.keypadHandlers.onDigit("1");
      WelcomeScreen.keypadHandlers.onDigit("2");
    });
    act(() => {
      WelcomeScreen.keypadHandlers.onClear();
    });
    const input = screen.getByTestId("card-input");
    expect((input as HTMLInputElement).value).toBe("1");
  });

  it("handleCancel clears card number", async () => {
    const user = userEvent.setup();
    renderWithProvider();
    const input = screen.getByTestId("card-input");
    await user.type(input, "1234");
    act(() => {
      WelcomeScreen.keypadHandlers.onCancel();
    });
    expect((input as HTMLInputElement).value).toBe("");
  });

  it("handleEnter shows error when empty", () => {
    renderWithProvider();
    act(() => {
      WelcomeScreen.keypadHandlers.onEnter();
    });
    expect(screen.getByTestId("welcome-error")).toHaveTextContent(
      "Please enter your card number",
    );
  });
});
