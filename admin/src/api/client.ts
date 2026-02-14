import axios from "axios";

const adminClient = axios.create({
  baseURL: "/admin/api",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Handle 401 (session expired) globally
adminClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      if (error.response.status === 401) {
        const url = error.config?.url ?? "";
        const isLoginEndpoint = url.includes("/login");
        if (!isLoginEndpoint) {
          window.dispatchEvent(new CustomEvent("admin:session-expired"));
        }
      }
    }
    return Promise.reject(error);
  },
);

export default adminClient;
