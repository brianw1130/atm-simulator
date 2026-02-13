import "./CashDispenser.css";

export function CashDispenser() {
  return (
    <div data-testid="cash-dispenser">
      <div className="cash-dispenser">
        <div className="cash-dispenser__flap" />
      </div>
      <div className="cash-dispenser__label">Cash</div>
    </div>
  );
}
