import { useContext } from "react";
import { ATMContext, type ATMContextValue } from "../state/context";

export function useATMContext(): ATMContextValue {
  const context = useContext(ATMContext);
  if (!context) {
    throw new Error("useATMContext must be used within an ATMProvider");
  }
  return context;
}
