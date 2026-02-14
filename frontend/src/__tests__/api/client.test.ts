import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";

interface RequestHandler {
  fulfilled: (config: InternalAxiosRequestConfig) => InternalAxiosRequestConfig;
}

interface ResponseHandler {
  rejected: (error: AxiosError) => Promise<never>;
}

function getRequestHandler(apiClient: ReturnType<typeof axios.create>): RequestHandler {
  const interceptors = apiClient.interceptors.request as unknown as {
    handlers: RequestHandler[];
  };
  const handler = interceptors.handlers[0];
  if (!handler) throw new Error("No request interceptor registered");
  return handler;
}

function getResponseHandler(apiClient: ReturnType<typeof axios.create>): ResponseHandler {
  const interceptors = apiClient.interceptors.response as unknown as {
    handlers: ResponseHandler[];
  };
  const handler = interceptors.handlers[0];
  if (!handler) throw new Error("No response interceptor registered");
  return handler;
}

describe("API client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  afterEach(() => {
    sessionStorage.clear();
  });

  it("creates an axios instance with correct baseURL", async () => {
    const { default: apiClient } = await import("../../api/client");
    expect(apiClient.defaults.baseURL).toBe("/api/v1");
  });

  it("sets 30s timeout", async () => {
    const { default: apiClient } = await import("../../api/client");
    expect(apiClient.defaults.timeout).toBe(30_000);
  });

  it("sets Content-Type to application/json", async () => {
    const { default: apiClient } = await import("../../api/client");
    expect(apiClient.defaults.headers["Content-Type"]).toBe("application/json");
  });

  it("attaches session ID from sessionStorage to requests", async () => {
    const { default: apiClient } = await import("../../api/client");
    sessionStorage.setItem("atm_session_id", "test-session-123");

    const handler = getRequestHandler(apiClient);
    const config = {
      headers: new axios.AxiosHeaders(),
    } as InternalAxiosRequestConfig;

    const result = handler.fulfilled(config);
    expect(result.headers["X-Session-ID"]).toBe("test-session-123");
  });

  it("does not attach session header when no session exists", async () => {
    const { default: apiClient } = await import("../../api/client");

    const handler = getRequestHandler(apiClient);
    const config = {
      headers: new axios.AxiosHeaders(),
    } as InternalAxiosRequestConfig;

    const result = handler.fulfilled(config);
    expect(result.headers["X-Session-ID"]).toBeUndefined();
  });

  it("dispatches session-expired event on 401 for non-auth endpoints", async () => {
    const { default: apiClient } = await import("../../api/client");
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");

    const handler = getResponseHandler(apiClient);
    const error = {
      isAxiosError: true,
      config: { url: "/accounts/" },
      response: { status: 401, data: {} },
    } as unknown as AxiosError;

    vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

    await expect(handler.rejected(error)).rejects.toBe(error);
    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(CustomEvent));
    const event = dispatchSpy.mock.calls[0]?.[0] as CustomEvent;
    expect(event.type).toBe("atm:session-expired");

    dispatchSpy.mockRestore();
  });

  it("does not dispatch session-expired on 401 from /auth/login", async () => {
    const { default: apiClient } = await import("../../api/client");
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");

    const handler = getResponseHandler(apiClient);
    const error = {
      isAxiosError: true,
      config: { url: "/auth/login" },
      response: { status: 401, data: { detail: "Invalid PIN" } },
    } as unknown as AxiosError;

    vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

    await expect(handler.rejected(error)).rejects.toBe(error);
    expect(dispatchSpy).not.toHaveBeenCalled();

    dispatchSpy.mockRestore();
  });

  it("does not dispatch session-expired on 401 from /auth/pin/change", async () => {
    const { default: apiClient } = await import("../../api/client");
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");

    const handler = getResponseHandler(apiClient);
    const error = {
      isAxiosError: true,
      config: { url: "/auth/pin/change" },
      response: { status: 401, data: { detail: "Incorrect current PIN" } },
    } as unknown as AxiosError;

    vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

    await expect(handler.rejected(error)).rejects.toBe(error);
    expect(dispatchSpy).not.toHaveBeenCalled();

    dispatchSpy.mockRestore();
  });

  it("dispatches maintenance event on 503 response", async () => {
    const { default: apiClient } = await import("../../api/client");
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");

    const handler = getResponseHandler(apiClient);
    const error = {
      isAxiosError: true,
      response: {
        status: 503,
        data: { detail: "ATM is under maintenance" },
      },
    } as unknown as AxiosError;

    vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

    await expect(handler.rejected(error)).rejects.toBe(error);
    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(CustomEvent));
    const event = dispatchSpy.mock.calls[0]?.[0] as CustomEvent;
    expect(event.type).toBe("atm:maintenance");
    expect(event.detail).toBe("ATM is under maintenance");

    dispatchSpy.mockRestore();
  });

  it("dispatches maintenance event with default message when detail is missing", async () => {
    const { default: apiClient } = await import("../../api/client");
    const dispatchSpy = vi.spyOn(window, "dispatchEvent");

    const handler = getResponseHandler(apiClient);
    const error = {
      isAxiosError: true,
      response: { status: 503, data: {} },
    } as unknown as AxiosError;

    vi.spyOn(axios, "isAxiosError").mockReturnValue(true);

    await expect(handler.rejected(error)).rejects.toBe(error);
    const event = dispatchSpy.mock.calls[0]?.[0] as CustomEvent;
    expect(event.detail).toBe("ATM is under maintenance");

    dispatchSpy.mockRestore();
  });
});
