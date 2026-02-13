import { createContext } from "react";
import type { ATMState, ATMAction } from "./types";

export interface ATMContextValue {
  state: ATMState;
  dispatch: React.Dispatch<ATMAction>;
}

export const ATMContext = createContext<ATMContextValue | null>(null);
