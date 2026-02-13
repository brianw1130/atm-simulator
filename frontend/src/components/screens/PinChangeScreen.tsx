import { useState, useCallback, useEffect } from "react";
import { useATMContext } from "../../hooks/useATMContext";
import { changePin } from "../../api/endpoints";
import axios from "axios";

const MAX_PIN_LENGTH = 6;

type Phase = "current" | "new_pin" | "confirm";

export function PinChangeScreen() {
  const { state, dispatch } = useATMContext();
  const [currentPin, setCurrentPin] = useState("");
  const [newPin, setNewPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [phase, setPhase] = useState<Phase>("current");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const activePin =
    phase === "current" ? currentPin : phase === "new_pin" ? newPin : confirmPin;

  const setActivePin =
    phase === "current"
      ? setCurrentPin
      : phase === "new_pin"
        ? setNewPin
        : setConfirmPin;

  const handleDigit = useCallback(
    (digit: string) => {
      if (state.isLoading || success) return;
      setActivePin((prev) =>
        prev.length < MAX_PIN_LENGTH ? prev + digit : prev,
      );
      setError(null);
    },
    [state.isLoading, success, setActivePin],
  );

  const handleClear = useCallback(() => {
    setActivePin((prev) => prev.slice(0, -1));
    setError(null);
  }, [setActivePin]);

  const handleCancel = useCallback(() => {
    dispatch({ type: "GO_BACK" });
  }, [dispatch]);

  const handleEnter = useCallback(async () => {
    if (phase === "current") {
      if (currentPin.length < 4) {
        setError("PIN must be at least 4 digits");
        return;
      }
      setPhase("new_pin");
      setError(null);
    } else if (phase === "new_pin") {
      if (newPin.length < 4) {
        setError("PIN must be at least 4 digits");
        return;
      }
      setPhase("confirm");
      setError(null);
    } else {
      if (confirmPin !== newPin) {
        setError("PINs do not match");
        setConfirmPin("");
        return;
      }

      dispatch({ type: "SET_LOADING", loading: true });
      setError(null);

      try {
        await changePin({
          current_pin: currentPin,
          new_pin: newPin,
          confirm_pin: confirmPin,
        });
        setSuccess(true);
        dispatch({ type: "SET_LOADING", loading: false });
      } catch (err: unknown) {
        let message = "PIN change failed";
        if (axios.isAxiosError(err) && err.response?.data) {
          const data = err.response.data as { detail?: string };
          if (data.detail) message = data.detail;
        }
        dispatch({ type: "SET_LOADING", loading: false });
        setError(message);
        setCurrentPin("");
        setNewPin("");
        setConfirmPin("");
        setPhase("current");
      }
    }
  }, [phase, currentPin, newPin, confirmPin, dispatch]);

  useEffect(() => {
    PinChangeScreen.keypadHandlers = {
      onDigit: handleDigit,
      onClear: handleClear,
      onCancel: handleCancel,
      onEnter: handleEnter,
    };
  }, [handleDigit, handleClear, handleCancel, handleEnter]);

  if (success) {
    return (
      <div className="screen-content" data-testid="pin-change-screen">
        <div className="screen-content__header">
          <h2>PIN Changed</h2>
        </div>
        <div className="screen-content__body">
          <p>Your PIN has been changed successfully.</p>
        </div>
        <div className="screen-content__footer">
          <button
            className="screen-btn"
            onClick={() => dispatch({ type: "NAVIGATE", screen: "main_menu" })}
            data-testid="pin-change-done-btn"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  const phaseLabel =
    phase === "current"
      ? "Enter current PIN"
      : phase === "new_pin"
        ? "Enter new PIN"
        : "Confirm new PIN";

  const phaseStep =
    phase === "current" ? "1/3" : phase === "new_pin" ? "2/3" : "3/3";

  return (
    <div className="screen-content" data-testid="pin-change-screen">
      <div className="screen-content__header">
        <h2>Change PIN</h2>
        <p className="screen-text-dim">
          Step {phaseStep}: {phaseLabel}
        </p>
      </div>
      <div className="screen-content__body">
        <div className="pin-display" data-testid="pin-display">
          {Array.from({ length: MAX_PIN_LENGTH }, (_, i) => (
            <span
              key={i}
              className={`pin-dot ${i < activePin.length ? "pin-dot--filled" : ""}`}
            />
          ))}
        </div>
        {error && (
          <p className="screen-error" data-testid="pin-change-error">
            {error}
          </p>
        )}
        {state.isLoading && (
          <p className="screen-text-dim">Processing...</p>
        )}
      </div>
    </div>
  );
}

PinChangeScreen.keypadHandlers = {
  onDigit: (_: string) => {},
  onClear: () => {},
  onCancel: () => {},
  onEnter: () => {},
};
