import { useCallback, useState } from "react";
import { DataTable } from "../shared/DataTable";
import { StatusBadge } from "../shared/StatusBadge";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { NotificationToast } from "../shared/Notification";
import { CustomerFormModal } from "../shared/CustomerFormModal";
import { AccountFormModal } from "../shared/AccountFormModal";
import { PinResetModal } from "../shared/PinResetModal";
import { ConfirmDialog } from "../shared/ConfirmDialog";
import { usePolling } from "../../hooks/usePolling";
import { useNotification } from "../../hooks/useNotification";
import * as api from "../../api/endpoints";
import type {
  AccountCreateData,
  AdminAccountDetail,
  AdminCard,
  CustomerCreateData,
} from "../../api/types";

interface CustomerDetailPageProps {
  customerId: number;
  onBack: () => void;
}

export function CustomerDetailPage({
  customerId,
  onBack,
}: CustomerDetailPageProps) {
  const fetchDetail = useCallback(
    () => api.getCustomerDetail(customerId),
    [customerId],
  );
  const { data: customer, isLoading, error, refresh } = usePolling(fetchDetail, 60_000);
  const { notification, showSuccess, showError, dismiss } = useNotification();

  const [showEditModal, setShowEditModal] = useState(false);
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [pinResetCard, setPinResetCard] = useState<AdminCard | null>(null);
  const [closeTarget, setCloseTarget] = useState<AdminAccountDetail | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const handleEdit = async (data: CustomerCreateData) => {
    await api.updateCustomer(customerId, data);
    showSuccess("Customer updated successfully");
    await refresh();
  };

  const handleCreateAccount = async (data: AccountCreateData) => {
    await api.createAccount(customerId, data);
    showSuccess("Account created successfully");
    await refresh();
  };

  const handleResetPin = async (newPin: string) => {
    if (!pinResetCard) return;
    await api.resetPin(pinResetCard.id, newPin);
    showSuccess(`PIN reset for card ${pinResetCard.card_number}`);
    await refresh();
  };

  const handleCloseAccount = async () => {
    if (!closeTarget) return;
    setActionLoading(true);
    try {
      await api.closeAccount(closeTarget.id);
      showSuccess(`Account ${closeTarget.account_number} closed`);
      setCloseTarget(null);
      await refresh();
    } catch {
      showError("Failed to close account. Balance must be zero.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleFreeze = async (accountId: number) => {
    try {
      await api.freezeAccount(accountId);
      showSuccess("Account frozen");
      await refresh();
    } catch {
      showError("Failed to freeze account");
    }
  };

  const handleUnfreeze = async (accountId: number) => {
    try {
      await api.unfreezeAccount(accountId);
      showSuccess("Account unfrozen");
      await refresh();
    } catch {
      showError("Failed to unfreeze account");
    }
  };

  if (error) return <div className="page-error">Error: {error}</div>;
  if (isLoading || !customer) return <LoadingSpinner />;

  const accountColumns = [
    {
      key: "account_number",
      header: "Account #",
      render: (row: AdminAccountDetail) => row.account_number,
    },
    {
      key: "type",
      header: "Type",
      render: (row: AdminAccountDetail) => row.account_type,
    },
    {
      key: "balance",
      header: "Balance",
      render: (row: AdminAccountDetail) => row.balance,
    },
    {
      key: "status",
      header: "Status",
      render: (row: AdminAccountDetail) => (
        <StatusBadge status={row.status} />
      ),
    },
    {
      key: "cards",
      header: "Cards",
      render: (row: AdminAccountDetail) =>
        row.cards.map((card) => (
          <div key={card.id} className="card-info">
            <span>{card.card_number}</span>
            {card.is_locked && (
              <span className="badge badge--frozen">Locked</span>
            )}
            <button
              className="btn btn--outline btn--small"
              onClick={() => setPinResetCard(card)}
            >
              Reset PIN
            </button>
          </div>
        )),
    },
    {
      key: "actions",
      header: "Actions",
      render: (row: AdminAccountDetail) => {
        const buttons = [];
        if (row.status === "ACTIVE") {
          buttons.push(
            <button
              key="freeze"
              className="btn btn--warning btn--small"
              onClick={() => void handleFreeze(row.id)}
            >
              Freeze
            </button>,
          );
          buttons.push(
            <button
              key="close"
              className="btn btn--danger btn--small"
              onClick={() => setCloseTarget(row)}
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
            >
              Unfreeze
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

  return (
    <div className="customer-detail-page">
      <NotificationToast notification={notification} onDismiss={dismiss} />
      <div className="breadcrumb">
        <button className="btn-link" onClick={onBack}>
          Customers
        </button>
        <span className="breadcrumb__separator">&gt;</span>
        <span>
          {customer.first_name} {customer.last_name}
        </span>
      </div>

      <div className="customer-info-header">
        <div className="customer-info">
          <h2>
            {customer.first_name} {customer.last_name}
          </h2>
          <p>Email: {customer.email}</p>
          {customer.phone && <p>Phone: {customer.phone}</p>}
          <p>Date of Birth: {customer.date_of_birth}</p>
          <p>
            Status:{" "}
            <StatusBadge status={customer.is_active ? "ACTIVE" : "CLOSED"} />
          </p>
        </div>
        <button
          className="btn btn--outline"
          onClick={() => setShowEditModal(true)}
        >
          Edit Customer
        </button>
      </div>

      <section className="customer-accounts-section">
        <div className="section-header">
          <h3>Accounts ({customer.accounts.length})</h3>
          <button
            className="btn btn--primary btn--small"
            onClick={() => setShowAccountModal(true)}
          >
            Add Account
          </button>
        </div>
        <DataTable
          columns={accountColumns}
          rows={customer.accounts}
          keyExtractor={(row) => row.id}
          emptyMessage="No accounts"
        />
      </section>

      <CustomerFormModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        onSubmit={handleEdit}
        customer={customer}
      />
      <AccountFormModal
        isOpen={showAccountModal}
        onClose={() => setShowAccountModal(false)}
        onSubmit={handleCreateAccount}
      />
      {pinResetCard && (
        <PinResetModal
          isOpen={!!pinResetCard}
          onClose={() => setPinResetCard(null)}
          onSubmit={handleResetPin}
          cardNumber={pinResetCard.card_number}
        />
      )}
      <ConfirmDialog
        isOpen={!!closeTarget}
        onClose={() => setCloseTarget(null)}
        onConfirm={() => void handleCloseAccount()}
        title="Close Account"
        message={
          closeTarget
            ? `Are you sure you want to close account ${closeTarget.account_number}? Balance must be zero.`
            : ""
        }
        confirmLabel="Close Account"
        variant="danger"
        isLoading={actionLoading}
      />
    </div>
  );
}
