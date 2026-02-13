export function LoadingOverlay() {
  return (
    <div className="loading-overlay" data-testid="loading-overlay">
      <p>Processing...</p>
      <p className="screen-text-dim">Please wait</p>
    </div>
  );
}
