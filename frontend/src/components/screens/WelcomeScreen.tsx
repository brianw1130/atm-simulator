import { useState, useCallback, useLayoutEffect } from "react";
import { useATMContext } from "../../hooks/useATMContext";

/** Strip non-digits and insert dashes: 1000-0001-0001 */
function formatCardNumber(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 12);
  if (digits.length <= 4) return digits;
  if (digits.length <= 8) return `${digits.slice(0, 4)}-${digits.slice(4)}`;
  return `${digits.slice(0, 4)}-${digits.slice(4, 8)}-${digits.slice(8)}`;
}

export function WelcomeScreen() {
  const { dispatch } = useATMContext();
  const [cardNumber, setCardNumber] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleDigit = useCallback((digit: string) => {
    setCardNumber((prev) => formatCardNumber(prev + digit));
    setError(null);
  }, []);

  const handleClear = useCallback(() => {
    setCardNumber((prev) => {
      const digits = prev.replace(/\D/g, "");
      return formatCardNumber(digits.slice(0, -1));
    });
    setError(null);
  }, []);

  const handleCancel = useCallback(() => {
    setCardNumber("");
    setError(null);
  }, []);

  const handleEnter = useCallback(() => {
    const trimmed = cardNumber.trim();
    if (!trimmed) {
      setError("Please enter your card number");
      return;
    }
    setError(null);
    dispatch({ type: "INSERT_CARD", cardNumber: trimmed });
  }, [cardNumber, dispatch]);

  // Expose keypad handlers for App.tsx to wire to NumericKeypad
  useLayoutEffect(() => {
    WelcomeScreen.keypadHandlers = {
      onDigit: handleDigit,
      onClear: handleClear,
      onCancel: handleCancel,
      onEnter: handleEnter,
    };
  }, [handleDigit, handleClear, handleCancel, handleEnter]);

  return (
    <div className="screen-content" data-testid="welcome-screen">
      <div className="screen-content__header">
        <h2>Welcome</h2>
        <p>Please insert your card to begin</p>
      </div>
      <div className="screen-content__body">
        <label className="screen-label" htmlFor="card-input">
          Card Number
        </label>
        <input
          id="card-input"
          className="screen-input"
          type="text"
          value={cardNumber}
          onChange={(e) => {
            setCardNumber(formatCardNumber(e.target.value));
            setError(null);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleEnter();
          }}
          placeholder="1000-0001-0001"
          maxLength={14}
          autoFocus
          data-testid="card-input"
        />
        {error && (
          <p className="screen-error" data-testid="welcome-error">
            {error}
          </p>
        )}
      </div>
      <div className="screen-content__footer">
        <button
          className="screen-btn"
          onClick={handleEnter}
          data-testid="insert-card-btn"
        >
          Insert Card
        </button>
      </div>
    </div>
  );
}

// Static property for keypad handler wiring
WelcomeScreen.keypadHandlers = {
  onDigit: (_: string) => { /* noop */ },
  onClear: () => { /* noop */ },
  onCancel: () => { /* noop */ },
  onEnter: () => { /* noop */ },
};
