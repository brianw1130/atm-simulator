import { useState, useCallback, useEffect } from "react";
import { useATMContext } from "../../hooks/useATMContext";

const MAX_ACCOUNT_DIGITS = 14;
const MAX_AMOUNT_DIGITS = 6;

type Phase = "destination" | "amount";

export function TransferScreen() {
  const { state, dispatch } = useATMContext();
  const [destinationStr, setDestinationStr] = useState("");
  const [amountStr, setAmountStr] = useState("");
  const [phase, setPhase] = useState<Phase>("destination");
  const [error, setError] = useState<string | null>(null);

  const setOwnAccountDestination = useCallback(
    (accountNumber: string) => {
      setDestinationStr(accountNumber);
      setPhase("amount");
      setError(null);
    },
    [],
  );

  const handleDigit = useCallback(
    (digit: string) => {
      if (state.isLoading) return;
      if (phase === "destination") {
        setDestinationStr((prev) => {
          if (prev.length >= MAX_ACCOUNT_DIGITS) return prev;
          return prev + digit;
        });
      } else {
        setAmountStr((prev) => {
          if (prev.length >= MAX_AMOUNT_DIGITS) return prev;
          if (prev === "" && digit === "0") return prev;
          return prev + digit;
        });
      }
      setError(null);
    },
    [state.isLoading, phase],
  );

  const handleClear = useCallback(() => {
    if (phase === "destination") {
      setDestinationStr((prev) => prev.slice(0, -1));
    } else {
      setAmountStr((prev) => prev.slice(0, -1));
    }
    setError(null);
  }, [phase]);

  const handleCancel = useCallback(() => {
    if (phase === "amount" && destinationStr) {
      setPhase("destination");
      setAmountStr("");
      setError(null);
    } else {
      dispatch({ type: "GO_BACK" });
    }
  }, [phase, destinationStr, dispatch]);

  const handleEnter = useCallback(() => {
    if (phase === "destination") {
      if (destinationStr.length === 0) {
        setError("Enter destination account");
        return;
      }
      setPhase("amount");
      setError(null);
    } else {
      const amount = parseInt(amountStr || "0", 10);
      if (amount === 0) {
        setError("Enter an amount");
        return;
      }
      dispatch({
        type: "STAGE_TRANSACTION",
        transaction: {
          type: "transfer",
          amountCents: amount * 100,
          destinationAccount: destinationStr,
        },
      });
    }
  }, [phase, destinationStr, amountStr, dispatch]);

  useEffect(() => {
    TransferScreen.keypadHandlers = {
      onDigit: handleDigit,
      onClear: handleClear,
      onCancel: handleCancel,
      onEnter: handleEnter,
    };
    TransferScreen.setOwnAccountDestination = setOwnAccountDestination;
  }, [handleDigit, handleClear, handleCancel, handleEnter, setOwnAccountDestination]);

  const selectedAccount = state.accounts.find(
    (a) => a.id === state.selectedAccountId,
  );

  return (
    <div className="screen-content" data-testid="transfer-screen">
      <div className="screen-content__header">
        <h2>Transfer</h2>
        {selectedAccount && (
          <p className="screen-text-dim">
            From: {selectedAccount.account_type} — ****
            {selectedAccount.account_number.slice(-4)}
          </p>
        )}
      </div>
      <div className="screen-content__body">
        {phase === "destination" ? (
          <>
            <p className="screen-text-dim">
              Enter destination account or select:
            </p>
            <div className="amount-input" data-testid="destination-display">
              {destinationStr || "—"}
            </div>
          </>
        ) : (
          <>
            <p className="screen-text-dim">
              To: {destinationStr} — Enter amount:
            </p>
            <div className="amount-input" data-testid="amount-display">
              ${amountStr || "0"}
            </div>
          </>
        )}
        {error && (
          <p className="screen-error" data-testid="transfer-error">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}

TransferScreen.keypadHandlers = {
  onDigit: (_: string) => {},
  onClear: () => {},
  onCancel: () => {},
  onEnter: () => {},
};

TransferScreen.setOwnAccountDestination = (_accountNumber: string) => {};
