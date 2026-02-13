import { useCallback, useRef } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useATMContext } from "./hooks/useATMContext";
import { useIdleTimer } from "./hooks/useIdleTimer";
import { ATMFrame } from "./components/atm-housing/ATMFrame";
import { ScreenBezel } from "./components/atm-housing/ScreenBezel";
import {
  SideButtons,
  type SideButtonConfig,
} from "./components/atm-housing/SideButtons";
import { NumericKeypad } from "./components/atm-housing/NumericKeypad";
import { CardSlot } from "./components/atm-housing/CardSlot";
import { CashDispenser } from "./components/atm-housing/CashDispenser";
import { ReceiptPrinter } from "./components/atm-housing/ReceiptPrinter";
import { WelcomeScreen } from "./components/screens/WelcomeScreen";
import { PinEntryScreen } from "./components/screens/PinEntryScreen";
import { MainMenuScreen } from "./components/screens/MainMenuScreen";
import { BalanceInquiryScreen } from "./components/screens/BalanceInquiryScreen";
import { WithdrawalScreen } from "./components/screens/WithdrawalScreen";
import { WithdrawalConfirmScreen } from "./components/screens/WithdrawalConfirmScreen";
import { WithdrawalReceiptScreen } from "./components/screens/WithdrawalReceiptScreen";
import { DepositScreen } from "./components/screens/DepositScreen";
import { DepositReceiptScreen } from "./components/screens/DepositReceiptScreen";
import { TransferScreen } from "./components/screens/TransferScreen";
import { TransferConfirmScreen } from "./components/screens/TransferConfirmScreen";
import { TransferReceiptScreen } from "./components/screens/TransferReceiptScreen";
import { StatementScreen } from "./components/screens/StatementScreen";
import { PinChangeScreen } from "./components/screens/PinChangeScreen";
import { SessionTimeoutScreen } from "./components/screens/SessionTimeoutScreen";
import { ErrorScreen } from "./components/screens/ErrorScreen";
import { MaintenanceModeScreen } from "./components/screens/MaintenanceModeScreen";
import {
  screenVariants,
  screenVariantsReduced,
  overlayVariants,
  countdownPulse,
} from "./utils/motion";
import type { ATMScreen } from "./state/types";
import { logout as apiLogout } from "./api/endpoints";

const noopHandlers = {
  onDigit: () => {},
  onClear: () => {},
  onCancel: () => {},
  onEnter: () => {},
};

/** Resolve the active screen's keypad handlers at call time.
 *  Reading static properties lazily avoids stale refs caused by
 *  AnimatePresence delaying child mounts. */
function getScreenHandlers(
  screen: ATMScreen,
  pending: unknown,
) {
  switch (screen) {
    case "welcome":
      return WelcomeScreen.keypadHandlers;
    case "pin_entry":
      return PinEntryScreen.keypadHandlers;
    case "withdrawal":
      return WithdrawalScreen.keypadHandlers;
    case "deposit":
      return pending ? DepositScreen.keypadHandlers : noopHandlers;
    case "transfer":
      return TransferScreen.keypadHandlers;
    case "pin_change":
      return PinChangeScreen.keypadHandlers;
    default:
      return noopHandlers;
  }
}

