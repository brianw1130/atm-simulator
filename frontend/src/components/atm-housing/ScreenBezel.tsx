import type { ReactNode } from "react";
import "./ScreenBezel.css";

interface ScreenBezelProps {
  children: ReactNode;
  leftLabels?: (string | null)[];
  rightLabels?: (string | null)[];
}

export function ScreenBezel({ children, leftLabels, rightLabels }: ScreenBezelProps) {
  return (
    <div className="screen-bezel" data-testid="screen-bezel">
      <div className="screen-display" data-testid="screen-display">
        {leftLabels && (
          <div className="screen-labels screen-labels--left">
            {leftLabels.map((label, i) => (
              <span
                key={`l-${String(i)}`}
                className={`screen-label-item ${label ? "" : "screen-label-item--empty"}`}
              >
                {label ? `${label} ◄` : ""}
              </span>
            ))}
          </div>
        )}
        {children}
        {rightLabels && (
          <div className="screen-labels screen-labels--right">
            {rightLabels.map((label, i) => (
              <span
                key={`r-${String(i)}`}
                className={`screen-label-item ${label ? "" : "screen-label-item--empty"}`}
              >
                {label ? `► ${label}` : ""}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
