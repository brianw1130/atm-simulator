import { StatsCard } from "../shared/StatsCard";
import { DataTable } from "../shared/DataTable";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { usePolling } from "../../hooks/usePolling";
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
  const { data, isLoading, error } = usePolling(fetchDashboardData, 30_000);

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
    </div>
  );
}
