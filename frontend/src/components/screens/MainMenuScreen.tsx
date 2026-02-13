import { useATMContext } from "../../hooks/useATMContext";

/** Placeholder main menu — will be fully built in Sprint 2. */
export function MainMenuScreen() {
  const { state, dispatch } = useATMContext();

  const handleLogout = () => {
    sessionStorage.removeItem("atm_session_id");
    dispatch({ type: "LOGOUT" });
  };

  return (
    <div className="screen-content" data-testid="main-menu-screen">
      <div className="screen-content__header">
        <h2>Main Menu</h2>
        <p>Welcome, {state.customerName ?? "Customer"}</p>
      </div>
      <div className="screen-content__body">
        <p className="screen-text-dim">Select a transaction</p>
        <p className="screen-text-dim">using the side buttons</p>
      </div>
      <div className="screen-content__footer">
        <button
          className="screen-btn"
          onClick={handleLogout}
          data-testid="logout-btn"
        >
          Logout
        </button>
      </div>
    </div>
  );
}

/** Side button configuration for the main menu. */
MainMenuScreen.sideButtons = {
  left: [
    { label: "Balance", screen: "balance_inquiry" as const },
    { label: "Withdraw", screen: "withdrawal" as const },
    { label: "Deposit", screen: "deposit" as const },
    { label: "Transfer", screen: "transfer" as const },
  ],
  right: [
    { label: "Statement", screen: "statement" as const },
    { label: "PIN Change", screen: "pin_change" as const },
    null,
    { label: "Logout", screen: null },
  ],
};
