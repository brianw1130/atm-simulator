import { useState, useCallback, useEffect } from "react";
import { useATMContext } from "../../hooks/useATMContext";

const MAX_AMOUNT_DIGITS = 5;

export function WithdrawalScreen() {
  const { state, dispatch } = useATMContext();
  const [amountStr, setAmountStr] = useState("");
  const [error, setError] = useState<string | null>(null);

  const stageWithdrawal = useCallback(
    (amountCents: number) => {
      dispatch({
        type: "STAGE_TRANSACTION",
        transaction: { type: "withdrawal", amountCents },
      });
    },
    [dispatch],
  );

  const handleDigit = useCallback(
    (digit: string) => {
      if (state.isLoading) return;
      setAmountStr((prev) => {
        if (prev.length >= MAX_AMOUNT_DIGITS) return prev;
        if (prev === "" && digit === "0") return prev;
        return prev + digit;
      });
      setError(null);
    },
    [state.isLoading],
  );

  const handleClear = useCallback(() => {
    setAmountStr((prev) => prev.slice(0, -1));
    setError(null);
  }, []);

  const handleCancel = useCallback(() => {
    dispatch({ type: "GO_BACK" });
  }, [dispatch]);

  const handleEnter = useCallback(() => {
    const amount = parseInt(amountStr || "0", 10);
    if (amount === 0) {
      setError("Enter an amount");
      return;
    }
    if (amount % 20 !== 0) {
      setError("Amount must be a multiple of $20");
      return;
    }
    stageWithdrawal(amount * 100);
  }, [amountStr, stageWithdrawal]);

  useEffect(() => {
    WithdrawalScreen.keypadHandlers = {
      onDigit: handleDigit,
      onClear: handleClear,
      onCancel: handleCancel,
      onEnter: handleEnter,
    };
    WithdrawalScreen.handleQuickAmount = stageWithdrawal;
  }, [handleDigit, handleClear, handleCancel, handleEnter, stageWithdrawal]);

  const selectedAccount = state.accounts.find(
    (a) => a.id === state.selectedAccountId,
  );

  return (
    <div className="screen-content" data-testid="withdrawal-screen">
      <div className="screen-content__header">
        <h2>Withdrawal</h2>
        {selectedAccount && (
          <p className="screen-text-dim">
            {selectedAccount.account_type} — Available: $
            {selectedAccount.available_balance}
          </p>
        )}
      </div>
      <div className="screen-content__body">
        <p className="screen-text-dim">Select amount or enter custom:</p>
        <div className="amount-input" data-testid="amount-display">
          ${amountStr || "0"}
        </div>
        {error && (
          <p className="screen-error" data-testid="withdrawal-error">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}

WithdrawalScreen.keypadHandlers = {
  onDigit: (_: string) => {},
  onClear: () => {},
  onCancel: () => {},
  onEnter: () => {},
};

WithdrawalScreen.handleQuickAmount = (_amountCents: number) => {};
