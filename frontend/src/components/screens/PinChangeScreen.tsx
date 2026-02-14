import { useState, useCallback, useRef, useLayoutEffect } from "react";
import { useATMContext } from "../../hooks/useATMContext";
import { changePin } from "../../api/endpoints";
import axios from "axios";

const MAX_PIN_LENGTH = 6;

type Phase = "current" | "new_pin" | "confirm";

export function PinChangeScreen() {
  const { state, dispatch } = useATMContext();
  const [pin, setPin] = useState("");
  const [phase, setPhase] = useState<Phase>("current");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Store completed phase values in refs (no re-render needed)
  const savedCurrentPin = useRef("");
  const savedNewPin = useRef("");

  const handleDigit = useCallback(
    (digit: string) => {
      if (state.isLoading || success) return;
      setPin((prev) => (prev.length < MAX_PIN_LENGTH ? prev + digit : prev));
      setError(null);
    },
    [state.isLoading, success],
  );

  const handleClear = useCallback(() => {
    setPin((prev) => prev.slice(0, -1));
    setError(null);
  }, []);

  const handleCancel = useCallback(() => {
    dispatch({ type: "GO_BACK" });
  }, [dispatch]);

  const handleEnter = useCallback(async () => {
    if (phase === "current") {
      if (pin.length < 4) {
        setError("PIN must be at least 4 digits");
        return;
      }
      savedCurrentPin.current = pin;
      setPin("");
      setPhase("new_pin");
      setError(null);
    } else if (phase === "new_pin") {
      if (pin.length < 4) {
        setError("PIN must be at least 4 digits");
        return;
      }
      savedNewPin.current = pin;
      setPin("");
      setPhase("confirm");
      setError(null);
    } else {
      if (pin !== savedNewPin.current) {
        setError("PINs do not match");
        setPin("");
        return;
      }

      dispatch({ type: "SET_LOADING", loading: true });
      setError(null);

      try {
        await changePin({
          current_pin: savedCurrentPin.current,
          new_pin: savedNewPin.current,
          confirm_pin: pin,
        });
        setSuccess(true);
        dispatch({ type: "SET_LOADING", loading: false });
      } catch (err: unknown) {
        let message = "PIN change failed";
        if (axios.isAxiosError(err) && err.response?.data) {
          const data = err.response.data as Record<string, unknown>;
          if (typeof data.detail === "string") {
            message = data.detail;
          } else if (Array.isArray(data.detail) && data.detail.length > 0) {
            const first = data.detail[0] as { msg?: string };
            message = (first.msg ?? message).replace(/^Value error, /i, "");
          }
        }
        dispatch({ type: "SET_LOADING", loading: false });
        setError(message);
        savedCurrentPin.current = "";
        savedNewPin.current = "";
        setPin("");
        setPhase("current");
      }
    }
  }, [phase, pin, dispatch]);

  useLayoutEffect(() => {
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
              className={`pin-dot ${i < pin.length ? "pin-dot--filled" : ""}`}
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
