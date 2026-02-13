import { useReducedMotion, motion, AnimatePresence } from "framer-motion";
import { receiptVariants } from "../../utils/motion";
import "./ReceiptPrinter.css";

interface ReceiptPrinterProps {
  printing?: boolean;
}

export function ReceiptPrinter({ printing = false }: ReceiptPrinterProps) {
  const reducedMotion = useReducedMotion();

  return (
    <div data-testid="receipt-printer">
      <div className="receipt-printer">
        <AnimatePresence mode="wait">
          {printing && !reducedMotion && (
            <motion.div
              className="receipt-printer__paper"
              data-testid="receipt-paper"
              variants={receiptVariants}
              initial="hidden"
              animate="printing"
              exit="retracted"
            />
          )}
        </AnimatePresence>
      </div>
      <div className="receipt-printer__label">Receipt</div>
    </div>
  );
}
