import { useATMContext } from "../../hooks/useATMContext";

export function SessionTimeoutScreen() {
  const { dispatch } = useATMContext();

  return (
    <div className="screen-content" data-testid="session-timeout-screen">
      <div className="screen-content__header">
        <h2>Session Expired</h2>
      </div>
      <div className="screen-content__body">
        <p>Your session has timed out</p>
        <p>due to inactivity.</p>
        <p className="screen-text-dim" style={{ marginTop: "16px" }}>
          Please insert your card to start a new session.
        </p>
      </div>
      <div className="screen-content__footer">
        <button
          className="screen-btn"
          onClick={() => dispatch({ type: "LOGOUT" })}
          data-testid="start-over-btn"
        >
          Start Over
        </button>
      </div>
    </div>
  );
}
