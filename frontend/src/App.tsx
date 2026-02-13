import { useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useATMContext } from "./hooks/useATMContext";
import { ATMFrame } from "./components/atm-housing/ATMFrame";
import { ScreenBezel } from "./components/atm-housing/ScreenBezel";
import { SideButtons, type SideButtonConfig } from "./components/atm-housing/SideButtons";
import { NumericKeypad } from "./components/atm-housing/NumericKeypad";
import { CardSlot } from "./components/atm-housing/CardSlot";
import { CashDispenser } from "./components/atm-housing/CashDispenser";
import { ReceiptPrinter } from "./components/atm-housing/ReceiptPrinter";
import { WelcomeScreen } from "./components/screens/WelcomeScreen";
import { PinEntryScreen } from "./components/screens/PinEntryScreen";
import { MainMenuScreen } from "./components/screens/MainMenuScreen";
import { SessionTimeoutScreen } from "./components/screens/SessionTimeoutScreen";
import { ErrorScreen } from "./components/screens/ErrorScreen";
import { MaintenanceModeScreen } from "./components/screens/MaintenanceModeScreen";
import type { ATMScreen } from "./state/types";
import { logout as apiLogout } from "./api/endpoints";

const screenTransition = {
  enter: { opacity: 0, x: 20 },
  center: { opacity: 1, x: 0, transition: { duration: 0.2 } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.15 } },
};

export default function App() {
  const { state, dispatch } = useATMContext();
  const keypadRef = useRef({
    onDigit: (_: string) => { /* noop */ },
    onClear: () => { /* noop */ },
    onCancel: () => { /* noop */ },
    onEnter: () => { /* noop */ },
  });

  // Navigate via side button
  const navigateTo = useCallback(
    (screen: ATMScreen) => {
      dispatch({ type: "NAVIGATE", screen });
    },
    [dispatch],
  );

  const handleLogout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      // Ignore logout errors
    }
    dispatch({ type: "LOGOUT" });
  }, [dispatch]);

  // Determine which screen to render
  const renderScreen = () => {
    switch (state.currentScreen) {
      case "welcome":
        return <WelcomeScreen />;
      case "pin_entry":
        return <PinEntryScreen />;
      case "main_menu":
        return <MainMenuScreen />;
      case "session_timeout":
        return <SessionTimeoutScreen />;
      case "error":
        return <ErrorScreen />;
      case "maintenance":
        return <MaintenanceModeScreen />;
      default:
        // Placeholder for Sprint 2 screens
        return (
          <div className="screen-content" data-testid="placeholder-screen">
            <div className="screen-content__header">
              <h2>{state.currentScreen.replace(/_/g, " ").toUpperCase()}</h2>
            </div>
            <div className="screen-content__body">
              <p className="screen-text-dim">Coming in Sprint 2</p>
            </div>
          </div>
        );
    }
  };

  // Wire keypad to current screen
  if (state.currentScreen === "pin_entry") {
    keypadRef.current = PinEntryScreen.keypadHandlers;
  } else if (state.currentScreen === "welcome") {
    keypadRef.current = {
      onDigit: () => {},
      onClear: () => {},
      onCancel: () => {},
      onEnter: () => {},
    };
  }

  // Build side buttons based on current screen
  const buildSideButtons = (
    side: "left" | "right",
  ): (SideButtonConfig | null)[] => {
    if (state.currentScreen === "main_menu") {
      const config = side === "left"
        ? MainMenuScreen.sideButtons.left
        : MainMenuScreen.sideButtons.right;

      return config.map((item) => {
        if (!item) return null;
        return {
          label: item.label,
          onClick: item.screen
            ? () => navigateTo(item.screen)
            : () => void handleLogout(),
        };
      });
    }

    // Default: no side buttons active
    return [null, null, null, null];
  };

  const isCardInserted = state.currentScreen !== "welcome";
  const isKeypadActive = state.currentScreen === "pin_entry";

  return (
    <ATMFrame>
      <div className="atm-screen-section">
        <SideButtons side="left" buttons={buildSideButtons("left")} />
        <ScreenBezel>
          <AnimatePresence mode="wait">
            <motion.div
              key={state.currentScreen}
              variants={screenTransition}
              initial="enter"
              animate="center"
              exit="exit"
              style={{ height: "100%", display: "flex", flexDirection: "column" }}
            >
              {renderScreen()}
            </motion.div>
          </AnimatePresence>
        </ScreenBezel>
        <SideButtons side="right" buttons={buildSideButtons("right")} />
      </div>

      <div className="atm-slots-section">
        <ReceiptPrinter />
        <CardSlot active={isCardInserted} />
      </div>

      <div className="atm-bottom-panel">
        <NumericKeypad
          onDigit={(d) => keypadRef.current.onDigit(d)}
          onClear={() => keypadRef.current.onClear()}
          onCancel={() => keypadRef.current.onCancel()}
          onEnter={() => keypadRef.current.onEnter()}
          disabled={!isKeypadActive || state.isLoading}
        />
        <CashDispenser />
      </div>
    </ATMFrame>
  );
}
