import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { DashboardPage } from "../../components/pages/DashboardPage";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getAccounts: vi.fn(),
  getAuditLogs: vi.fn(),
  getMaintenanceStatus: vi.fn(),
}));

const mockAccounts = [
  {
    id: 1,
    account_number: "1000-0001-0001",
    account_type: "CHECKING" as const,
    balance: "5250.00",
    available_balance: "5250.00",
    status: "ACTIVE" as const,
    customer_name: "Alice Johnson",
  },
  {
    id: 2,
    account_number: "1000-0002-0001",
    account_type: "CHECKING" as const,
    balance: "850.75",
    available_balance: "850.75",
    status: "FROZEN" as const,
    customer_name: "Bob Williams",
  },
];

const mockLogs = [
  {
    id: 10,
    event_type: "AUTH_SUCCESS",
    account_id: 5,
    ip_address: "127.0.0.1",
    session_id: "abc",
    details: {},
    created_at: "2026-02-13T12:00:00Z",
  },
];

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading spinner while fetching", () => {
    vi.mocked(api.getAccounts).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getAuditLogs).mockReturnValue(new Promise(() => {}));
    vi.mocked(api.getMaintenanceStatus).mockReturnValue(new Promise(() => {}));
    render(<DashboardPage />);
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });

  it("renders stats cards with correct data", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    vi.mocked(api.getAuditLogs).mockResolvedValue(mockLogs);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Total Accounts")).toBeInTheDocument();
    });

    // 2 total accounts, 1 active, 1 frozen
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("OFF")).toBeInTheDocument();
  });

  it("renders recent activity table", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    vi.mocked(api.getAuditLogs).mockResolvedValue(mockLogs);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    });

    expect(screen.getByText("AUTH_SUCCESS")).toBeInTheDocument();
  });

  it("shows maintenance ON badge when enabled", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    vi.mocked(api.getAuditLogs).mockResolvedValue([]);
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: true,
      reason: "Upgrading",
    });
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("ON")).toBeInTheDocument();
    });
  });

  it("shows error on API failure", async () => {
    vi.mocked(api.getAccounts).mockRejectedValue(new Error("Server error"));
    vi.mocked(api.getAuditLogs).mockRejectedValue(new Error("Server error"));
    vi.mocked(api.getMaintenanceStatus).mockRejectedValue(
      new Error("Server error"),
    );
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/Error/)).toBeInTheDocument();
    });
  });
});
