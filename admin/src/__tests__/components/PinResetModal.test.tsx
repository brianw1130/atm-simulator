import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PinResetModal } from "../../components/shared/PinResetModal";

describe("PinResetModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn().mockResolvedValue(undefined),
    cardNumber: "1000-0001-0001",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when not open", () => {
    const { container } = render(
      <PinResetModal {...defaultProps} isOpen={false} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("shows card number", () => {
    render(<PinResetModal {...defaultProps} />);
    expect(screen.getByText("Card: 1000-0001-0001")).toBeInTheDocument();
  });

  it("renders PIN input fields", () => {
    render(<PinResetModal {...defaultProps} />);
    expect(screen.getByLabelText("New PIN")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm PIN")).toBeInTheDocument();
  });

  it("disables submit when PINs are empty", () => {
    render(<PinResetModal {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: "Reset PIN" }),
    ).toBeDisabled();
  });

  it("shows mismatch error when PINs differ", async () => {
    const user = userEvent.setup();
    render(<PinResetModal {...defaultProps} />);

    await user.type(screen.getByLabelText("New PIN"), "4826");
    await user.type(screen.getByLabelText("Confirm PIN"), "9999");

    expect(screen.getByText("PINs do not match")).toBeInTheDocument();
  });

  it("shows complexity error for repeated digits", async () => {
    const user = userEvent.setup();
    render(<PinResetModal {...defaultProps} />);

    await user.type(screen.getByLabelText("New PIN"), "1111");

    expect(
      screen.getByText("PIN cannot be all the same digit"),
    ).toBeInTheDocument();
  });

  it("shows complexity error for sequential digits", async () => {
    const user = userEvent.setup();
    render(<PinResetModal {...defaultProps} />);

    await user.type(screen.getByLabelText("New PIN"), "1234");

    expect(
      screen.getByText("PIN cannot be sequential digits"),
    ).toBeInTheDocument();
  });

  it("submits valid PIN and closes", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <PinResetModal {...defaultProps} onSubmit={onSubmit} onClose={onClose} />,
    );

    await user.type(screen.getByLabelText("New PIN"), "4826");
    await user.type(screen.getByLabelText("Confirm PIN"), "4826");
    await user.click(screen.getByRole("button", { name: "Reset PIN" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith("4826");
    });
    expect(onClose).toHaveBeenCalled();
  });

  it("shows error on submit failure", async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error("Server error"));
    const user = userEvent.setup();

    render(<PinResetModal {...defaultProps} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("New PIN"), "4826");
    await user.type(screen.getByLabelText("Confirm PIN"), "4826");
    await user.click(screen.getByRole("button", { name: "Reset PIN" }));

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });

  it("calls onClose when Cancel is clicked", () => {
    render(<PinResetModal {...defaultProps} />);
    fireEvent.click(screen.getByText("Cancel"));
    expect(defaultProps.onClose).toHaveBeenCalled();
  });
});
