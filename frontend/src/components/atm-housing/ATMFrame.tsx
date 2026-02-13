import type { ReactNode } from "react";
import "./ATMFrame.css";

interface ATMFrameProps {
  children: ReactNode;
}

export function ATMFrame({ children }: ATMFrameProps) {
  return (
    <div className="atm-frame" data-testid="atm-frame">
      <div className="atm-header">
        <div className="atm-header__logo">ATM</div>
      </div>
      {children}
    </div>
  );
}
