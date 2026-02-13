import { useReducedMotion, motion, AnimatePresence } from "framer-motion";
import { cashFlapVariants, cashBillVariants } from "../../utils/motion";
import "./CashDispenser.css";

interface CashDispenserProps {
  dispensing?: boolean;
  billCount?: number;
}

const MAX_VISUAL_BILLS = 5;

export function CashDispenser({
  dispensing = false,
  billCount = 0,
}: CashDispenserProps) {
  const reducedMotion = useReducedMotion();
  const visualBills = Math.min(billCount, MAX_VISUAL_BILLS);

  return (
    <div data-testid="cash-dispenser">
      <div className="cash-dispenser">
        <motion.div
          className="cash-dispenser__flap"
          variants={!reducedMotion ? cashFlapVariants : undefined}
          animate={dispensing && !reducedMotion ? "open" : "closed"}
          style={{ transformOrigin: "top center" }}
          data-testid="cash-dispenser-flap"
        />
        <AnimatePresence>
          {dispensing && !reducedMotion && visualBills > 0 && (
            <div className="cash-dispenser__bills" data-testid="cash-dispenser-bills">
              {Array.from({ length: visualBills }, (_, i) => (
                <motion.div
                  key={`bill-${String(i)}`}
                  className="cash-dispenser__bill"
                  variants={cashBillVariants(i)}
                  initial="hidden"
                  animate="visible"
                  exit="withdrawn"
                  data-testid={`cash-bill-${String(i)}`}
                />
              ))}
            </div>
          )}
        </AnimatePresence>
      </div>
      <div className="cash-dispenser__label">Cash</div>
    </div>
  );
}