export default function App() {
  const { state, dispatch } = useATMContext();
  const { showWarning, secondsLeft } = useIdleTimer();
  const reducedMotion = useReducedMotion();

  // Track current screen in a ref so keypad handlers can read it at
  // event time (after AnimatePresence has mounted the screen component).
  const screenRef = useRef(state.currentScreen);
  screenRef.current = state.currentScreen;
  const pendingRef = useRef(state.pendingTransaction);
  pendingRef.current = state.pendingTransaction;

  const keypadRef = useRef({
    onDigit: (d: string) => {
      getScreenHandlers(screenRef.current, pendingRef.current).onDigit(d);
    },
    onClear: () => {
      getScreenHandlers(screenRef.current, pendingRef.current).onClear();
    },
    onCancel: () => {
      getScreenHandlers(screenRef.current, pendingRef.current).onCancel();
    },
    onEnter: () => {
      getScreenHandlers(screenRef.current, pendingRef.current).onEnter();
    },
  });

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

  const handleBack = useCallback(() => {
    dispatch({ type: "GO_BACK" });
  }, [dispatch]);

  const handleAnotherTransaction = useCallback(() => {
    dispatch({ type: "NAVIGATE", screen: "main_menu" });
  }, [dispatch]);

  // Render the screen component for the current state
  const renderScreen = () => {
    switch (state.currentScreen) {
      case "welcome":
        return <WelcomeScreen />;
      case "pin_entry":
        return <PinEntryScreen />;
      case "main_menu":
        return <MainMenuScreen />;
      case "balance_inquiry":
        return <BalanceInquiryScreen />;
      case "withdrawal":
        return <WithdrawalScreen />;
      case "withdrawal_confirm":
        return <WithdrawalConfirmScreen />;
      case "withdrawal_receipt":
        return <WithdrawalReceiptScreen />;
      case "deposit":
        return <DepositScreen />;
      case "deposit_receipt":
        return <DepositReceiptScreen />;
      case "transfer":
        return <TransferScreen />;
      case "transfer_confirm":
        return <TransferConfirmScreen />;
      case "transfer_receipt":
        return <TransferReceiptScreen />;
      case "statement":
        return <StatementScreen />;
      case "pin_change":
        return <PinChangeScreen />;
      case "session_timeout":
        return <SessionTimeoutScreen />;
      case "error":
        return <ErrorScreen />;
      case "maintenance":
        return <MaintenanceModeScreen />;
    }
  };

  // Build side button config for left/right panels
  const buildSideButtons = (
    side: "left" | "right",
  ): (SideButtonConfig | null)[] => {
    switch (state.currentScreen) {
      case "main_menu": {
        const config =
          side === "left"
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

      case "balance_inquiry": {
        if (side === "left") {
          return state.accounts.map((acct) => ({
            label: acct.account_type === "CHECKING" ? "Checking" : "Savings",
            onClick: () =>
              dispatch({ type: "SELECT_ACCOUNT", accountId: acct.id }),
          }));
        }
        return [null, null, null, { label: "Back", onClick: handleBack }];
      }

      case "withdrawal": {
        if (side === "left") {
          return [
            {
              label: "$20",
              onClick: () => WithdrawalScreen.handleQuickAmount(2000),
            },
            {
              label: "$40",
              onClick: () => WithdrawalScreen.handleQuickAmount(4000),
            },
            {
              label: "$60",
              onClick: () => WithdrawalScreen.handleQuickAmount(6000),
            },
            {
              label: "$100",
              onClick: () => WithdrawalScreen.handleQuickAmount(10000),
            },
          ];
        }
        return [
          {
            label: "$200",
            onClick: () => WithdrawalScreen.handleQuickAmount(20000),
          },
          null,
          null,
          { label: "Back", onClick: handleBack },
        ];
      }

      case "withdrawal_confirm":
        if (side === "left") return [null, null, null, null];
        return [
          null,
          null,
          {
            label: "Confirm",
            onClick: () => void WithdrawalConfirmScreen.handleConfirm(),
          },
          { label: "Cancel", onClick: handleBack },
        ];

      case "withdrawal_receipt":
      case "deposit_receipt":
      case "transfer_receipt":
        if (side === "left") return [null, null, null, null];
        return [
          null,
          null,
          { label: "Another", onClick: handleAnotherTransaction },
          { label: "Done", onClick: () => void handleLogout() },
        ];

      case "deposit": {
        if (!state.pendingTransaction) {
          // Type selection phase
          if (side === "left") {
            return [
              {
                label: "Cash",
                onClick: () =>
                  dispatch({
                    type: "STAGE_TRANSACTION",
                    transaction: {
                      type: "deposit",
                      amountCents: 0,
                      depositType: "cash",
                    },
                  }),
              },
              {
                label: "Check",
                onClick: () =>
                  dispatch({
                    type: "STAGE_TRANSACTION",
                    transaction: {
                      type: "deposit",
                      amountCents: 0,
                      depositType: "check",
                    },
                  }),
              },
              null,
              null,
            ];
          }
          return [null, null, null, { label: "Back", onClick: handleBack }];
        }
        // Amount entry phase
        if (side === "left") return [null, null, null, null];
        return [null, null, null, { label: "Back", onClick: handleBack }];
      }

      case "transfer": {
        if (side === "left") {
          // Show own accounts as quick destinations, pad to 4
          const otherAccounts = state.accounts
            .filter((a) => a.id !== state.selectedAccountId)
            .map(
              (acct): SideButtonConfig => ({
                label:
                  acct.account_type === "CHECKING" ? "Checking" : "Savings",
                onClick: () =>
                  TransferScreen.setOwnAccountDestination(
                    acct.account_number,
                  ),
              }),
            );
          const padded: (SideButtonConfig | null)[] = [
            ...otherAccounts,
            null,
            null,
            null,
            null,
          ];
          return padded.slice(0, 4);
        }
        return [null, null, null, { label: "Back", onClick: handleBack }];
      }

      case "transfer_confirm":
        if (side === "left") return [null, null, null, null];
        return [
          null,
          null,
          {
            label: "Confirm",
            onClick: () => void TransferConfirmScreen.handleConfirm(),
          },
          { label: "Cancel", onClick: handleBack },
        ];

      case "statement": {
        if (side === "left") {
          return [
            {
              label: "7 Days",
              onClick: () => void StatementScreen.handleGenerate(7),
            },
            {
              label: "30 Days",
              onClick: () => void StatementScreen.handleGenerate(30),
            },
            {
              label: "90 Days",
              onClick: () => void StatementScreen.handleGenerate(90),
            },
            null,
          ];
        }
        return [null, null, null, { label: "Back", onClick: handleBack }];
      }

      case "pin_change":
        if (side === "left") return [null, null, null, null];
        return [null, null, null, { label: "Cancel", onClick: handleBack }];

      default:
        return [null, null, null, null];
    }
  };

  const isCardInserted = state.currentScreen !== "welcome";
  const isKeypadActive =
    (state.currentScreen === "welcome" ||
      state.currentScreen === "pin_entry" ||
      state.currentScreen === "withdrawal" ||
      (state.currentScreen === "deposit" &&
        state.pendingTransaction !== null) ||
      state.currentScreen === "transfer" ||
      state.currentScreen === "pin_change") &&
    !state.isLoading;

  // Derive animation flags from state — no reducer changes needed
  const isCashDispensing =
    state.currentScreen === "withdrawal_receipt" &&
    state.lastReceipt?.receiptType === "withdrawal";

  const isReceiptPrinting =
    state.currentScreen === "withdrawal_receipt" ||
    state.currentScreen === "deposit_receipt" ||
    state.currentScreen === "transfer_receipt";

  const billCount =
    isCashDispensing && state.lastReceipt?.receiptType === "withdrawal"
      ? Math.min(state.lastReceipt.denominations.total_bills, 5)
      : 0;

  const activeVariants = reducedMotion ? screenVariantsReduced : screenVariants;

  return (
    <ATMFrame>
      <div className="atm-screen-section">
        <SideButtons side="left" buttons={buildSideButtons("left")} />
        <ScreenBezel>
          <AnimatePresence mode="wait">
            <motion.div
              key={state.currentScreen}
              variants={activeVariants}
              initial="enter"
              animate="center"
              exit="exit"
              style={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
              }}
            >
              {renderScreen()}
            </motion.div>
          </AnimatePresence>
          <AnimatePresence>
            {showWarning && (
              <motion.div
                className="idle-warning"
                data-testid="idle-warning"
                variants={!reducedMotion ? overlayVariants : undefined}
                initial={!reducedMotion ? "hidden" : undefined}
                animate={!reducedMotion ? "visible" : undefined}
                exit={!reducedMotion ? "exit" : undefined}
              >
                <p>Session expires in</p>
                <motion.p
                  className="idle-warning__countdown"
                  key={secondsLeft}
                  variants={!reducedMotion ? countdownPulse : undefined}
                  initial={!reducedMotion ? "initial" : undefined}
                  animate={!reducedMotion ? "animate" : undefined}
                >
                  {secondsLeft}s
                </motion.p>
                <p className="screen-text-dim">
                  Press any key to continue
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </ScreenBezel>
        <SideButtons side="right" buttons={buildSideButtons("right")} />
      </div>

      <div className="atm-slots-section">
        <ReceiptPrinter printing={isReceiptPrinting} />
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
        <CashDispenser dispensing={isCashDispensing} billCount={billCount} />
      </div>
    </ATMFrame>
  );
}
