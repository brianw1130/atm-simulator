import { useCallback, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { StatusBadge } from "../shared/StatusBadge";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { NotificationToast } from "../shared/Notification";
import { CustomerFormModal } from "../shared/CustomerFormModal";
import { ConfirmDialog } from "../shared/ConfirmDialog";
import { usePolling } from "../../hooks/usePolling";
import { useNotification } from "../../hooks/useNotification";
import * as api from "../../api/endpoints";
import type { AdminCustomer, CustomerCreateData } from "../../api/types";

interface CustomersPageProps {
  onNavigateToCustomer: (customerId: number) => void;
}

export function CustomersPage({ onNavigateToCustomer }: CustomersPageProps) {
  const fetchCustomers = useCallback(() => api.getCustomers(), []);
  const { data: customers, isLoading, error, refresh } = usePolling(fetchCustomers, 60_000);
  const { notification, showSuccess, showError, dismiss } = useNotification();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deactivateTarget, setDeactivateTarget] = useState<AdminCustomer | null>(null);
  const [activateTarget, setActivateTarget] = useState<AdminCustomer | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const handleCreate = async (data: CustomerCreateData) => {
    await api.createCustomer(data);
    showSuccess("Customer created successfully");
    await refresh();
  };

  const handleDeactivate = async () => {
    if (!deactivateTarget) return;
    setActionLoading(true);
    try {
      await api.deactivateCustomer(deactivateTarget.id);
      showSuccess(`${deactivateTarget.first_name} ${deactivateTarget.last_name} deactivated`);
      setDeactivateTarget(null);
      await refresh();
    } catch {
      showError("Failed to deactivate customer");
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivate = async () => {
    if (!activateTarget) return;
    setActionLoading(true);
    try {
      await api.activateCustomer(activateTarget.id);
      showSuccess(`${activateTarget.first_name} ${activateTarget.last_name} activated`);
      setActivateTarget(null);
      await refresh();
    } catch {
      showError("Failed to activate customer");
    } finally {
      setActionLoading(false);
    }
  };

  const columns = [
    {
      key: "name",
      header: "Name",
      render: (row: AdminCustomer) => (
        <button
          className="btn-link"
          onClick={() => onNavigateToCustomer(row.id)}
        >
          {row.first_name} {row.last_name}
        </button>
      ),
    },
    {
      key: "email",
      header: "Email",
      render: (row: AdminCustomer) => row.email,
    },
    {
      key: "phone",
      header: "Phone",
      render: (row: AdminCustomer) => row.phone ?? "-",
    },
    {
      key: "accounts",
      header: "Accounts",
      render: (row: AdminCustomer) => String(row.account_count),
    },
    {
      key: "status",
      header: "Status",
      render: (row: AdminCustomer) => (
        <StatusBadge status={row.is_active ? "ACTIVE" : "CLOSED"} />
      ),
    },
    {
      key: "actions",
      header: "Actions",
      render: (row: AdminCustomer) => {
        if (row.is_active) {
          return (
            <button
              className="btn btn--danger btn--small"
              onClick={() => setDeactivateTarget(row)}
            >
              Deactivate
            </button>
          );
        }
        return (
          <button
            className="btn btn--success btn--small"
            onClick={() => setActivateTarget(row)}
          >
            Activate
          </button>
        );
      },
    },
  ];

  if (error) return <div className="page-error">Error: {error}</div>;
  if (isLoading || !customers) return <LoadingSpinner />;

  return (
    <div className="customers-page">
      <NotificationToast notification={notification} onDismiss={dismiss} />
      <div className="page-actions">
        <button
          className="btn btn--primary"
          onClick={() => setShowCreateModal(true)}
        >
          Create Customer
        </button>
      </div>
      <DataTable
        columns={columns}
        rows={customers}
        keyExtractor={(row) => row.id}
        emptyMessage="No customers found"
      />
      <CustomerFormModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreate}
      />
      <ConfirmDialog
        isOpen={!!deactivateTarget}
        onClose={() => setDeactivateTarget(null)}
        onConfirm={() => void handleDeactivate()}
        title="Deactivate Customer"
        message={
          deactivateTarget
            ? `Are you sure you want to deactivate ${deactivateTarget.first_name} ${deactivateTarget.last_name}?`
            : ""
        }
        confirmLabel="Deactivate"
        variant="danger"
        isLoading={actionLoading}
      />
      <ConfirmDialog
        isOpen={!!activateTarget}
        onClose={() => setActivateTarget(null)}
        onConfirm={() => void handleActivate()}
        title="Activate Customer"
        message={
          activateTarget
            ? `Are you sure you want to activate ${activateTarget.first_name} ${activateTarget.last_name}?`
            : ""
        }
        confirmLabel="Activate"
        variant="warning"
        isLoading={actionLoading}
      />
    </div>
  );
}
