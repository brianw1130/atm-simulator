export function MaintenanceModeScreen() {
  return (
    <div className="screen-content" data-testid="maintenance-screen">
      <div className="screen-content__header">
        <h2 style={{ color: "var(--screen-error)" }}>Out of Service</h2>
      </div>
      <div className="screen-content__body">
        <p>This ATM is temporarily</p>
        <p>unavailable for maintenance.</p>
        <p className="screen-text-dim" style={{ marginTop: "16px" }}>
          Please try again later.
        </p>
      </div>
    </div>
  );
}
