import { useReducedMotion, motion, AnimatePresence } from "framer-motion";
import { cardVariants } from "../../utils/motion";
import "./CardSlot.css";

interface CardSlotProps {
  active?: boolean;
}

export function CardSlot({ active = false }: CardSlotProps) {
  const reducedMotion = useReducedMotion();

  return (
    <div data-testid="card-slot">
      <div className="card-slot">
        <AnimatePresence mode="wait">
          {active && !reducedMotion && (
            <motion.div
              className="card-slot__card"
              data-testid="card-slot-card"
              variants={cardVariants}
              initial="hidden"
              animate="inserted"
              exit="ejected"
            />
          )}
        </AnimatePresence>
        <div
          className={`card-slot__indicator ${active ? "" : "card-slot__indicator--inactive"}`}
          data-testid="card-slot-indicator"
        />
      </div>
      <div className="card-slot__label">Insert Card</div>
    </div>
  );
}
