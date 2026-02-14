import { useCallback, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { usePolling } from "../../hooks/usePolling";
import * as api from "../../api/endpoints";
import { AUDIT_EVENT_TYPES } from "../../api/types";
import type { AuditLogEntry } from "../../api/types";

export function AuditLogsPage() {
  const [eventFilter, setEventFilter] = useState<string>("");
  const [limit, setLimit] = useState(100);

  const fetchLogs = useCallback(
    () => api.getAuditLogs(limit, eventFilter || undefined),
    [limit, eventFilter],
  );
  const { data: logs, isLoading, error } = usePolling(fetchLogs, 30_000);

  const [expandedId, setExpandedId] = useState<number | null>(null);

  const columns = [
    {
      key: "time",
      header: "Timestamp",
      render: (row: AuditLogEntry) => {
        const date = new Date(row.created_at);
        return date.toLocaleString();
      },
    },
    {
      key: "event_type",
      header: "Event Type",
      render: (row: AuditLogEntry) => (
        <span className="badge badge--info">{row.event_type}</span>
      ),
    },
    {
      key: "account_id",
      header: "Account ID",
      render: (row: AuditLogEntry) =>
        row.account_id !== null ? String(row.account_id) : "-",
    },
    {
      key: "details",
      header: "Details",
      render: (row: AuditLogEntry) => {
        const text = JSON.stringify(row.details);
        const isExpanded = expandedId === row.id;
        if (text.length <= 60) return <span>{text}</span>;
        return (
          <button
            className="btn-link"
            onClick={() => setExpandedId(isExpanded ? null : row.id)}
          >
            {isExpanded ? text : text.slice(0, 60) + "..."}
          </button>
        );
      },
    },
  ];

  if (isLoading && !logs) return <LoadingSpinner />;
  if (error) return <div className="page-error">Error: {error}</div>;

  return (
    <div className="audit-logs-page">
      <div className="filters">
        <label htmlFor="event-filter">Event Type:</label>
        <select
          id="event-filter"
          className="filter-select"
          value={eventFilter}
          onChange={(e) => setEventFilter(e.target.value)}
        >
          <option value="">All Events</option>
          {AUDIT_EVENT_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <label htmlFor="limit-select">Limit:</label>
        <select
          id="limit-select"
          className="filter-select"
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
        >
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
          <option value={250}>250</option>
        </select>
      </div>
      <DataTable
        columns={columns}
        rows={logs ?? []}
        keyExtractor={(row) => row.id}
        emptyMessage="No audit logs found"
      />
    </div>
  );
}
