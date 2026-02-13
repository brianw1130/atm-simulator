import type { ReactNode } from "react";
import "./ScreenBezel.css";

interface ScreenBezelProps {
  children: ReactNode;
}

export function ScreenBezel({ children }: ScreenBezelProps) {
  return (
    <div className="screen-bezel" data-testid="screen-bezel">
      <div className="screen-display" data-testid="screen-display">
        {children}
      </div>
    </div>
  );
}
