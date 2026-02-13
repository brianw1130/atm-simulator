import "./CardSlot.css";

interface CardSlotProps {
  active?: boolean;
}

export function CardSlot({ active = false }: CardSlotProps) {
  return (
    <div data-testid="card-slot">
      <div className="card-slot">
        <div
          className={`card-slot__indicator ${active ? "" : "card-slot__indicator--inactive"}`}
        />
      </div>
      <div className="card-slot__label">Insert Card</div>
    </div>
  );
}
