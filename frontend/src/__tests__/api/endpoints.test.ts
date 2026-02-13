import { describe, it, expect, vi, beforeEach } from "vitest";
import apiClient from "../../api/client";
import {
  login,
  logout,
  refreshSession,
  changePin,
  listAccounts,
  getBalance,
  withdraw,
  deposit,
  transfer,
  generateStatement,
} from "../../api/endpoints";

vi.mock("../../api/client", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

const mockPost = apiClient.post as ReturnType<typeof vi.fn>;
const mockGet = apiClient.get as ReturnType<typeof vi.fn>;

describe("API endpoints", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("login", () => {
    it("posts to /auth/login and returns response data", async () => {
      const responseData = { session_id: "s1", account_number: "1000-0001-0001", customer_name: "Alice", message: "OK" };
      mockPost.mockResolvedValue({ data: responseData });
      const result = await login({ card_number: "1000-0001-0001", pin: "1234" });
      expect(mockPost).toHaveBeenCalledWith("/auth/login", { card_number: "1000-0001-0001", pin: "1234" });
      expect(result).toEqual(responseData);
    });
  });

  describe("logout", () => {
    it("posts to /auth/logout", async () => {
      mockPost.mockResolvedValue({});
      await logout();
      expect(mockPost).toHaveBeenCalledWith("/auth/logout");
    });
  });

  describe("refreshSession", () => {
    it("posts to /auth/session/refresh and returns data", async () => {
      const data = { message: "Refreshed", timeout_seconds: "120" };
      mockPost.mockResolvedValue({ data });
      const result = await refreshSession();
      expect(mockPost).toHaveBeenCalledWith("/auth/session/refresh");
      expect(result).toEqual(data);
    });
  });

  describe("changePin", () => {
    it("posts to /auth/pin/change", async () => {
      mockPost.mockResolvedValue({});
      await changePin({ current_pin: "1234", new_pin: "5678", confirm_pin: "5678" });
      expect(mockPost).toHaveBeenCalledWith("/auth/pin/change", {
        current_pin: "1234", new_pin: "5678", confirm_pin: "5678",
      });
    });
  });

  describe("listAccounts", () => {
    it("gets /accounts/ and returns data", async () => {
      const data = { accounts: [{ id: 1 }] };
      mockGet.mockResolvedValue({ data });
      const result = await listAccounts();
      expect(mockGet).toHaveBeenCalledWith("/accounts/");
      expect(result).toEqual(data);
    });
  });

  describe("getBalance", () => {
    it("gets /accounts/{id}/balance and returns data", async () => {
      const data = { account: { id: 1 }, recent_transactions: [] };
      mockGet.mockResolvedValue({ data });
      const result = await getBalance(1);
      expect(mockGet).toHaveBeenCalledWith("/accounts/1/balance");
      expect(result).toEqual(data);
    });
  });

  describe("withdraw", () => {
    it("posts to /transactions/withdraw and returns data", async () => {
      const data = { reference_number: "REF-1", amount: "100.00" };
      mockPost.mockResolvedValue({ data });
      const result = await withdraw({ amount_cents: 10000 });
      expect(mockPost).toHaveBeenCalledWith("/transactions/withdraw", { amount_cents: 10000 });
      expect(result).toEqual(data);
    });
  });

  describe("deposit", () => {
    it("posts to /transactions/deposit and returns data", async () => {
      const data = { reference_number: "REF-2", amount: "500.00" };
      mockPost.mockResolvedValue({ data });
      const result = await deposit({ amount_cents: 50000, deposit_type: "cash" });
      expect(mockPost).toHaveBeenCalledWith("/transactions/deposit", {
        amount_cents: 50000, deposit_type: "cash",
      });
      expect(result).toEqual(data);
    });
  });

  describe("transfer", () => {
    it("posts to /transactions/transfer and returns data", async () => {
      const data = { reference_number: "REF-3", amount: "200.00" };
      mockPost.mockResolvedValue({ data });
      const result = await transfer({
        destination_account_number: "1000-0002-0001", amount_cents: 20000,
      });
      expect(mockPost).toHaveBeenCalledWith("/transactions/transfer", {
        destination_account_number: "1000-0002-0001", amount_cents: 20000,
      });
      expect(result).toEqual(data);
    });
  });

  describe("generateStatement", () => {
    it("posts to /statements/generate and returns data", async () => {
      const data = { file_path: "/tmp/stmt.pdf", period: "7 days", transaction_count: 5 };
      mockPost.mockResolvedValue({ data });
      const result = await generateStatement({ days: 7 });
      expect(mockPost).toHaveBeenCalledWith("/statements/generate", { days: 7 });
      expect(result).toEqual(data);
    });
  });
});
