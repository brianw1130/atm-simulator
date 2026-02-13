import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NumericKeypad } from "../../components/atm-housing/NumericKeypad";

describe("NumericKeypad", () => {
  const defaultProps = {
    onDigit: vi.fn(),
    onClear: vi.fn(),
    onCancel: vi.fn(),
    onEnter: vi.fn(),
  };

  it("renders all 10 digit buttons", () => {
    render(<NumericKeypad {...defaultProps} />);
    for (let i = 0; i <= 9; i++) {
      expect(screen.getByTestId(`key-${i}`)).toBeInTheDocument();
    }
  });

  it("renders function keys (Cancel, Clear, Enter)", () => {
    render(<NumericKeypad {...defaultProps} />);
    expect(screen.getByTestId("key-cancel")).toBeInTheDocument();
    expect(screen.getByTestId("key-clear")).toBeInTheDocument();
    expect(screen.getByTestId("key-enter")).toBeInTheDocument();
  });

  it("calls onDigit when a number button is clicked", async () => {
    const onDigit = vi.fn();
    const user = userEvent.setup();
    render(<NumericKeypad {...defaultProps} onDigit={onDigit} />);
    await user.click(screen.getByTestId("key-5"));
    expect(onDigit).toHaveBeenCalledWith("5");
  });

  it("calls onEnter when Enter button is clicked", async () => {
    const onEnter = vi.fn();
    const user = userEvent.setup();
    render(<NumericKeypad {...defaultProps} onEnter={onEnter} />);
    await user.click(screen.getByTestId("key-enter"));
    expect(onEnter).toHaveBeenCalledOnce();
  });

  it("calls onClear when Clear button is clicked", async () => {
    const onClear = vi.fn();
    const user = userEvent.setup();
    render(<NumericKeypad {...defaultProps} onClear={onClear} />);
    await user.click(screen.getByTestId("key-clear"));
    expect(onClear).toHaveBeenCalledOnce();
  });

  it("calls onCancel when Cancel button is clicked", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    render(<NumericKeypad {...defaultProps} onCancel={onCancel} />);
    await user.click(screen.getByTestId("key-cancel"));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("disables all buttons when disabled prop is true", () => {
    render(<NumericKeypad {...defaultProps} disabled={true} />);
    for (let i = 0; i <= 9; i++) {
      expect(screen.getByTestId(`key-${i}`)).toBeDisabled();
    }
    expect(screen.getByTestId("key-cancel")).toBeDisabled();
    expect(screen.getByTestId("key-clear")).toBeDisabled();
    expect(screen.getByTestId("key-enter")).toBeDisabled();
  });

  it("maps physical keyboard digits to onDigit", () => {
    const onDigit = vi.fn();
    render(<NumericKeypad {...defaultProps} onDigit={onDigit} />);
    fireEvent.keyDown(window, { key: "7" });
    expect(onDigit).toHaveBeenCalledWith("7");
  });

  it("maps physical Enter key to onEnter", () => {
    const onEnter = vi.fn();
    render(<NumericKeypad {...defaultProps} onEnter={onEnter} />);
    fireEvent.keyDown(window, { key: "Enter" });
    expect(onEnter).toHaveBeenCalledOnce();
  });

  it("maps physical Escape key to onCancel", () => {
    const onCancel = vi.fn();
    render(<NumericKeypad {...defaultProps} onCancel={onCancel} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("maps physical Backspace key to onClear", () => {
    const onClear = vi.fn();
    render(<NumericKeypad {...defaultProps} onClear={onClear} />);
    fireEvent.keyDown(window, { key: "Backspace" });
    expect(onClear).toHaveBeenCalledOnce();
  });

  it("ignores keyboard events when disabled", () => {
    const onDigit = vi.fn();
    render(<NumericKeypad {...defaultProps} onDigit={onDigit} disabled={true} />);
    fireEvent.keyDown(window, { key: "5" });
    expect(onDigit).not.toHaveBeenCalled();
  });
});
