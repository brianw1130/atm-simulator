import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useNotification } from "../../hooks/useNotification";

describe("useNotification", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("starts with null notification", () => {
    const { result } = renderHook(() => useNotification());
    expect(result.current.notification).toBeNull();
  });

  it("shows success notification", () => {
    const { result } = renderHook(() => useNotification());
    act(() => result.current.showSuccess("Saved!"));
    expect(result.current.notification).toEqual({
      message: "Saved!",
      type: "success",
    });
  });

  it("shows error notification", () => {
    const { result } = renderHook(() => useNotification());
    act(() => result.current.showError("Failed!"));
    expect(result.current.notification).toEqual({
      message: "Failed!",
      type: "error",
    });
  });

  it("dismisses notification", () => {
    const { result } = renderHook(() => useNotification());
    act(() => result.current.showSuccess("Test"));
    expect(result.current.notification).not.toBeNull();
    act(() => result.current.dismiss());
    expect(result.current.notification).toBeNull();
  });

  it("auto-dismisses after 5 seconds", () => {
    const { result } = renderHook(() => useNotification());
    act(() => result.current.showSuccess("Test"));
    expect(result.current.notification).not.toBeNull();

    act(() => vi.advanceTimersByTime(5000));
    expect(result.current.notification).toBeNull();
  });
});
