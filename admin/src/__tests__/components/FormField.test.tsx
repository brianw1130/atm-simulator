import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FormField } from "../../components/shared/FormField";

describe("FormField", () => {
  it("renders label and input", () => {
    render(<FormField id="name" label="Name" />);
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
  });

  it("shows error message when provided", () => {
    render(<FormField id="email" label="Email" error="Invalid email" />);
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
  });

  it("applies error class when error exists", () => {
    render(<FormField id="test" label="Test" error="Error" />);
    expect(screen.getByLabelText("Test").className).toContain(
      "form-input--error",
    );
  });

  it("does not show error class without error", () => {
    render(<FormField id="test" label="Test" />);
    expect(screen.getByLabelText("Test").className).not.toContain(
      "form-input--error",
    );
  });

  it("passes through input attributes", () => {
    render(
      <FormField
        id="pin"
        label="PIN"
        type="password"
        maxLength={6}
        disabled
      />,
    );
    const input = screen.getByLabelText("PIN");
    expect(input).toHaveAttribute("type", "password");
    expect(input).toHaveAttribute("maxlength", "6");
    expect(input).toBeDisabled();
  });

  it("handles onChange events", () => {
    const onChange = vi.fn();
    render(<FormField id="test" label="Test" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Test"), {
      target: { value: "hello" },
    });
    expect(onChange).toHaveBeenCalled();
  });
});
