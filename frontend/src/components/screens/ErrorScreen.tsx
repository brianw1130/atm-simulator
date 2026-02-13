import { useATMContext } from "../../hooks/useATMContext";

export function ErrorScreen() {
  const { state, dispatch } = useATMContext();

  return (
    <div className="screen-content" data-testid="error-screen">
      <div className="screen-content__header">
        <h2 style={{ color: "var(--screen-error)" }}>Error</h2>
      </div>
      <div className="screen-content__body">
        <p>{state.lastError ?? "An unexpected error occurred"}</p>
      </div>
      <div className="screen-content__footer">
        <button
          className="screen-btn"
          onClick={() => {
            dispatch({ type: "CLEAR_ERROR" });
            dispatch({ type: "GO_BACK" });
          }}
          data-testid="error-back-btn"
        >
          Back
        </button>
      </div>
    </div>
  );
}
