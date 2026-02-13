import { useState, useCallback } from "react";
import { useATMContext } from "../../hooks/useATMContext";
import { deposit } from "../../api/endpoints";
import axios from "axios";

const MAX_AMOUNT_DIGITS = 6;
const MAX_CHECK_DIGITS = 10;

type Phase = "amount" | "check_number";

export function DepositScreen() {
  const { state, dispatch } = useATMContext();
  const [amountStr, setAmountStr] = useState("");
  const [checkNumberStr, setCheckNumberStr] = useState("");
  const [phase, setPhase] = useState<Phase>("amount");
  const [error, setError] = useState<string | null>(null);

  const depositType = state.pendingTransaction?.depositType ?? null;
  const isCheck = depositType === "check";

  const submitDeposit = useCallback(
    async (amountCents: number, checkNumber?: string) => {
      if (!depositType) return;

      dispatch({ type: "SET_LOADING", loading: true });
      setError(null);

      try {
        const response = await deposit({
          amount_cents: amountCents,
          deposit_type: depositType,
          check_number: checkNumber,
        });
        dispatch({
          type: "TRANSACTION_SUCCESS",
          receipt: { ...response, receiptType: "deposit" },
        });
      } catch (err: unknown) {
        let message = "Deposit failed";
        if (axios.isAxiosError(err) && err.response?.data) {
          const data = err.response.data as { detail?: string };
          if (data.detail) message = data.detail;
        }
        dispatch({ type: "TRANSACTION_FAILURE", error: message });
      }
    },
    [depositType, dispatch],
  );

  const handleDigit = useCallback(
    (digit: string) => {
      if (state.isLoading) return;
      if (phase === "amount") {
        setAmountStr((prev) => {
          if (prev.length >= MAX_AMOUNT_DIGITS) return prev;
          if (prev === "" && digit === "0") return prev;
          return prev + digit;
        });
      } else {
        setCheckNumberStr((prev) => {
          if (prev.length >= MAX_CHECK_DIGITS) return prev;
          return prev + digit;
        });
      }
      setError(null);
    },
    [state.isLoading, phase],
  );

  const handleClear = useCallback(() => {
    if (phase === "amount") {
      setAmountStr((prev) => prev.slice(0, -1));
    } else {
      setCheckNumberStr((prev) => prev.slice(0, -1));
    }
    setError(null);
  }, [phase]);

  const handleCancel = useCallback(() => {
    dispatch({ type: "GO_BACK" });
  }, [dispatch]);

  const handleEnter = useCallback(() => {
    if (phase === "amount") {
      const amount = parseInt(amountStr || "0", 10);
      if (amount === 0) {
        setError("Enter an amount");
        return;
      }
      if (isCheck) {
        setPhase("check_number");
        setError(null);
        return;
      }
      void submitDeposit(amount * 100);
    } else {
      if (checkNumberStr.length === 0) {
        setError("Enter check number");
        return;
      }
      const amount = parseInt(amountStr || "0", 10);
      void submitDeposit(amount * 100, checkNumberStr);
    }
  }, [phase, amountStr, isCheck, checkNumberStr, submitDeposit]);

  DepositScreen.keypadHandlers = {
    onDigit: handleDigit,
    onClear: handleClear,
    onCancel: handleCancel,
    onEnter: handleEnter,
  };

  const selectedAccount = state.accounts.find(
    (a) => a.id === state.selectedAccountId,
  );

  // Phase 0: type selection (no pendingTransaction yet)
  if (!state.pendingTransaction) {
    return (
      <div className="screen-content" data-testid="deposit-screen">
        <div className="screen-content__header">
          <h2>Deposit</h2>
          {selectedAccount && (
            <p className="screen-text-dim">
              {selectedAccount.account_type} — ****
              {selectedAccount.account_number.slice(-4)}
            </p>
          )}
        </div>
        <div className="screen-content__body">
          <p className="screen-text-dim">Select deposit type</p>
          <p className="screen-text-dim">using the side buttons</p>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-content" data-testid="deposit-screen">
      <div className="screen-content__header">
        <h2>{isCheck ? "Check" : "Cash"} Deposit</h2>
        {selectedAccount && (
          <p className="screen-text-dim">
            {selectedAccount.account_type} — ****
            {selectedAccount.account_number.slice(-4)}
          </p>
        )}
      </div>
      <div className="screen-content__body">
        {phase === "amount" ? (
          <>
            <p className="screen-text-dim">Enter deposit amount:</p>
            <div className="amount-input" data-testid="amount-display">
              ${amountStr || "0"}
            </div>
          </>
        ) : (
          <>
            <p className="screen-text-dim">
              Amount: ${amountStr} — Enter check number:
            </p>
            <div className="amount-input" data-testid="check-number-display">
              #{checkNumberStr || "—"}
            </div>
          </>
        )}
        {error && (
          <p className="screen-error" data-testid="deposit-error">
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

DepositScreen.keypadHandlers = {
  onDigit: (_: string) => {},
  onClear: () => {},
  onCancel: () => {},
  onEnter: () => {},
};
