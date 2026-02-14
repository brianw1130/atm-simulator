import { useRef, useState } from "react";
import { StatsCard } from "../shared/StatsCard";
import { DataTable } from "../shared/DataTable";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { NotificationToast } from "../shared/Notification";
import { ConfirmDialog } from "../shared/ConfirmDialog";
import { usePolling } from "../../hooks/usePolling";
import { useNotification } from "../../hooks/useNotification";
import * as api from "../../api/endpoints";
import type { AdminAccount, AuditLogEntry, MaintenanceStatus } from "../../api/types";

interface DashboardData {
  accounts: AdminAccount[];
  recentActivity: AuditLogEntry[];
  maintenance: MaintenanceStatus;
}

async function fetchDashboardData(): Promise<DashboardData> {
  const [accounts, recentActivity, maintenance] = await Promise.all([
    api.getAccounts(),
    api.getAuditLogs(10),
    api.getMaintenanceStatus(),
  ]);
  return { accounts, recentActivity, maintenance };
}

const activityColumns = [
  {
    key: "time",
    header: "Time",
    render: (row: AuditLogEntry) => {
      const date = new Date(row.created_at);
      return date.toLocaleString();
    },
  },
  {
    key: "event",
    header: "Event",
    render: (row: AuditLogEntry) => row.event_type,
  },
  {
    key: "details",
    header: "Details",
    render: (row: AuditLogEntry) => {
      const text = JSON.stringify(row.details);
      return text.length > 80 ? text.slice(0, 80) + "..." : text;
    },
  },
];

export function DashboardPage() {
  const { data, isLoading, error, refresh } = usePolling(fetchDashboardData, 30_000);
  const { notification, showSuccess, showError, dismiss } = useNotification();
  const [importFile, setImportFile] = useState<File | null>(null);
  const [conflictStrategy, setConflictStrategy] = useState<"skip" | "replace">("skip");
  const [showImportConfirm, setShowImportConfirm] = useState(false);
  const [importLoading, setImportLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = async () => {
    setExportLoading(true);
    try {
      const blob = await api.exportSnapshot();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "atm-snapshot.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showSuccess("Snapshot exported successfully");
    } catch {
      showError("Failed to export snapshot");
    } finally {
      setExportLoading(false);
    }
  };

  const handleImportConfirm = async () => {
    if (!importFile) return;
    setImportLoading(true);
    try {
      const stats = await api.importSnapshot(importFile, conflictStrategy);
      const created = (stats["customers_created"] ?? 0) + (stats["accounts_created"] ?? 0);
      showSuccess(`Import complete: ${String(created)} entities created`);
      setShowImportConfirm(false);
      setImportFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await refresh();
    } catch {
      showError("Failed to import snapshot");
    } finally {
      setImportLoading(false);
    }
  };

  if (error) return <div className="page-error">Error: {error}</div>;
  if (isLoading || !data) return <LoadingSpinner />;

  const totalAccounts = data.accounts.length;
  const activeAccounts = data.accounts.filter(
    (a) => a.status === "ACTIVE",
  ).length;
  const frozenAccounts = data.accounts.filter(
    (a) => a.status === "FROZEN",
  ).length;
  const maintenanceLabel = data.maintenance.enabled ? "ON" : "OFF";

  return (
    <div className="dashboard-page">
      <NotificationToast notification={notification} onDismiss={dismiss} />
      <div className="stats-grid">
        <StatsCard label="Total Accounts" value={totalAccounts} />
        <StatsCard label="Active" value={activeAccounts} variant="success" />
        <StatsCard label="Frozen" value={frozenAccounts} variant="warning" />
        <StatsCard
          label="Maintenance"
          value={maintenanceLabel}
          variant={data.maintenance.enabled ? "danger" : "default"}
        />
      </div>
      <section className="dashboard-section">
        <h2>Recent Activity</h2>
        <DataTable
          columns={activityColumns}
          rows={data.recentActivity}
          keyExtractor={(row) => row.id}
          emptyMessage="No recent activity"
        />
      </section>
      <section className="dashboard-section">
        <h2>Data Management</h2>
        <div className="data-management-grid">
          <div className="data-management-card">
            <h3>Export Snapshot</h3>
            <p>Download a complete database snapshot as JSON.</p>
            <button
              className="btn btn--primary"
              onClick={() => void handleExport()}
              disabled={exportLoading}
            >
              {exportLoading ? "Exporting..." : "Export Snapshot"}
            </button>
          </div>
          <div className="data-management-card">
            <h3>Import Snapshot</h3>
            <p>Upload a JSON snapshot file to seed the database.</p>
            <div className="import-controls">
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                aria-label="Snapshot file"
                onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
              />
              <div className="conflict-strategy">
                <label>
                  <input
                    type="radio"
                    name="conflict"
                    value="skip"
                    checked={conflictStrategy === "skip"}
                    onChange={() => setConflictStrategy("skip")}
                  />
                  Skip existing
                </label>
                <label>
                  <input
                    type="radio"
                    name="conflict"
                    value="replace"
                    checked={conflictStrategy === "replace"}
                    onChange={() => setConflictStrategy("replace")}
                  />
                  Replace existing
                </label>
              </div>
              <button
                className="btn btn--warning"
                disabled={!importFile || importLoading}
                onClick={() => setShowImportConfirm(true)}
              >
                Import
              </button>
            </div>
          </div>
        </div>
      </section>
      <ConfirmDialog
        isOpen={showImportConfirm}
        onClose={() => setShowImportConfirm(false)}
        onConfirm={() => void handleImportConfirm()}
        title="Import Snapshot"
        message={`This will import data from "${importFile?.name ?? ""}". Conflict strategy: ${conflictStrategy}. Continue?`}
        confirmLabel="Import"
        variant="warning"
        isLoading={importLoading}
      />
    </div>
  );
}
