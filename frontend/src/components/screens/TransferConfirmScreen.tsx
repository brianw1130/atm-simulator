import { useState, useCallback } from "react";
import { useATMContext } from "../../hooks/useATMContext";
import { transfer } from "../../api/endpoints";
import axios from "axios";

export function TransferConfirmScreen() {
  const { state, dispatch } = useATMContext();

  const [displayAmount] = useState(() =>
    state.pendingTransaction
      ? `$${(state.pendingTransaction.amountCents / 100).toFixed(2)}`
      : "$0.00",
  );

  const [displayDestination] = useState(
    () => state.pendingTransaction?.destinationAccount ?? "—",
  );

  const handleConfirm = useCallback(async () => {
    if (!state.pendingTransaction?.destinationAccount) return;

    dispatch({ type: "SET_LOADING", loading: true });

    try {
      const response = await transfer({
        destination_account_number: state.pendingTransaction.destinationAccount,
        amount_cents: state.pendingTransaction.amountCents,
      });
      dispatch({
        type: "TRANSACTION_SUCCESS",
        receipt: { ...response, receiptType: "transfer" },
      });
    } catch (err: unknown) {
      let message = "Transfer failed";
      if (axios.isAxiosError(err) && err.response?.data) {
        const data = err.response.data as { detail?: string };
        if (data.detail) message = data.detail;
      }
      dispatch({ type: "TRANSACTION_FAILURE", error: message });
    }
  }, [state.pendingTransaction, dispatch]);

  TransferConfirmScreen.handleConfirm = handleConfirm;

  const selectedAccount = state.accounts.find(
    (a) => a.id === state.selectedAccountId,
  );

  return (
    <div className="screen-content" data-testid="transfer-confirm-screen">
      <div className="screen-content__header">
        <h2>Confirm Transfer</h2>
      </div>
      <div className="screen-content__body">
        <div className="confirm-details" data-testid="confirm-details">
          <div className="confirm-row">
            <span>From:</span>
            <span>
              {selectedAccount
                ? `${selectedAccount.account_type} ****${selectedAccount.account_number.slice(-4)}`
                : "—"}
            </span>
          </div>
          <div className="confirm-row">
            <span>To:</span>
            <span>{displayDestination}</span>
          </div>
          <div className="confirm-row">
            <span>Amount:</span>
            <span className="confirm-amount">{displayAmount}</span>
          </div>
        </div>
        {state.lastError && (
          <p className="screen-error" data-testid="confirm-error">
            {state.lastError}
          </p>
        )}
        {state.isLoading && (
          <p className="screen-text-dim">Processing...</p>
        )}
      </div>
    </div>
  );
}

TransferConfirmScreen.handleConfirm = async () => {};
