import { useCallback, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { StatusBadge } from "../shared/StatusBadge";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { usePolling } from "../../hooks/usePolling";
import * as api from "../../api/endpoints";
import type { AdminAccount } from "../../api/types";

export function AccountsPage() {
  const fetchAccounts = useCallback(() => api.getAccounts(), []);
  const { data: accounts, isLoading, error, refresh } = usePolling(fetchAccounts, 60_000);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const handleFreeze = async (accountId: number) => {
    setActionLoading(accountId);
    try {
      await api.freezeAccount(accountId);
      await refresh();
    } finally {
      setActionLoading(null);
    }
  };

  const handleUnfreeze = async (accountId: number) => {
    setActionLoading(accountId);
    try {
      await api.unfreezeAccount(accountId);
      await refresh();
    } finally {
      setActionLoading(null);
    }
  };

  const columns = [
    {
      key: "account_number",
      header: "Account #",
      render: (row: AdminAccount) => row.account_number,
    },
    {
      key: "customer_name",
      header: "Customer",
      render: (row: AdminAccount) => row.customer_name,
    },
    {
      key: "account_type",
      header: "Type",
      render: (row: AdminAccount) => row.account_type,
    },
    {
      key: "balance",
      header: "Balance",
      render: (row: AdminAccount) => `$${row.balance}`,
    },
    {
      key: "status",
      header: "Status",
      render: (row: AdminAccount) => <StatusBadge status={row.status} />,
    },
    {
      key: "actions",
      header: "Actions",
      render: (row: AdminAccount) => {
        const isProcessing = actionLoading === row.id;
        if (row.status === "ACTIVE") {
          return (
            <button
              className="btn btn--danger btn--small"
              onClick={() => void handleFreeze(row.id)}
              disabled={isProcessing}
            >
              {isProcessing ? "Freezing..." : "Freeze"}
            </button>
          );
        }
        if (row.status === "FROZEN") {
          return (
            <button
              className="btn btn--success btn--small"
              onClick={() => void handleUnfreeze(row.id)}
              disabled={isProcessing}
            >
              {isProcessing ? "Unfreezing..." : "Unfreeze"}
            </button>
          );
        }
        return <span className="text-muted">N/A</span>;
      },
    },
  ];

  if (isLoading || !accounts) return <LoadingSpinner />;
  if (error) return <div className="page-error">Error: {error}</div>;

  return (
    <div className="accounts-page">
      <DataTable
        columns={columns}
        rows={accounts}
        keyExtractor={(row) => row.id}
        emptyMessage="No accounts found"
      />
    </div>
  );
}
