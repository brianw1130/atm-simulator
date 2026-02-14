import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CustomersPage } from "../../components/pages/CustomersPage";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getCustomers: vi.fn(),
  createCustomer: vi.fn(),
  deactivateCustomer: vi.fn(),
  activateCustomer: vi.fn(),
}));

const mockCustomers = [
  {
    id: 1,
    first_name: "Alice",
    last_name: "Johnson",
    email: "alice@example.com",
    phone: "555-0101",
    date_of_birth: "1990-05-15",
    is_active: true,
    account_count: 2,
  },
  {
    id: 2,
    first_name: "Bob",
    last_name: "Williams",
    email: "bob@example.com",
    phone: null,
    date_of_birth: "1985-03-20",
    is_active: false,
    account_count: 1,
  },
];

describe("CustomersPage", () => {
  const onNavigateToCustomer = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading spinner initially", () => {
    vi.mocked(api.getCustomers).mockReturnValue(new Promise(() => {}));
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("renders customer list", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Alice Johnson")).toBeInTheDocument();
    });
    expect(screen.getByText("Bob Williams")).toBeInTheDocument();
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    expect(screen.getByText("555-0101")).toBeInTheDocument();
  });

  it("shows dash for null phone", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("-")).toBeInTheDocument();
    });
  });

  it("navigates to customer detail on name click", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    const user = userEvent.setup();
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Alice Johnson")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Alice Johnson"));
    expect(onNavigateToCustomer).toHaveBeenCalledWith(1);
  });

  it("shows Create Customer button", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue([]);
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Create Customer")).toBeInTheDocument();
    });
  });

  it("opens create modal and submits", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue([]);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- test data is known
    vi.mocked(api.createCustomer).mockResolvedValue(mockCustomers[0]!);
    const user = userEvent.setup();

    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Create Customer")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Create Customer"));
    expect(screen.getByText("First Name")).toBeInTheDocument();
  });

  it("shows deactivate button for active customer", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Deactivate")).toBeInTheDocument();
    });
  });

  it("shows activate button for inactive customer", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Activate")).toBeInTheDocument();
    });
  });

  it("opens deactivate confirm dialog", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    const user = userEvent.setup();
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Deactivate")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Deactivate"));

    expect(
      screen.getByText(
        "Are you sure you want to deactivate Alice Johnson?",
      ),
    ).toBeInTheDocument();
  });

  it("opens activate confirm dialog", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    const user = userEvent.setup();
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Activate")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Activate"));

    expect(
      screen.getByText(
        "Are you sure you want to activate Bob Williams?",
      ),
    ).toBeInTheDocument();
  });

  it("completes create customer flow", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue([]);
    vi.mocked(api.createCustomer).mockResolvedValue(mockCustomers[0] as typeof mockCustomers[0]);
    const user = userEvent.setup();

    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Create Customer")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Create Customer"));
    await user.type(screen.getByLabelText("First Name"), "Alice");
    await user.type(screen.getByLabelText("Last Name"), "Johnson");
    await user.type(screen.getByLabelText("Email"), "alice@example.com");
    await user.type(screen.getByLabelText("Date of Birth"), "1990-05-15");
    await user.click(screen.getByRole("button", { name: "Create" }));

    await waitFor(() => {
      expect(api.createCustomer).toHaveBeenCalled();
    });
  });

  it("completes deactivate customer flow", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    vi.mocked(api.deactivateCustomer).mockResolvedValue({ message: "ok" });
    const user = userEvent.setup();

    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Deactivate")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Deactivate"));

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByText("Deactivate"));

    await waitFor(() => {
      expect(api.deactivateCustomer).toHaveBeenCalledWith(1);
    });
  });

  it("completes activate customer flow", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    vi.mocked(api.activateCustomer).mockResolvedValue({ message: "ok" });
    const user = userEvent.setup();

    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Activate")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Activate"));

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByText("Activate"));

    await waitFor(() => {
      expect(api.activateCustomer).toHaveBeenCalledWith(2);
    });
  });

  it("shows notification on deactivate failure", async () => {
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    vi.mocked(api.deactivateCustomer).mockRejectedValue(new Error("fail"));
    const user = userEvent.setup();

    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText("Deactivate")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Deactivate"));

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByText("Deactivate"));

    await waitFor(() => {
      expect(
        screen.getByText("Failed to deactivate customer"),
      ).toBeInTheDocument();
    });
  });

  it("shows error state", async () => {
    vi.mocked(api.getCustomers).mockRejectedValue(new Error("Network error"));
    render(<CustomersPage onNavigateToCustomer={onNavigateToCustomer} />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });
});
