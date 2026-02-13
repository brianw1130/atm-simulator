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
});

describe("CashDispenser", () => {
  it("renders the cash dispenser", () => {
    render(<CashDispenser />);
    expect(screen.getByTestId("cash-dispenser")).toBeInTheDocument();
  });
});

describe("ReceiptPrinter", () => {
  it("renders the receipt printer", () => {
    render(<ReceiptPrinter />);
    expect(screen.getByTestId("receipt-printer")).toBeInTheDocument();
  });
});
