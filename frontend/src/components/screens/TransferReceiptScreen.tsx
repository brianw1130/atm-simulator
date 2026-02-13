import { useATMContext } from "../../hooks/useATMContext";

export function TransferReceiptScreen() {
  const { state } = useATMContext();

  const receipt =
    state.lastReceipt?.receiptType === "transfer" ? state.lastReceipt : null;

  if (!receipt) {
    return (
      <div className="screen-content" data-testid="transfer-receipt-screen">
        <div className="screen-content__body">
          <p className="screen-error">No receipt data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-content" data-testid="transfer-receipt-screen">
      <div className="screen-content__header">
        <h2>Transfer Complete</h2>
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
            <span>From:</span>
            <span>{receipt.source_account}</span>
          </div>
          <div className="receipt-row">
            <span>To:</span>
            <span>{receipt.destination_account}</span>
          </div>
          <div className="receipt-row">
            <span>Amount:</span>
            <span>{receipt.amount}</span>
          </div>
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
