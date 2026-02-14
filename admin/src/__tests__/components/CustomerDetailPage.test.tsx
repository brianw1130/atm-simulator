import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CustomerDetailPage } from "../../components/pages/CustomerDetailPage";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getCustomerDetail: vi.fn(),
  updateCustomer: vi.fn(),
  createAccount: vi.fn(),
  resetPin: vi.fn(),
  closeAccount: vi.fn(),
  freezeAccount: vi.fn(),
  unfreezeAccount: vi.fn(),
}));

const mockDetail = {
  id: 1,
  first_name: "Alice",
  last_name: "Johnson",
  email: "alice@example.com",
  phone: "555-0101",
  date_of_birth: "1990-05-15",
  is_active: true,
  account_count: 2,
  accounts: [
    {
      id: 10,
      account_number: "1000-0001-0001",
      account_type: "CHECKING" as const,
      balance: "$5,250.00",
      available_balance: "$5,250.00",
      status: "ACTIVE" as const,
      cards: [
        {
          id: 100,
          card_number: "1000-0001-0001",
          is_active: true,
          failed_attempts: 0,
          is_locked: false,
        },
      ],
    },
    {
      id: 11,
      account_number: "1000-0001-0002",
      account_type: "SAVINGS" as const,
      balance: "$12,500.00",
      available_balance: "$12,500.00",
      status: "FROZEN" as const,
      cards: [],
    },
  ],
};

describe("CustomerDetailPage", () => {
  const onBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading spinner initially", () => {
    vi.mocked(api.getCustomerDetail).mockReturnValue(new Promise(() => {}));
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("renders customer info", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Alice Johnson" }),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("Email: alice@example.com")).toBeInTheDocument();
    expect(screen.getByText("Phone: 555-0101")).toBeInTheDocument();
    expect(
      screen.getByText("Date of Birth: 1990-05-15"),
    ).toBeInTheDocument();
  });

  it("renders breadcrumb with back navigation", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Customers")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Customers"));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("renders accounts table", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Accounts (2)")).toBeInTheDocument();
    });
    expect(screen.getAllByText("1000-0001-0001").length).toBeGreaterThanOrEqual(
      1,
    );
    expect(screen.getByText("1000-0001-0002")).toBeInTheDocument();
  });

  it("shows freeze button for active account", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Freeze")).toBeInTheDocument();
    });
  });

  it("shows unfreeze button for frozen account", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Unfreeze")).toBeInTheDocument();
    });
  });

  it("shows close button for active account", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Close")).toBeInTheDocument();
    });
  });

  it("opens close account confirm dialog", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Close")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Close"));

    expect(
      screen.getByText(
        "Are you sure you want to close account 1000-0001-0001? Balance must be zero.",
      ),
    ).toBeInTheDocument();
  });

  it("shows Reset PIN button for cards", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Reset PIN")).toBeInTheDocument();
    });
  });

  it("opens PIN reset modal", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Reset PIN")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Reset PIN"));

    expect(screen.getByText("Card: 1000-0001-0001")).toBeInTheDocument();
  });

  it("shows Edit Customer button", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Edit Customer")).toBeInTheDocument();
    });
  });

  it("shows Add Account button", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Add Account")).toBeInTheDocument();
    });
  });

  it("opens edit modal with pre-filled data", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Edit Customer")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Edit Customer"));

    expect(screen.getByLabelText("First Name")).toHaveValue("Alice");
  });

  it("completes edit customer flow", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.updateCustomer).mockResolvedValue(mockDetail);
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Edit Customer")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Edit Customer"));
    await user.click(screen.getByRole("button", { name: "Update" }));

    await waitFor(() => {
      expect(api.updateCustomer).toHaveBeenCalledWith(1, expect.any(Object));
    });
  });

  it("opens add account modal", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Add Account")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Add Account"));

    expect(screen.getByLabelText("Account Type")).toBeInTheDocument();
  });

  it("completes create account flow", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.createAccount).mockResolvedValue({
      id: 12,
      account_number: "1000-0001-0003",
      account_type: "CHECKING",
      balance: "$0.00",
      available_balance: "$0.00",
      status: "ACTIVE",
      cards: [],
    });
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Add Account")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Add Account"));
    await user.click(screen.getByRole("button", { name: "Create Account" }));

    await waitFor(() => {
      expect(api.createAccount).toHaveBeenCalledWith(1, expect.any(Object));
    });
  });

  it("completes freeze account flow", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.freezeAccount).mockResolvedValue({ message: "Frozen" });
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Freeze")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Freeze"));

    await waitFor(() => {
      expect(api.freezeAccount).toHaveBeenCalledWith(10);
    });
  });

  it("completes unfreeze account flow", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.unfreezeAccount).mockResolvedValue({ message: "Unfrozen" });
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Unfreeze")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Unfreeze"));

    await waitFor(() => {
      expect(api.unfreezeAccount).toHaveBeenCalledWith(11);
    });
  });

  it("completes close account flow", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.closeAccount).mockResolvedValue({ message: "Closed" });
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Close")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Close"));

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Close Account" }));

    await waitFor(() => {
      expect(api.closeAccount).toHaveBeenCalledWith(10);
    });
  });

  it("shows error on close account failure", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.closeAccount).mockRejectedValue(new Error("Balance not zero"));
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Close")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Close"));

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Close Account" }));

    await waitFor(() => {
      expect(
        screen.getByText("Failed to close account. Balance must be zero."),
      ).toBeInTheDocument();
    });
  });

  it("completes PIN reset flow", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.resetPin).mockResolvedValue({ message: "PIN reset" });
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Reset PIN")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Reset PIN"));

    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText("New PIN"), "4826");
    await user.type(within(dialog).getByLabelText("Confirm PIN"), "4826");
    await user.click(within(dialog).getByRole("button", { name: /Reset PIN/ }));

    await waitFor(() => {
      expect(api.resetPin).toHaveBeenCalledWith(100, "4826");
    });
  });

  it("shows error on freeze failure", async () => {
    vi.mocked(api.getCustomerDetail).mockResolvedValue(mockDetail);
    vi.mocked(api.freezeAccount).mockRejectedValue(new Error("fail"));
    const user = userEvent.setup();
    render(<CustomerDetailPage customerId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Freeze")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Freeze"));

    await waitFor(() => {
      expect(
        screen.getByText("Failed to freeze account"),
      ).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    vi.mocked(api.getCustomerDetail).mockRejectedValue(
      new Error("Not found"),
    );
    render(<CustomerDetailPage customerId={999} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });
});
