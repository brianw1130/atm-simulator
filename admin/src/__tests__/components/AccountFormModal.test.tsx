import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AccountFormModal } from "../../components/shared/AccountFormModal";

describe("AccountFormModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn().mockResolvedValue(undefined),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders form fields", () => {
    render(<AccountFormModal {...defaultProps} />);
    expect(screen.getByLabelText("Account Type")).toBeInTheDocument();
    expect(screen.getByLabelText("Initial Balance ($)")).toBeInTheDocument();
  });

  it("defaults to CHECKING type", () => {
    render(<AccountFormModal {...defaultProps} />);
    expect(screen.getByLabelText("Account Type")).toHaveValue("CHECKING");
  });

  it("submits with CHECKING and zero balance by default", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <AccountFormModal
        {...defaultProps}
        onSubmit={onSubmit}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        account_type: "CHECKING",
        initial_balance_cents: 0,
      });
    });
    expect(onClose).toHaveBeenCalled();
  });

  it("submits with SAVINGS and converted balance", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<AccountFormModal {...defaultProps} onSubmit={onSubmit} />);

    await user.selectOptions(screen.getByLabelText("Account Type"), "SAVINGS");
    await user.type(screen.getByLabelText("Initial Balance ($)"), "100.50");
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        account_type: "SAVINGS",
        initial_balance_cents: 10050,
      });
    });
  });

  it("shows error on submit failure", async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error("Creation failed"));
    const user = userEvent.setup();

    render(<AccountFormModal {...defaultProps} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(screen.getByText("Creation failed")).toBeInTheDocument();
    });
  });

  it("renders nothing when not open", () => {
    const { container } = render(
      <AccountFormModal {...defaultProps} isOpen={false} />,
    );
    expect(container.innerHTML).toBe("");
  });
});
