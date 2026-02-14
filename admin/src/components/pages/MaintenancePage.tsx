import { useCallback, useState } from "react";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { usePolling } from "../../hooks/usePolling";
import * as api from "../../api/endpoints";

export function MaintenancePage() {
  const fetchStatus = useCallback(() => api.getMaintenanceStatus(), []);
  const { data: status, isLoading, error, refresh } = usePolling(fetchStatus, 10_000);
  const [reason, setReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const handleEnable = async () => {
    setActionLoading(true);
    try {
      await api.enableMaintenance(reason || undefined);
      setReason("");
      await refresh();
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisable = async () => {
    setActionLoading(true);
    try {
      await api.disableMaintenance();
      await refresh();
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading || !status) return <LoadingSpinner />;
  if (error) return <div className="page-error">Error: {error}</div>;

  return (
    <div className="maintenance-page">
      <div className="maintenance-status">
        <div
          className={`maintenance-indicator ${status.enabled ? "maintenance-indicator--on" : "maintenance-indicator--off"}`}
        >
          <span className="maintenance-indicator__label">
            Maintenance Mode
          </span>
          <span className="maintenance-indicator__value">
            {status.enabled ? "ON" : "OFF"}
          </span>
        </div>

        {status.enabled && status.reason && (
          <p className="maintenance-reason">
            Reason: {status.reason}
          </p>
        )}

        {!status.enabled && (
          <div className="maintenance-controls">
            <input
              type="text"
              className="maintenance-input"
              placeholder="Reason for maintenance (optional)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              disabled={actionLoading}
            />
            <button
              className="btn btn--danger"
              onClick={() => void handleEnable()}
              disabled={actionLoading}
            >
              {actionLoading ? "Enabling..." : "Enable Maintenance Mode"}
            </button>
            <p className="maintenance-warning">
              Warning: Enabling maintenance mode will prevent all ATM
              transactions.
            </p>
          </div>
        )}

        {status.enabled && (
          <div className="maintenance-controls">
            <button
              className="btn btn--success"
              onClick={() => void handleDisable()}
              disabled={actionLoading}
            >
              {actionLoading ? "Disabling..." : "Disable Maintenance Mode"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
