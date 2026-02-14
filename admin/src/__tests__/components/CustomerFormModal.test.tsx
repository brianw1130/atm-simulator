import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CustomerFormModal } from "../../components/shared/CustomerFormModal";

describe("CustomerFormModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSubmit: vi.fn().mockResolvedValue(undefined),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders create mode title", () => {
    render(<CustomerFormModal {...defaultProps} />);
    expect(screen.getByText("Create Customer")).toBeInTheDocument();
  });

  it("renders edit mode title with pre-filled fields", () => {
    const customer = {
      id: 1,
      first_name: "Alice",
      last_name: "Johnson",
      email: "alice@example.com",
      phone: "555-0101",
      date_of_birth: "1990-05-15",
      is_active: true,
      account_count: 2,
    };
    render(<CustomerFormModal {...defaultProps} customer={customer} />);
    expect(screen.getByText("Edit Customer")).toBeInTheDocument();
    expect(screen.getByLabelText("First Name")).toHaveValue("Alice");
    expect(screen.getByLabelText("Last Name")).toHaveValue("Johnson");
    expect(screen.getByLabelText("Email")).toHaveValue("alice@example.com");
    expect(screen.getByLabelText("Phone (optional)")).toHaveValue("555-0101");
    expect(screen.getByLabelText("Date of Birth")).toHaveValue("1990-05-15");
  });

  it("disables submit when required fields are empty", () => {
    render(<CustomerFormModal {...defaultProps} />);
    expect(screen.getByText("Create")).toBeDisabled();
  });

  it("submits form data in create mode", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <CustomerFormModal
        {...defaultProps}
        onSubmit={onSubmit}
        onClose={onClose}
      />,
    );

    await user.type(screen.getByLabelText("First Name"), "Bob");
    await user.type(screen.getByLabelText("Last Name"), "Smith");
    await user.type(screen.getByLabelText("Email"), "bob@test.com");
    await user.type(screen.getByLabelText("Date of Birth"), "1985-03-20");
    await user.click(screen.getByText("Create"));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        first_name: "Bob",
        last_name: "Smith",
        email: "bob@test.com",
        date_of_birth: "1985-03-20",
      });
    });
    expect(onClose).toHaveBeenCalled();
  });

  it("shows error on submit failure", async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error("Duplicate email"));
    const user = userEvent.setup();

    render(<CustomerFormModal {...defaultProps} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("First Name"), "Bob");
    await user.type(screen.getByLabelText("Last Name"), "Smith");
    await user.type(screen.getByLabelText("Email"), "bob@test.com");
    await user.type(screen.getByLabelText("Date of Birth"), "1985-03-20");
    await user.click(screen.getByText("Create"));

    await waitFor(() => {
      expect(screen.getByText("Duplicate email")).toBeInTheDocument();
    });
  });

  it("includes phone when provided", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<CustomerFormModal {...defaultProps} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("First Name"), "Bob");
    await user.type(screen.getByLabelText("Last Name"), "Smith");
    await user.type(screen.getByLabelText("Email"), "bob@test.com");
    await user.type(screen.getByLabelText("Phone (optional)"), "555-1234");
    await user.type(screen.getByLabelText("Date of Birth"), "1985-03-20");
    await user.click(screen.getByText("Create"));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({ phone: "555-1234" }),
      );
    });
  });
});
