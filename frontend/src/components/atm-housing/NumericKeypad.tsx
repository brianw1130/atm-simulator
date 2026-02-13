import { useEffect, useCallback } from "react";
import "./NumericKeypad.css";

interface NumericKeypadProps {
  onDigit: (digit: string) => void;
  onClear: () => void;
  onCancel: () => void;
  onEnter: () => void;
  disabled?: boolean;
}

const DIGIT_KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];

export function NumericKeypad({
  onDigit,
  onClear,
  onCancel,
  onEnter,
  disabled = false,
}: NumericKeypadProps) {
  // Map physical keyboard to keypad actions
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (disabled) return;
      if (e.key >= "0" && e.key <= "9") {
        onDigit(e.key);
      } else if (e.key === "Enter") {
        onEnter();
      } else if (e.key === "Escape") {
        onCancel();
      } else if (e.key === "Backspace" || e.key === "Delete") {
        onClear();
      }
    },
    [disabled, onDigit, onClear, onCancel, onEnter],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="keypad" data-testid="numeric-keypad">
      <div className="keypad__number-grid">
        {DIGIT_KEYS.map((digit) => (
          <button
            key={digit}
            className="key key--number"
            onClick={() => onDigit(digit)}
            disabled={disabled}
            aria-label={`Digit ${digit}`}
            data-testid={`key-${digit}`}
          >
            {digit}
          </button>
        ))}
        <button
          className="key key--number key--zero"
          onClick={() => onDigit("0")}
          disabled={disabled}
          aria-label="Digit 0"
          data-testid="key-0"
        >
          0
        </button>
      </div>
      <div className="keypad__function-keys">
        <button
          className="key key--cancel"
          onClick={onCancel}
          disabled={disabled}
          aria-label="Cancel"
          data-testid="key-cancel"
        >
          CANCEL
        </button>
        <button
          className="key key--clear"
          onClick={onClear}
          disabled={disabled}
          aria-label="Clear"
          data-testid="key-clear"
        >
          CLEAR
        </button>
        <button
          className="key key--enter"
          onClick={onEnter}
          disabled={disabled}
          aria-label="Enter"
          data-testid="key-enter"
        >
          ENTER
        </button>
      </div>
    </div>
  );
}
