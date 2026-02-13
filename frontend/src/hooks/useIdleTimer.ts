import { useEffect, useRef, useState, useCallback } from "react";
import { useATMContext } from "./useATMContext";
import { refreshSession } from "../api/endpoints";
import { SESSION_TIMEOUT_MS } from "../state/types";

const WARNING_THRESHOLD_MS = 30_000;
const THROTTLE_MS = 1_000;
const SERVER_REFRESH_INTERVAL_MS = 60_000;

const ACTIVITY_EVENTS: readonly string[] = [
  "mousedown",
  "keydown",
  "touchstart",
];

const ACTIVE_SCREENS: readonly string[] = [
  "main_menu",
  "balance_inquiry",
  "withdrawal",
  "withdrawal_confirm",
  "withdrawal_receipt",
  "deposit",
  "deposit_receipt",
  "transfer",
  "transfer_confirm",
  "transfer_receipt",
  "statement",
  "pin_change",
  "error",
];

interface IdleTimerResult {
  showWarning: boolean;
  secondsLeft: number;
}

export function useIdleTimer(): IdleTimerResult {
  const { state, dispatch } = useATMContext();
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const warningTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastResetRef = useRef(0);
  const lastServerRefreshRef = useRef(Date.now());

  const [showWarning, setShowWarning] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);

  const clearAllTimers = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
    if (countdownRef.current) clearInterval(countdownRef.current);
    timeoutRef.current = null;
    warningTimeoutRef.current = null;
    countdownRef.current = null;
  }, []);

  const resetTimer = useCallback(() => {
    const now = Date.now();
    if (now - lastResetRef.current < THROTTLE_MS) return;
    lastResetRef.current = now;

    clearAllTimers();
    setShowWarning(false);

    dispatch({ type: "REFRESH_SESSION_TIMER" });

    if (now - lastServerRefreshRef.current > SERVER_REFRESH_INTERVAL_MS) {
      lastServerRefreshRef.current = now;
      refreshSession().catch(() => {
        /* ignore refresh errors */
      });
    }

    warningTimeoutRef.current = setTimeout(() => {
      setShowWarning(true);
      setSecondsLeft(Math.floor(WARNING_THRESHOLD_MS / 1000));
      countdownRef.current = setInterval(() => {
        setSecondsLeft((prev) => {
          if (prev <= 1) {
            if (countdownRef.current) clearInterval(countdownRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }, SESSION_TIMEOUT_MS - WARNING_THRESHOLD_MS);

    timeoutRef.current = setTimeout(() => {
      dispatch({ type: "SESSION_TIMEOUT" });
    }, SESSION_TIMEOUT_MS);
  }, [dispatch, clearAllTimers]);

  useEffect(() => {
    if (
      !state.sessionId ||
      !ACTIVE_SCREENS.includes(state.currentScreen)
    ) {
      clearAllTimers();
      setShowWarning(false);
      return;
    }

    for (const event of ACTIVITY_EVENTS) {
      window.addEventListener(event, resetTimer);
    }

    resetTimer();

    return () => {
      for (const event of ACTIVITY_EVENTS) {
        window.removeEventListener(event, resetTimer);
      }
      clearAllTimers();
    };
  }, [state.sessionId, state.currentScreen, resetTimer, clearAllTimers]);

  return { showWarning, secondsLeft };
}
