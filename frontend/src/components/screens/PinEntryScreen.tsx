import { useState, useCallback, useEffect } from "react";
import { useATMContext } from "../../hooks/useATMContext";
import { login, listAccounts } from "../../api/endpoints";
import axios from "axios";

const MAX_PIN_LENGTH = 6;

export function PinEntryScreen() {
  const { state, dispatch } = useATMContext();
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleDigit = useCallback(
    (digit: string) => {
      if (state.isLoading) return;
      setPin((prev) => (prev.length < MAX_PIN_LENGTH ? prev + digit : prev));
      setError(null);
    },
    [state.isLoading],
  );

  const handleClear = useCallback(() => {
    setPin("");
    setError(null);
  }, []);

  const handleCancel = useCallback(() => {
    dispatch({ type: "LOGOUT" });
  }, [dispatch]);

  const handleEnter = useCallback(async () => {
    if (pin.length < 4) {
      setError("PIN must be at least 4 digits");
      return;
    }
    if (!state.cardNumber) {
      setError("No card number found");
      return;
    }

    dispatch({ type: "SET_LOADING", loading: true });
    setError(null);

    try {
      const loginResponse = await login({
        card_number: state.cardNumber,
        pin,
      });

      // Store session in sessionStorage for persistence across refresh
      sessionStorage.setItem("atm_session_id", loginResponse.session_id);

      // Fetch account list for main menu
      const accountsResponse = await listAccounts();

      dispatch({
        type: "LOGIN_SUCCESS",
        payload: loginResponse,
        accounts: accountsResponse.accounts,
      });
    } catch (err) {
      let message = "Authentication failed";
      if (axios.isAxiosError(err) && err.response?.data) {
        const data = err.response.data as { detail?: string };
        if (data.detail) {
          message = data.detail;
        }
      }
      dispatch({ type: "LOGIN_FAILURE", error: message });
      setError(message);
      setPin("");
    }
  }, [pin, state.cardNumber, dispatch]);

  // Expose keypad handlers for App.tsx to wire to NumericKeypad
  useEffect(() => {
    PinEntryScreen.keypadHandlers = {
      onDigit: handleDigit,
      onClear: handleClear,
      onCancel: handleCancel,
      onEnter: handleEnter,
    };
  }, [handleDigit, handleClear, handleCancel, handleEnter]);

  const maskedCard = state.cardNumber
    ? `****${state.cardNumber.slice(-4)}`
    : "****";

  return (
    <div className="screen-content" data-testid="pin-entry-screen">
      <div className="screen-content__header">
        <h2>Enter Your PIN</h2>
        <p className="screen-text-dim">Card: {maskedCard}</p>
      </div>
      <div className="screen-content__body">
        <div className="pin-display" data-testid="pin-display">
          {Array.from({ length: MAX_PIN_LENGTH }, (_, i) => (
            <span
              key={i}
              className={`pin-dot ${i < pin.length ? "pin-dot--filled" : ""}`}
            />
          ))}
        </div>
        {error && (
          <p className="screen-error" data-testid="pin-error">
            {error}
          </p>
        )}
        {state.isLoading && (
          <p className="screen-text-dim" data-testid="pin-loading">
            Verifying...
          </p>
        )}
      </div>
    </div>
  );
}

// Static property for keypad handler wiring
PinEntryScreen.keypadHandlers = {
  onDigit: (_: string) => { /* noop */ },
  onClear: () => { /* noop */ },
  onCancel: () => { /* noop */ },
  onEnter: () => { /* noop */ },
};
