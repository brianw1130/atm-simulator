import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../../App";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getAccounts: vi.fn(),
  getDashboardStats: vi.fn(),
  getAuditLogs: vi.fn(),
  getMaintenanceStatus: vi.fn(),
  getCustomers: vi.fn(),
  getCustomerDetail: vi.fn(),
  freezeAccount: vi.fn(),
  unfreezeAccount: vi.fn(),
  closeAccount: vi.fn(),
  exportSnapshot: vi.fn(),
  importSnapshot: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it("shows loading spinner initially", () => {
    vi.mocked(api.getAccounts).mockReturnValue(new Promise(() => {}));
    render(<App />);
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("shows login page when unauthenticated", async () => {
    vi.mocked(api.getAccounts).mockRejectedValue(new Error("401"));
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("ATM Admin")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("Username")).toBeInTheDocument();
  });

  it("shows dashboard when authenticated", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    vi.mocked(api.getDashboardStats).mockResolvedValue({
      total_customers: 3,
      active_customers: 3,
      total_accounts: 5,
      active_accounts: 4,
      frozen_accounts: 1,
      closed_accounts: 0,
      total_balance_formatted: "$18,600.75",
    });
    vi.mocked(api.getAuditLogs).mockResolvedValue([]);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    sessionStorage.setItem("admin_username", "admin");
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Total Accounts")).toBeInTheDocument();
    });
  });

  it("navigates between pages", async () => {
    const user = userEvent.setup();
    const mockAccountData = [
      {
        id: 1,
        account_number: "1000-0001-0001",
        account_type: "CHECKING" as const,
        balance: "5250.00",
        available_balance: "5250.00",
        status: "ACTIVE" as const,
        customer_name: "Alice",
      },
    ];
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccountData);
    vi.mocked(api.getDashboardStats).mockResolvedValue({
      total_customers: 3,
      active_customers: 3,
      total_accounts: 5,
      active_accounts: 4,
      frozen_accounts: 1,
      closed_accounts: 0,
      total_balance_formatted: "$18,600.75",
    });
    vi.mocked(api.getAuditLogs).mockResolvedValue([]);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    sessionStorage.setItem("admin_username", "admin");
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Total Accounts")).toBeInTheDocument();
    });

    // Navigate to Accounts page
    await user.click(screen.getByRole("button", { name: /Accounts/ }));
    await waitFor(() => {
      expect(screen.getByText("Alice")).toBeInTheDocument();
    });
  });

  it("logs out and returns to login", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    vi.mocked(api.getDashboardStats).mockResolvedValue({
      total_customers: 0,
      active_customers: 0,
      total_accounts: 0,
      active_accounts: 0,
      frozen_accounts: 0,
      closed_accounts: 0,
      total_balance_formatted: "$0.00",
    });
    vi.mocked(api.getAuditLogs).mockResolvedValue([]);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    vi.mocked(api.logout).mockResolvedValue({ message: "ok" });
    sessionStorage.setItem("admin_username", "admin");
    render(<App />);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Logout" }),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Logout" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Username")).toBeInTheDocument();
    });
  });

  it("navigates to Customers page", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    vi.mocked(api.getDashboardStats).mockResolvedValue({
      total_customers: 0,
      active_customers: 0,
      total_accounts: 0,
      active_accounts: 0,
      frozen_accounts: 0,
      closed_accounts: 0,
      total_balance_formatted: "$0.00",
    });
    vi.mocked(api.getAuditLogs).mockResolvedValue([]);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    vi.mocked(api.getCustomers).mockResolvedValue([]);
    sessionStorage.setItem("admin_username", "admin");
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("Total Accounts")).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /Customers/ }));
    await waitFor(() => {
      expect(screen.getByText("Create Customer")).toBeInTheDocument();
    });
  });

  it("navigates to customer detail and back", async () => {
    const user = userEvent.setup();
    const mockCustomers = [
      {
        id: 1,
        first_name: "Alice",
        last_name: "Johnson",
        email: "alice@example.com",
        phone: null,
        date_of_birth: "1990-05-15",
        is_active: true,
        account_count: 1,
      },
    ];
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    vi.mocked(api.getDashboardStats).mockResolvedValue({
      total_customers: 1,
      active_customers: 1,
      total_accounts: 1,
      active_accounts: 1,
      frozen_accounts: 0,
      closed_accounts: 0,
      total_balance_formatted: "$5,250.00",
    });
    vi.mocked(api.getAuditLogs).mockResolvedValue([]);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    vi.mocked(api.getCustomers).mockResolvedValue(mockCustomers);
    vi.mocked(api.getCustomerDetail).mockResolvedValue({
      id: 1,
      first_name: "Alice",
      last_name: "Johnson",
      email: "alice@example.com",
      phone: null,
      date_of_birth: "1990-05-15",
      is_active: true,
      account_count: 1,
      accounts: [],
    });
    sessionStorage.setItem("admin_username", "admin");
    render(<App />);

    // Navigate to customers
    await waitFor(() => {
      expect(screen.getByText("Total Accounts")).toBeInTheDocument();
    });
    await user.click(screen.getByRole("button", { name: /Customers/ }));

    // Click customer name to go to detail
    await waitFor(() => {
      expect(screen.getByText("Alice Johnson")).toBeInTheDocument();
    });
    await user.click(screen.getByText("Alice Johnson"));

    // Verify detail page
    await waitFor(() => {
      expect(screen.getByText("Email: alice@example.com")).toBeInTheDocument();
    });
  });
});
