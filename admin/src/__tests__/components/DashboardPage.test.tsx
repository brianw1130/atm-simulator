import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DashboardPage } from "../../components/pages/DashboardPage";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getAccounts: vi.fn(),
  getAuditLogs: vi.fn(),
  getMaintenanceStatus: vi.fn(),
  exportSnapshot: vi.fn(),
  importSnapshot: vi.fn(),
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

function mockDashboardData() {
  vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
  vi.mocked(api.getAuditLogs).mockResolvedValue(mockLogs);
  vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
    enabled: false,
    reason: null,
  });
}

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
    mockDashboardData();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Total Accounts")).toBeInTheDocument();
    });

    // 2 total accounts, 1 active, 1 frozen
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("OFF")).toBeInTheDocument();
  });

  it("renders recent activity table", async () => {
    mockDashboardData();
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

  // --- Data Management section ---

  it("renders Data Management section", async () => {
    mockDashboardData();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Data Management")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "Export Snapshot" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Import Snapshot" })).toBeInTheDocument();
  });

  it("export button triggers download", async () => {
    mockDashboardData();
    const blob = new Blob(['{"version":"1.0"}'], { type: "application/json" });
    vi.mocked(api.exportSnapshot).mockResolvedValue(blob);

    const createObjectURL = vi.fn().mockReturnValue("blob:fake-url");
    const revokeObjectURL = vi.fn();
    globalThis.URL.createObjectURL = createObjectURL;
    globalThis.URL.revokeObjectURL = revokeObjectURL;

    const user = userEvent.setup();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Export Snapshot" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Export Snapshot" }));

    await waitFor(() => {
      expect(api.exportSnapshot).toHaveBeenCalledOnce();
    });
    expect(createObjectURL).toHaveBeenCalledWith(blob);
  });

  it("shows error on export failure", async () => {
    mockDashboardData();
    vi.mocked(api.exportSnapshot).mockRejectedValue(new Error("fail"));

    const user = userEvent.setup();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Export Snapshot" })).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: "Export Snapshot" }));

    await waitFor(() => {
      expect(screen.getByText("Failed to export snapshot")).toBeInTheDocument();
    });
  });

  it("import button disabled without file", async () => {
    mockDashboardData();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Import")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Import" })).toBeDisabled();
  });

  it("opens import confirm dialog when file selected", async () => {
    mockDashboardData();
    const user = userEvent.setup();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Import Snapshot" })).toBeInTheDocument();
    });

    const file = new File(['{"version":"1.0"}'], "snapshot.json", { type: "application/json" });
    const input = screen.getByLabelText("Snapshot file");
    await user.upload(input, file);

    await user.click(screen.getByRole("button", { name: "Import" }));

    expect(screen.getByText(/This will import data from/)).toBeInTheDocument();
  });

  it("completes import flow", async () => {
    mockDashboardData();
    vi.mocked(api.importSnapshot).mockResolvedValue({
      customers_created: 2,
      accounts_created: 3,
    });

    const user = userEvent.setup();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Import Snapshot" })).toBeInTheDocument();
    });

    const file = new File(['{"version":"1.0"}'], "snapshot.json", { type: "application/json" });
    const input = screen.getByLabelText("Snapshot file");
    await user.upload(input, file);

    await user.click(screen.getByRole("button", { name: "Import" }));

    // Confirm import
    const dialog = await screen.findByRole("dialog");
    const confirmBtn = dialog.querySelector("button.btn--warning");
    expect(confirmBtn).not.toBeNull();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- test element known to exist
    await user.click(confirmBtn!);

    await waitFor(() => {
      expect(api.importSnapshot).toHaveBeenCalledWith(file, "skip");
    });
  });

  it("shows error on import failure", async () => {
    mockDashboardData();
    vi.mocked(api.importSnapshot).mockRejectedValue(new Error("fail"));

    const user = userEvent.setup();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Import Snapshot" })).toBeInTheDocument();
    });

    const file = new File(['{"version":"1.0"}'], "test.json", { type: "application/json" });
    const input = screen.getByLabelText("Snapshot file");
    await user.upload(input, file);

    await user.click(screen.getByRole("button", { name: "Import" }));

    const dialog = await screen.findByRole("dialog");
    const confirmBtn = dialog.querySelector("button.btn--warning");
    expect(confirmBtn).not.toBeNull();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- test element known to exist
    await user.click(confirmBtn!);

    await waitFor(() => {
      expect(screen.getByText("Failed to import snapshot")).toBeInTheDocument();
    });
  });

  it("can select replace conflict strategy", async () => {
    mockDashboardData();
    vi.mocked(api.importSnapshot).mockResolvedValue({ customers_created: 0, accounts_created: 0 });

    const user = userEvent.setup();
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Replace existing")).toBeInTheDocument();
    });

    await user.click(screen.getByLabelText("Replace existing"));

    const file = new File(['{"version":"1.0"}'], "snap.json", { type: "application/json" });
    const input = screen.getByLabelText("Snapshot file");
    await user.upload(input, file);

    await user.click(screen.getByRole("button", { name: "Import" }));

    const dialog = await screen.findByRole("dialog");
    const confirmBtn = dialog.querySelector("button.btn--warning");
    expect(confirmBtn).not.toBeNull();
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- test element known to exist
    await user.click(confirmBtn!);

    await waitFor(() => {
      expect(api.importSnapshot).toHaveBeenCalledWith(file, "replace");
    });
  });
});
