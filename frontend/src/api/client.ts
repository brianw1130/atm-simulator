import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// Attach session ID to every request
apiClient.interceptors.request.use((config) => {
  const sessionId = sessionStorage.getItem("atm_session_id");
  if (sessionId) {
    config.headers["X-Session-ID"] = sessionId;
  }
  return config;
});

// Handle 401 (session expired) and 503 (maintenance) globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      if (error.response.status === 401) {
        // Only treat as session expiry for authenticated endpoints.
        // Login and PIN change return 401 for wrong credentials — those
        // are handled by each screen's own catch block.
        const url = error.config?.url ?? "";
        const isAuthEndpoint =
          url.includes("/auth/login") || url.includes("/auth/pin/change");
        if (!isAuthEndpoint) {
          window.dispatchEvent(new CustomEvent("atm:session-expired"));
        }
      }
      if (error.response.status === 503) {
        const data: unknown = error.response.data;
        const reason =
          typeof data === "object" &&
          data !== null &&
          "detail" in data &&
          typeof (data as Record<string, unknown>).detail === "string"
            ? (data as Record<string, string>).detail
            : "ATM is under maintenance";
        window.dispatchEvent(
          new CustomEvent("atm:maintenance", { detail: reason }),
        );
      }
    }
    return Promise.reject(error);
  },
);

export default apiClient;
