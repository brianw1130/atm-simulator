import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { overlayVariants, spinnerTransition } from "../../utils/motion";

interface LoadingOverlayProps {
  visible?: boolean;
}

export function LoadingOverlay({ visible = true }: LoadingOverlayProps) {
  const reducedMotion = useReducedMotion();

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="loading-overlay"
          data-testid="loading-overlay"
          variants={!reducedMotion ? overlayVariants : undefined}
          initial={!reducedMotion ? "hidden" : undefined}
          animate={!reducedMotion ? "visible" : undefined}
          exit={!reducedMotion ? "exit" : undefined}
        >
          <div className="loading-spinner" data-testid="loading-spinner">
            <motion.div
              className="loading-spinner__circle"
              animate={!reducedMotion ? { rotate: 360 } : undefined}
              transition={!reducedMotion ? spinnerTransition : undefined}
            />
          </div>
          <p>Processing...</p>
          <p className="screen-text-dim">Please wait</p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
