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
  getCustomers,
  getCustomerDetail,
  createCustomer,
  updateCustomer,
  deactivateCustomer,
  activateCustomer,
  createAccount,
  updateAccount,
  closeAccount,
  resetPin,
} from "../../api/endpoints";

vi.mock("../../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const mockGet = vi.mocked(adminClient.get);
const mockPost = vi.mocked(adminClient.post);
const mockPut = vi.mocked(adminClient.put);

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

  // --- Customer endpoints ---

  it("getCustomers calls GET /customers", async () => {
    const customers = [{ id: 1, first_name: "Alice" }];
    mockGet.mockResolvedValue({ data: customers });
    const result = await getCustomers();
    expect(mockGet).toHaveBeenCalledWith("/customers");
    expect(result).toEqual(customers);
  });

  it("getCustomerDetail calls GET /customers/:id", async () => {
    const detail = { id: 1, first_name: "Alice", accounts: [] };
    mockGet.mockResolvedValue({ data: detail });
    const result = await getCustomerDetail(1);
    expect(mockGet).toHaveBeenCalledWith("/customers/1");
    expect(result).toEqual(detail);
  });

  it("createCustomer calls POST /customers", async () => {
    const data = { first_name: "Bob", last_name: "Smith", email: "bob@test.com", date_of_birth: "1990-01-01" };
    const created = { id: 3, ...data };
    mockPost.mockResolvedValue({ data: created });
    const result = await createCustomer(data);
    expect(mockPost).toHaveBeenCalledWith("/customers", data);
    expect(result).toEqual(created);
  });

  it("updateCustomer calls PUT /customers/:id", async () => {
    const data = { first_name: "Robert" };
    const updated = { id: 3, first_name: "Robert" };
    mockPut.mockResolvedValue({ data: updated });
    const result = await updateCustomer(3, data);
    expect(mockPut).toHaveBeenCalledWith("/customers/3", data);
    expect(result).toEqual(updated);
  });

  it("deactivateCustomer calls POST /customers/:id/deactivate", async () => {
    mockPost.mockResolvedValue({ data: { message: "Deactivated" } });
    const result = await deactivateCustomer(1);
    expect(mockPost).toHaveBeenCalledWith("/customers/1/deactivate");
    expect(result).toEqual({ message: "Deactivated" });
  });

  it("activateCustomer calls POST /customers/:id/activate", async () => {
    mockPost.mockResolvedValue({ data: { message: "Activated" } });
    const result = await activateCustomer(2);
    expect(mockPost).toHaveBeenCalledWith("/customers/2/activate");
    expect(result).toEqual({ message: "Activated" });
  });

  it("createAccount calls POST /customers/:id/accounts", async () => {
    const data = { account_type: "CHECKING" as const, initial_balance_cents: 0 };
    const created = { id: 10, account_number: "1000-0001-0001" };
    mockPost.mockResolvedValue({ data: created });
    const result = await createAccount(1, data);
    expect(mockPost).toHaveBeenCalledWith("/customers/1/accounts", data);
    expect(result).toEqual(created);
  });

  it("updateAccount calls PUT /accounts/:id", async () => {
    const data = { daily_withdrawal_limit_cents: 100000 };
    const updated = { id: 10, daily_withdrawal_limit_cents: 100000 };
    mockPut.mockResolvedValue({ data: updated });
    const result = await updateAccount(10, data);
    expect(mockPut).toHaveBeenCalledWith("/accounts/10", data);
    expect(result).toEqual(updated);
  });

  it("closeAccount calls POST /accounts/:id/close", async () => {
    mockPost.mockResolvedValue({ data: { message: "Account closed" } });
    const result = await closeAccount(10);
    expect(mockPost).toHaveBeenCalledWith("/accounts/10/close");
    expect(result).toEqual({ message: "Account closed" });
  });

  it("resetPin calls POST /cards/:id/reset-pin", async () => {
    mockPost.mockResolvedValue({ data: { message: "PIN reset" } });
    const result = await resetPin(100, "4567");
    expect(mockPost).toHaveBeenCalledWith("/cards/100/reset-pin", { new_pin: "4567" });
    expect(result).toEqual({ message: "PIN reset" });
  });
});
