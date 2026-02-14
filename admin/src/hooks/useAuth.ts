import { useCallback, useEffect, useState } from "react";
import * as api from "../api/endpoints";

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  username: string | null;
  error: string | null;
}

interface UseAuthReturn extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    username: null,
    error: null,
  });

  const checkSession = useCallback(async () => {
    try {
      await api.getAccounts();
      const storedUsername = sessionStorage.getItem("admin_username");
      setState({
        isAuthenticated: true,
        isLoading: false,
        username: storedUsername,
        error: null,
      });
    } catch {
      setState({
        isAuthenticated: false,
        isLoading: false,
        username: null,
        error: null,
      });
    }
  }, []);

  useEffect(() => {
    void checkSession();
  }, [checkSession]);

  useEffect(() => {
    const handleSessionExpired = () => {
      sessionStorage.removeItem("admin_username");
      setState({
        isAuthenticated: false,
        isLoading: false,
        username: null,
        error: null,
      });
    };
    window.addEventListener("admin:session-expired", handleSessionExpired);
    return () => {
      window.removeEventListener("admin:session-expired", handleSessionExpired);
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setState((prev) => ({ ...prev, error: null, isLoading: true }));
    try {
      await api.login(username, password);
      sessionStorage.setItem("admin_username", username);
      setState({
        isAuthenticated: true,
        isLoading: false,
        username,
        error: null,
      });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Login failed";
      setState({
        isAuthenticated: false,
        isLoading: false,
        username: null,
        error: message,
      });
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      sessionStorage.removeItem("admin_username");
      setState({
        isAuthenticated: false,
        isLoading: false,
        username: null,
        error: null,
      });
    }
  }, []);

  return { ...state, login, logout };
}
