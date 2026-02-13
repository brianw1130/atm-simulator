/**
 * Shared Framer Motion presets for ATM animations.
 *
 * All animations use only `transform` and `opacity` (GPU-composited).
 * Reduced-motion users get instant transitions via `useReducedMotion()`.
 */
import type { Transition, Variants } from "framer-motion";

/* ------------------------------------------------------------------ */
/*  Spring presets                                                     */
/* ------------------------------------------------------------------ */

export const springs = {
  /** Card insertion: stiff, quick settle (~0.5s) */
  card: { type: "spring", stiffness: 300, damping: 30 } satisfies Transition,

  /** Cash dispensing: slightly softer (~0.6s) */
  cash: { type: "spring", stiffness: 200, damping: 25 } satisfies Transition,

  /** Screen transitions: responsive with slight overshoot */
  screen: {
    type: "spring",
    stiffness: 300,
    damping: 30,
    mass: 0.8,
  } satisfies Transition,
};

/* ------------------------------------------------------------------ */
/*  Screen transition variants (enhanced from Sprint 2)                */
/* ------------------------------------------------------------------ */

export const screenVariants: Variants = {
  enter: { opacity: 0, x: 30, scale: 0.98 },
  center: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: springs.screen,
  },
  exit: {
    opacity: 0,
    x: -30,
    scale: 0.98,
    transition: { duration: 0.15 },
  },
};

/** Reduced-motion variants: instant, no spatial movement. */
export const screenVariantsReduced: Variants = {
  enter: { opacity: 0 },
  center: { opacity: 1, transition: { duration: 0.01 } },
  exit: { opacity: 0, transition: { duration: 0.01 } },
};

/* ------------------------------------------------------------------ */
/*  Card insertion / ejection                                          */
/* ------------------------------------------------------------------ */

export const cardVariants: Variants = {
  hidden: { x: 60, opacity: 0 },
  inserted: {
    x: -20,
    opacity: 1,
    transition: springs.card,
  },
  ejected: {
    x: 60,
    opacity: 0,
    transition: { duration: 0.3, ease: "easeIn" },
  },
};

/* ------------------------------------------------------------------ */
/*  Cash dispensing                                                     */
/* ------------------------------------------------------------------ */

export const cashFlapVariants: Variants = {
  closed: { rotateX: 0 },
  open: {
    rotateX: -15,
    transition: { duration: 0.2, ease: "easeOut" },
  },
};

/** Build per-bill variants with staggered delay. */
export function cashBillVariants(index: number): Variants {
  return {
    hidden: { y: -10, opacity: 0 },
    visible: {
      y: 8 + index * 3,
      opacity: 1,
      transition: {
        ...springs.cash,
        delay: 0.3 + index * 0.1,
      },
    },
    withdrawn: {
      y: -10,
      opacity: 0,
      transition: { duration: 0.2 },
    },
  };
}

/* ------------------------------------------------------------------ */
/*  Receipt printing                                                   */
/* ------------------------------------------------------------------ */

export const receiptVariants: Variants = {
  hidden: { y: 0, scaleY: 0, opacity: 0, transformOrigin: "bottom" },
  printing: {
    y: -35,
    scaleY: 1,
    opacity: 1,
    transformOrigin: "bottom",
    transition: { duration: 0.8, ease: "easeOut" },
  },
  retracted: {
    y: 0,
    scaleY: 0,
    opacity: 0,
    transformOrigin: "bottom",
    transition: { duration: 0.3, ease: "easeIn" },
  },
};

/* ------------------------------------------------------------------ */
/*  Overlay fade                                                       */
/* ------------------------------------------------------------------ */

export const overlayVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.2, ease: "easeOut" },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: { duration: 0.15, ease: "easeIn" },
  },
};

/* ------------------------------------------------------------------ */
/*  Idle warning countdown pulse                                       */
/* ------------------------------------------------------------------ */

export const countdownPulse: Variants = {
  initial: { scale: 1.2, opacity: 0.7 },
  animate: {
    scale: 1,
    opacity: 1,
    transition: { type: "spring", stiffness: 400, damping: 15 },
  },
};

/* ------------------------------------------------------------------ */
/*  Loading spinner                                                    */
/* ------------------------------------------------------------------ */

export const spinnerTransition: Transition = {
  repeat: Infinity,
  duration: 0.8,
  ease: "linear",
};
