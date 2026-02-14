import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../../App";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getAccounts: vi.fn(),
  getAuditLogs: vi.fn(),
  getMaintenanceStatus: vi.fn(),
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
});
