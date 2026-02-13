import {
  useReducer,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { atmReducer } from "./atmReducer";
import { INITIAL_ATM_STATE } from "./types";
import { ATMContext } from "./context";

export type { ATMContextValue } from "./context";

export function ATMProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(atmReducer, INITIAL_ATM_STATE);

  const handleSessionExpired = useCallback(() => {
    dispatch({ type: "SESSION_TIMEOUT" });
  }, []);

  const handleMaintenance = useCallback(() => {
    dispatch({ type: "MAINTENANCE_MODE" });
  }, []);

  useEffect(() => {
    window.addEventListener("atm:session-expired", handleSessionExpired);
    window.addEventListener("atm:maintenance", handleMaintenance);
    return () => {
      window.removeEventListener("atm:session-expired", handleSessionExpired);
      window.removeEventListener("atm:maintenance", handleMaintenance);
    };
  }, [handleSessionExpired, handleMaintenance]);

  return (
    <ATMContext.Provider value={{ state, dispatch }}>
      {children}
    </ATMContext.Provider>
  );
}
