import { describe, it, expect, vi, beforeEach } from "vitest";
import adminClient from "../../api/client";
import {
  login,
  logout,
  getAccounts,
  freezeAccount,
  unfreezeAccount,
  getAuditLogs,
  getMaintenanceStatus,
  enableMaintenance,
  disableMaintenance,
} from "../../api/endpoints";

vi.mock("../../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockGet = vi.mocked(adminClient.get);
const mockPost = vi.mocked(adminClient.post);

describe("API endpoints", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("login sends username and password", async () => {
    mockPost.mockResolvedValue({ data: { message: "Admin login successful" } });
    const result = await login("admin", "pass123");
    expect(mockPost).toHaveBeenCalledWith("/login", {
      username: "admin",
      password: "pass123",
    });
    expect(result).toEqual({ message: "Admin login successful" });
  });

  it("logout calls POST /logout", async () => {
    mockPost.mockResolvedValue({ data: { message: "Logged out" } });
    const result = await logout();
    expect(mockPost).toHaveBeenCalledWith("/logout");
    expect(result).toEqual({ message: "Logged out" });
  });

  it("getAccounts calls GET /accounts", async () => {
    const accounts = [{ id: 1, account_number: "1000-0001-0001" }];
    mockGet.mockResolvedValue({ data: accounts });
    const result = await getAccounts();
    expect(mockGet).toHaveBeenCalledWith("/accounts");
    expect(result).toEqual(accounts);
  });

  it("freezeAccount calls POST /accounts/:id/freeze", async () => {
    mockPost.mockResolvedValue({ data: { message: "Account frozen" } });
    const result = await freezeAccount(5);
    expect(mockPost).toHaveBeenCalledWith("/accounts/5/freeze");
    expect(result).toEqual({ message: "Account frozen" });
  });

  it("unfreezeAccount calls POST /accounts/:id/unfreeze", async () => {
    mockPost.mockResolvedValue({ data: { message: "Account unfrozen" } });
    const result = await unfreezeAccount(5);
    expect(mockPost).toHaveBeenCalledWith("/accounts/5/unfreeze");
    expect(result).toEqual({ message: "Account unfrozen" });
  });

  it("getAuditLogs calls GET /audit-logs with params", async () => {
    const logs = [{ id: 1, event_type: "AUTH_SUCCESS" }];
    mockGet.mockResolvedValue({ data: logs });
    const result = await getAuditLogs(50, "AUTH_SUCCESS");
    expect(mockGet).toHaveBeenCalledWith("/audit-logs", {
      params: { limit: 50, event_type: "AUTH_SUCCESS" },
    });
    expect(result).toEqual(logs);
  });

  it("getMaintenanceStatus calls GET /maintenance/status", async () => {
    const status = { enabled: false, reason: null };
    mockGet.mockResolvedValue({ data: status });
    const result = await getMaintenanceStatus();
    expect(mockGet).toHaveBeenCalledWith("/maintenance/status");
    expect(result).toEqual(status);
  });

  it("enableMaintenance sends reason", async () => {
    mockPost.mockResolvedValue({ data: { message: "Maintenance enabled" } });
    const result = await enableMaintenance("Scheduled update");
    expect(mockPost).toHaveBeenCalledWith("/maintenance/enable", {
      reason: "Scheduled update",
    });
    expect(result).toEqual({ message: "Maintenance enabled" });
  });

  it("enableMaintenance sends empty body without reason", async () => {
    mockPost.mockResolvedValue({ data: { message: "Maintenance enabled" } });
    await enableMaintenance();
    expect(mockPost).toHaveBeenCalledWith("/maintenance/enable", {});
  });

  it("getAuditLogs omits event_type when not provided", async () => {
    mockGet.mockResolvedValue({ data: [] });
    await getAuditLogs(100);
    expect(mockGet).toHaveBeenCalledWith("/audit-logs", {
      params: { limit: 100 },
    });
  });

  it("disableMaintenance calls POST /maintenance/disable", async () => {
    mockPost.mockResolvedValue({ data: { message: "Maintenance disabled" } });
    const result = await disableMaintenance();
    expect(mockPost).toHaveBeenCalledWith("/maintenance/disable");
    expect(result).toEqual({ message: "Maintenance disabled" });
  });
});
