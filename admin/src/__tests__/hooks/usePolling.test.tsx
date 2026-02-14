import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { usePolling } from "../../hooks/usePolling";

describe("usePolling", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("fetches immediately on mount", async () => {
    const fetchFn = vi.fn().mockResolvedValue({ count: 42 });
    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(fetchFn).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual({ count: 42 });
    expect(result.current.error).toBeNull();
  });

  it("fetches on interval", async () => {
    const fetchFn = vi.fn().mockResolvedValue("data");
    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(fetchFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });
    expect(fetchFn).toHaveBeenCalledTimes(2);
  });

  it("cleans up interval on unmount", async () => {
    const fetchFn = vi.fn().mockResolvedValue("data");
    const { result, unmount } = renderHook(() => usePolling(fetchFn, 5000));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    unmount();

    await act(async () => {
      vi.advanceTimersByTime(10000);
    });
    // Should only have been called once (on mount), not again after unmount
    expect(fetchFn).toHaveBeenCalledTimes(1);
  });

  it("sets error state on fetch failure", async () => {
    const fetchFn = vi.fn().mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.data).toBeNull();
  });

  it("handles non-Error rejection", async () => {
    const fetchFn = vi.fn().mockRejectedValue("string error");
    const { result } = renderHook(() => usePolling(fetchFn, 5000));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Fetch failed");
  });
});
