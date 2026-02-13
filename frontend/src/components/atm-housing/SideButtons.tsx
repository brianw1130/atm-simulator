import "./SideButtons.css";

export interface SideButtonConfig {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

interface SideButtonsProps {
  side: "left" | "right";
  buttons: (SideButtonConfig | null)[];
}

/**
 * Renders 4 side buttons (soft keys) next to the ATM screen.
 * Pass null for empty button slots.
 */
export function SideButtons({ side, buttons }: SideButtonsProps) {
  // Ensure exactly 4 slots
  const slots = buttons.slice(0, 4);
  while (slots.length < 4) {
    slots.push(null);
  }

  return (
    <div
      className={`side-buttons side-buttons--${side}`}
      data-testid={`side-buttons-${side}`}
    >
      {slots.map((btn, i) => (
        <button
          key={`${side}-${String(i)}`}
          className={`side-button side-button--${side}`}
          onClick={btn?.onClick}
          disabled={!btn || btn.disabled}
          aria-label={btn?.label ?? `Empty ${side} button ${String(i + 1)}`}
          title={btn?.label}
          data-testid={
            btn ? `side-btn-${side}-${btn.label.toLowerCase().replace(/[\s$]/g, "-")}` : undefined
          }
        >
          {btn?.label && <span className="side-button__label">{btn.label}</span>}
        </button>
      ))}
    </div>
  );
}
