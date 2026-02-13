import { useATMContext } from "../../hooks/useATMContext";

export function DepositReceiptScreen() {
  const { state } = useATMContext();

  const receipt =
    state.lastReceipt?.receiptType === "deposit" ? state.lastReceipt : null;

  if (!receipt) {
    return (
      <div className="screen-content" data-testid="deposit-receipt-screen">
        <div className="screen-content__body">
          <p className="screen-error">No receipt data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-content" data-testid="deposit-receipt-screen">
      <div className="screen-content__header">
        <h2>Deposit Complete</h2>
      </div>
      <div
        className="screen-content__body"
        style={{ justifyContent: "flex-start", alignItems: "stretch" }}
      >
        <div className="receipt-details" data-testid="receipt-details">
          <div className="receipt-row">
            <span>Reference:</span>
            <span className="receipt-ref">{receipt.reference_number}</span>
          </div>
          <div className="receipt-row">
            <span>Amount:</span>
            <span>{receipt.amount}</span>
          </div>
          <div className="receipt-row">
            <span>Available Now:</span>
            <span>{receipt.available_immediately}</span>
          </div>
          {receipt.held_amount !== "$0.00" &&
            receipt.held_amount !== "0.00" && (
              <div className="receipt-row">
                <span>On Hold:</span>
                <span>
                  {receipt.held_amount}
                  {receipt.hold_until ? ` until ${receipt.hold_until}` : ""}
                </span>
              </div>
            )}
          <div className="receipt-row">
            <span>Balance After:</span>
            <span>{receipt.balance_after}</span>
          </div>
        </div>
        <p className="screen-text-dim receipt-message">{receipt.message}</p>
      </div>
    </div>
  );
}
