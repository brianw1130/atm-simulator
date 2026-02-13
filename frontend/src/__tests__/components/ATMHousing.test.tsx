import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ATMFrame } from "../../components/atm-housing/ATMFrame";
import { ScreenBezel } from "../../components/atm-housing/ScreenBezel";
import { CardSlot } from "../../components/atm-housing/CardSlot";
import { CashDispenser } from "../../components/atm-housing/CashDispenser";
import { ReceiptPrinter } from "../../components/atm-housing/ReceiptPrinter";

describe("ATMFrame", () => {
  it("renders children inside the frame", () => {
    render(
      <ATMFrame>
        <div data-testid="child">Hello</div>
      </ATMFrame>,
    );
    expect(screen.getByTestId("atm-frame")).toBeInTheDocument();
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  it("displays ATM logo", () => {
    render(<ATMFrame><span /></ATMFrame>);
    expect(screen.getByText("ATM")).toBeInTheDocument();
  });
});

describe("ScreenBezel", () => {
  it("renders children inside the display", () => {
    render(
      <ScreenBezel>
        <div data-testid="screen-child">Content</div>
      </ScreenBezel>,
    );
    expect(screen.getByTestId("screen-bezel")).toBeInTheDocument();
    expect(screen.getByTestId("screen-display")).toBeInTheDocument();
    expect(screen.getByTestId("screen-child")).toBeInTheDocument();
  });
});

describe("CardSlot", () => {
  it("renders with inactive state by default", () => {
    render(<CardSlot active={false} />);
    expect(screen.getByTestId("card-slot")).toBeInTheDocument();
  });

  it("renders with active state", () => {
    render(<CardSlot active={true} />);
    expect(screen.getByTestId("card-slot")).toBeInTheDocument();
  });

  it("shows indicator with inactive class when not active", () => {
    render(<CardSlot active={false} />);
    const indicator = screen.getByTestId("card-slot-indicator");
    expect(indicator).toHaveClass("card-slot__indicator--inactive");
  });

  it("shows indicator without inactive class when active", () => {
    render(<CardSlot active={true} />);
    const indicator = screen.getByTestId("card-slot-indicator");
    expect(indicator).not.toHaveClass("card-slot__indicator--inactive");
  });

  it("displays Insert Card label", () => {
    render(<CardSlot />);
    expect(screen.getByText("Insert Card")).toBeInTheDocument();
  });
});

describe("CashDispenser", () => {
  it("renders the cash dispenser", () => {
    render(<CashDispenser />);
    expect(screen.getByTestId("cash-dispenser")).toBeInTheDocument();
  });

  it("renders flap element", () => {
    render(<CashDispenser />);
    expect(screen.getByTestId("cash-dispenser-flap")).toBeInTheDocument();
  });

  it("does not render bills when not dispensing", () => {
    render(<CashDispenser dispensing={false} billCount={5} />);
    expect(screen.queryByTestId("cash-dispenser-bills")).not.toBeInTheDocument();
  });

  it("displays Cash label", () => {
    render(<CashDispenser />);
    expect(screen.getByText("Cash")).toBeInTheDocument();
  });

  it("accepts dispensing and billCount props", () => {
    render(<CashDispenser dispensing={true} billCount={3} />);
    expect(screen.getByTestId("cash-dispenser")).toBeInTheDocument();
  });
});

describe("ReceiptPrinter", () => {
  it("renders the receipt printer", () => {
    render(<ReceiptPrinter />);
    expect(screen.getByTestId("receipt-printer")).toBeInTheDocument();
  });

  it("displays Receipt label", () => {
    render(<ReceiptPrinter />);
    expect(screen.getByText("Receipt")).toBeInTheDocument();
  });

  it("does not render paper when not printing", () => {
    render(<ReceiptPrinter printing={false} />);
    expect(screen.queryByTestId("receipt-paper")).not.toBeInTheDocument();
  });

  it("accepts printing prop", () => {
    render(<ReceiptPrinter printing={true} />);
    expect(screen.getByTestId("receipt-printer")).toBeInTheDocument();
  });
});
