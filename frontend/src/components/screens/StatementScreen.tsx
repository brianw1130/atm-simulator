import { useState, useCallback, useLayoutEffect } from "react";
import { useATMContext } from "../../hooks/useATMContext";
import { generateStatement } from "../../api/endpoints";
import type { StatementResponse } from "../../api/types";
import axios from "axios";

export function StatementScreen() {
  const { state, dispatch } = useATMContext();
  const [result, setResult] = useState<StatementResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = useCallback(
    async (days: number) => {
      dispatch({ type: "SET_LOADING", loading: true });
      setError(null);

      try {
        const response = await generateStatement({ days });
        setResult(response);
      } catch (err: unknown) {
        let message = "Failed to generate statement";
        if (axios.isAxiosError(err) && err.response?.data) {
          const data = err.response.data as { detail?: string };
          if (data.detail) message = data.detail;
        }
        setError(message);
      } finally {
        dispatch({ type: "SET_LOADING", loading: false });
      }
    },
    [dispatch],
  );

  useLayoutEffect(() => {
    StatementScreen.handleGenerate = handleGenerate;
  }, [handleGenerate]);

  const handleDownload = useCallback(() => {
    if (!result) return;
    const filename = result.file_path.split("/").pop() ?? "";
    window.open(`/api/v1/statements/download/${filename}`, "_blank");
  }, [result]);

  const selectedAccount = state.accounts.find(
    (a) => a.id === state.selectedAccountId,
  );

  if (result) {
    return (
      <div className="screen-content" data-testid="statement-screen">
        <div className="screen-content__header">
          <h2>Statement Ready</h2>
        </div>
        <div
          className="screen-content__body"
          style={{ justifyContent: "flex-start", alignItems: "stretch" }}
        >
          <div className="receipt-details" data-testid="statement-result">
            <div className="receipt-row">
              <span>Period:</span>
              <span>{result.period}</span>
            </div>
            <div className="receipt-row">
              <span>Transactions:</span>
              <span>{String(result.transaction_count)}</span>
            </div>
            <div className="receipt-row">
              <span>Opening Balance:</span>
              <span>{result.opening_balance}</span>
            </div>
            <div className="receipt-row">
              <span>Closing Balance:</span>
              <span>{result.closing_balance}</span>
            </div>
          </div>
          <button
            className="screen-btn"
            onClick={handleDownload}
            data-testid="download-btn"
            style={{ marginTop: "12px" }}
          >
            Download PDF
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-content" data-testid="statement-screen">
      <div className="screen-content__header">
        <h2>Account Statement</h2>
        {selectedAccount && (
          <p className="screen-text-dim">
            {selectedAccount.account_type} — ****
            {selectedAccount.account_number.slice(-4)}
          </p>
        )}
      </div>
      <div className="screen-content__body">
        <p className="screen-text-dim">Select period using side buttons</p>
        {error && (
          <p className="screen-error" data-testid="statement-error">
            {error}
          </p>
        )}
        {state.isLoading && (
          <p className="screen-text-dim">Generating...</p>
        )}
      </div>
    </div>
  );
}

StatementScreen.handleGenerate = async (_days: number) => {};
