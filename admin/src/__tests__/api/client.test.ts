import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import axios from "axios";

vi.mock("axios", () => {
  const interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  };
  const instance = {
    interceptors,
    get: vi.fn(),
    post: vi.fn(),
    defaults: { headers: { common: {} } },
  };
  return {
    default: {
      create: vi.fn(() => instance),
      isAxiosError: vi.fn((err: unknown) => {
        return (
          typeof err === "object" &&
          err !== null &&
          "isAxiosError" in err &&
          (err as { isAxiosError: boolean }).isAxiosError === true
        );
      }),
    },
  };
});

describe("adminClient", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it("creates axios instance with correct baseURL", async () => {
    await import("../../api/client");
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: "/admin/api",
      }),
    );
  });

  it("sets withCredentials to true", async () => {
    await import("../../api/client");
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        withCredentials: true,
      }),
    );
  });

  it("sets Content-Type header to application/json", async () => {
    await import("../../api/client");
    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("dispatches admin:session-expired on 401 for non-login endpoints", async () => {
    await import("../../api/client");
    const responseInterceptor = (
      axios.create as Mock
    ).mock.results[0]?.value.interceptors.response.use as Mock;
    const errorHandler = responseInterceptor.mock.calls[0]?.[1] as (
      err: unknown,
    ) => Promise<unknown>;

    const dispatchSpy = vi.spyOn(window, "dispatchEvent");
    const error = {
      isAxiosError: true,
      response: { status: 401 },
      config: { url: "/accounts" },
    };

    await expect(errorHandler(error)).rejects.toBe(error);
    expect(dispatchSpy).toHaveBeenCalledWith(
      expect.objectContaining({ type: "admin:session-expired" }),
    );
    dispatchSpy.mockRestore();
  });

  it("does not dispatch session-expired for login endpoint 401", async () => {
    await import("../../api/client");
    const responseInterceptor = (
      axios.create as Mock
    ).mock.results[0]?.value.interceptors.response.use as Mock;
    const errorHandler = responseInterceptor.mock.calls[0]?.[1] as (
      err: unknown,
    ) => Promise<unknown>;

    const dispatchSpy = vi.spyOn(window, "dispatchEvent");
    const error = {
      isAxiosError: true,
      response: { status: 401 },
      config: { url: "/login" },
    };

    await expect(errorHandler(error)).rejects.toBe(error);
    expect(dispatchSpy).not.toHaveBeenCalled();
    dispatchSpy.mockRestore();
  });
});
