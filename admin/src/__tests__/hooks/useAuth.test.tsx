import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAuth } from "../../hooks/useAuth";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getAccounts: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
}));

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it("starts in loading state", () => {
    vi.mocked(api.getAccounts).mockReturnValue(new Promise(() => {}));
    const { result } = renderHook(() => useAuth());
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("checks session and sets authenticated on success", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    sessionStorage.setItem("admin_username", "admin");
    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.username).toBe("admin");
  });

  it("checks session and sets unauthenticated on failure", async () => {
    vi.mocked(api.getAccounts).mockRejectedValue(new Error("401"));
    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.username).toBeNull();
  });

  it("login success sets authenticated", async () => {
    vi.mocked(api.getAccounts).mockRejectedValue(new Error("401"));
    vi.mocked(api.login).mockResolvedValue({ message: "ok" });
    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.login("admin", "password");
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.username).toBe("admin");
    expect(sessionStorage.getItem("admin_username")).toBe("admin");
  });

  it("login failure sets error", async () => {
    vi.mocked(api.getAccounts).mockRejectedValue(new Error("401"));
    vi.mocked(api.login).mockRejectedValue(new Error("Invalid credentials"));
    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let threwError = false;
    await act(async () => {
      try {
        await result.current.login("admin", "wrong");
      } catch {
        threwError = true;
      }
    });

    expect(threwError).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBe("Invalid credentials");
  });

  it("handles admin:session-expired event", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    sessionStorage.setItem("admin_username", "admin");
    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    act(() => {
      window.dispatchEvent(new CustomEvent("admin:session-expired"));
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.username).toBeNull();
  });

  it("logout clears state", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue([]);
    vi.mocked(api.logout).mockResolvedValue({ message: "ok" });
    sessionStorage.setItem("admin_username", "admin");
    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.username).toBeNull();
    expect(sessionStorage.getItem("admin_username")).toBeNull();
  });
});
