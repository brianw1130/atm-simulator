import { useCallback, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { StatusBadge } from "../shared/StatusBadge";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { NotificationToast } from "../shared/Notification";
import { ConfirmDialog } from "../shared/ConfirmDialog";
import { usePolling } from "../../hooks/usePolling";
import { useNotification } from "../../hooks/useNotification";
import * as api from "../../api/endpoints";
import type { AdminAccount } from "../../api/types";

interface AccountsPageProps {
  onNavigateToCustomer?: (customerId: number) => void;
}

export function AccountsPage({ onNavigateToCustomer }: AccountsPageProps) {
  const fetchAccounts = useCallback(() => api.getAccounts(), []);
  const { data: accounts, isLoading, error, refresh } = usePolling(fetchAccounts, 60_000);
  const { notification, showSuccess, showError, dismiss } = useNotification();
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [closeTarget, setCloseTarget] = useState<AdminAccount | null>(null);
  const [closeLoading, setCloseLoading] = useState(false);

  const handleFreeze = async (accountId: number) => {
    setActionLoading(accountId);
    try {
      await api.freezeAccount(accountId);
      showSuccess("Account frozen");
      await refresh();
    } catch {
      showError("Failed to freeze account");
    } finally {
      setActionLoading(null);
    }
  };

  const handleUnfreeze = async (accountId: number) => {
    setActionLoading(accountId);
    try {
      await api.unfreezeAccount(accountId);
      showSuccess("Account unfrozen");
      await refresh();
    } catch {
      showError("Failed to unfreeze account");
    } finally {
      setActionLoading(null);
    }
  };

  const handleClose = async () => {
    if (!closeTarget) return;
    setCloseLoading(true);
    try {
      await api.closeAccount(closeTarget.id);
      showSuccess(`Account ${closeTarget.account_number} closed`);
      setCloseTarget(null);
      await refresh();
    } catch {
      showError("Failed to close account. Balance must be zero.");
    } finally {
      setCloseLoading(false);
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
      render: (row: AdminAccount) =>
        onNavigateToCustomer ? (
          <button
            className="btn-link"
            onClick={() => onNavigateToCustomer(row.id)}
          >
            {row.customer_name}
          </button>
        ) : (
          row.customer_name
        ),
    },
    {
      key: "account_type",
      header: "Type",
      render: (row: AdminAccount) => row.account_type,
    },
    {
      key: "balance",
      header: "Balance",
      render: (row: AdminAccount) => row.balance,
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
        const buttons = [];
        if (row.status === "ACTIVE") {
          buttons.push(
            <button
              key="freeze"
              className="btn btn--danger btn--small"
              onClick={() => void handleFreeze(row.id)}
              disabled={isProcessing}
            >
              {isProcessing ? "Freezing..." : "Freeze"}
            </button>,
          );
          buttons.push(
            <button
              key="close"
              className="btn btn--warning btn--small"
              onClick={() => setCloseTarget(row)}
              disabled={isProcessing}
            >
              Close
            </button>,
          );
        }
        if (row.status === "FROZEN") {
          buttons.push(
            <button
              key="unfreeze"
              className="btn btn--success btn--small"
              onClick={() => void handleUnfreeze(row.id)}
              disabled={isProcessing}
            >
              {isProcessing ? "Unfreezing..." : "Unfreeze"}
            </button>,
          );
        }
        if (buttons.length === 0) {
          return <span className="text-muted">N/A</span>;
        }
        return <div className="action-buttons">{buttons}</div>;
      },
    },
  ];

  if (isLoading || !accounts) return <LoadingSpinner />;
  if (error) return <div className="page-error">Error: {error}</div>;

  return (
    <div className="accounts-page">
      <NotificationToast notification={notification} onDismiss={dismiss} />
      <DataTable
        columns={columns}
        rows={accounts}
        keyExtractor={(row) => row.id}
        emptyMessage="No accounts found"
      />
      <ConfirmDialog
        isOpen={!!closeTarget}
        onClose={() => setCloseTarget(null)}
        onConfirm={() => void handleClose()}
        title="Close Account"
        message={
          closeTarget
            ? `Are you sure you want to close account ${closeTarget.account_number}? Balance must be zero.`
            : ""
        }
        confirmLabel="Close Account"
        variant="danger"
        isLoading={closeLoading}
      />
    </div>
  );
}
