import { useState } from "react";
import { useATMContext } from "../../hooks/useATMContext";

export function WelcomeScreen() {
  const { dispatch } = useATMContext();
  const [cardNumber, setCardNumber] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleInsertCard = () => {
    const trimmed = cardNumber.trim();
    if (!trimmed) {
      setError("Please enter your card number");
      return;
    }
    setError(null);
    dispatch({ type: "INSERT_CARD", cardNumber: trimmed });
  };

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
          onChange={(e) => setCardNumber(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleInsertCard();
          }}
          placeholder="1000-0001-0001"
          maxLength={20}
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
          onClick={handleInsertCard}
          data-testid="insert-card-btn"
        >
          Insert Card
        </button>
      </div>
    </div>
  );
}
