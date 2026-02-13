import type { MiniStatementEntry } from "../../api/types";

interface MiniStatementProps {
  transactions: MiniStatementEntry[];
}

export function MiniStatement({ transactions }: MiniStatementProps) {
  if (transactions.length === 0) {
    return (
      <p className="screen-text-dim" data-testid="mini-statement-empty">
        No recent transactions
      </p>
    );
  }

  return (
    <div className="mini-statement" data-testid="mini-statement">
      {transactions.map((tx, i) => (
        <div key={i} className="mini-statement__row">
          <span className="mini-statement__date">{tx.date}</span>
          <span className="mini-statement__desc">{tx.description}</span>
          <span
            className={`mini-statement__amount ${tx.amount.startsWith("-") ? "amount-negative" : "amount-positive"}`}
          >
            {tx.amount}
          </span>
        </div>
      ))}
    </div>
  );
}
