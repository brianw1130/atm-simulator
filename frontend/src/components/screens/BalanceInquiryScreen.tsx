import { useEffect, useState } from "react";
import { useATMContext } from "../../hooks/useATMContext";
import { getBalance } from "../../api/endpoints";
import { MiniStatement } from "../shared/MiniStatement";
import type { BalanceInquiryResponse } from "../../api/types";
import axios from "axios";

export function BalanceInquiryScreen() {
  const { state, dispatch } = useATMContext();
  const [data, setData] = useState<BalanceInquiryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!state.selectedAccountId) return;

    let cancelled = false;
    dispatch({ type: "SET_LOADING", loading: true });

    getBalance(state.selectedAccountId)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          let message = "Failed to retrieve balance";
          if (axios.isAxiosError(err) && err.response?.data) {
            const errData = err.response.data as { detail?: string };
            if (errData.detail) message = errData.detail;
          }
          setError(message);
        }
      })
      .finally(() => {
        if (!cancelled) dispatch({ type: "SET_LOADING", loading: false });
      });

    return () => {
      cancelled = true;
    };
  }, [state.selectedAccountId, dispatch]);

  if (error) {
    return (
      <div className="screen-content" data-testid="balance-inquiry-screen">
        <div className="screen-content__header">
          <h2>Balance Inquiry</h2>
        </div>
        <div className="screen-content__body">
          <p className="screen-error">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="screen-content" data-testid="balance-inquiry-screen">
        <div className="screen-content__header">
          <h2>Balance Inquiry</h2>
        </div>
        <div className="screen-content__body">
          <p className="screen-text-dim">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-content" data-testid="balance-inquiry-screen">
      <div className="screen-content__header">
        <h2>Balance Inquiry</h2>
        <p className="screen-text-dim">
          {data.account.account_type} — ****
          {data.account.account_number.slice(-4)}
        </p>
      </div>
      <div
        className="screen-content__body"
        style={{ justifyContent: "flex-start", alignItems: "stretch" }}
      >
        <div className="balance-display">
          <div className="balance-row">
            <span>Available Balance:</span>
            <span className="balance-amount">
              ${data.account.available_balance}
            </span>
          </div>
          <div className="balance-row">
            <span>Total Balance:</span>
            <span className="balance-amount">${data.account.balance}</span>
          </div>
        </div>
        <div className="balance-transactions">
          <p className="screen-label">Recent Transactions</p>
          <MiniStatement transactions={data.recent_transactions} />
        </div>
      </div>
    </div>
  );
}
