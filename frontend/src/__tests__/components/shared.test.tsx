import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingOverlay } from "../../components/shared/LoadingOverlay";
import { MiniStatement } from "../../components/shared/MiniStatement";
import type { MiniStatementEntry } from "../../api/types";

describe("LoadingOverlay", () => {
  it("renders processing message", () => {
    render(<LoadingOverlay />);
    expect(screen.getByTestId("loading-overlay")).toBeInTheDocument();
    expect(screen.getByText("Processing...")).toBeInTheDocument();
    expect(screen.getByText("Please wait")).toBeInTheDocument();
  });
});

describe("MiniStatement", () => {
  const transactions: MiniStatementEntry[] = [
    {
      date: "2024-01-15",
      description: "ATM Withdrawal",
      amount: "-$100.00",
      balance_after: "$4,900.00",
    },
    {
      date: "2024-01-14",
      description: "Deposit",
      amount: "$500.00",
      balance_after: "$5,000.00",
    },
  ];

  it("renders transactions", () => {
    render(<MiniStatement transactions={transactions} />);
    expect(screen.getByTestId("mini-statement")).toBeInTheDocument();
    expect(screen.getByText("2024-01-15")).toBeInTheDocument();
    expect(screen.getByText("ATM Withdrawal")).toBeInTheDocument();
    expect(screen.getByText("-$100.00")).toBeInTheDocument();
  });

  it("applies negative class for negative amounts", () => {
    render(<MiniStatement transactions={transactions} />);
    const negativeAmount = screen.getByText("-$100.00");
    expect(negativeAmount).toHaveClass("amount-negative");
  });

  it("applies positive class for positive amounts", () => {
    render(<MiniStatement transactions={transactions} />);
    const positiveAmount = screen.getByText("$500.00");
    expect(positiveAmount).toHaveClass("amount-positive");
  });

  it("shows empty message when no transactions", () => {
    render(<MiniStatement transactions={[]} />);
    expect(screen.getByTestId("mini-statement-empty")).toBeInTheDocument();
    expect(screen.getByText("No recent transactions")).toBeInTheDocument();
  });
});
