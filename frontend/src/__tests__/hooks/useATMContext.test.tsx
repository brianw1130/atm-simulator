import { describe, it, expect } from "vitest";
import { renderHook } from "@testing-library/react";
import { useATMContext } from "../../hooks/useATMContext";

describe("useATMContext", () => {
  it("throws when used outside ATMProvider", () => {
    expect(() => {
      renderHook(() => useATMContext());
    }).toThrow("useATMContext must be used within an ATMProvider");
  });
});
