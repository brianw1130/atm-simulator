import { useCallback, useState } from "react";
import { useAuth } from "./hooks/useAuth";
import { LoginPage } from "./components/pages/LoginPage";
import { DashboardPage } from "./components/pages/DashboardPage";
import { CustomersPage } from "./components/pages/CustomersPage";
import { CustomerDetailPage } from "./components/pages/CustomerDetailPage";
import { AccountsPage } from "./components/pages/AccountsPage";
import { AuditLogsPage } from "./components/pages/AuditLogsPage";
import { MaintenancePage } from "./components/pages/MaintenancePage";
import { AppLayout } from "./components/layout/AppLayout";
import { LoadingSpinner } from "./components/shared/LoadingSpinner";

export default function App() {
  const { isAuthenticated, isLoading, username, login, logout } = useAuth();
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(
    null,
  );

  const navigateToCustomer = useCallback((customerId: number) => {
    setSelectedCustomerId(customerId);
    setActivePage("customer-detail");
  }, []);

  const handleNavigate = useCallback((page: string) => {
    setActivePage(page);
    if (page !== "customer-detail") {
      setSelectedCustomerId(null);
    }
  }, []);

  function renderPage() {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage />;
      case "customers":
        return <CustomersPage onNavigateToCustomer={navigateToCustomer} />;
      case "customer-detail":
        return selectedCustomerId ? (
          <CustomerDetailPage
            customerId={selectedCustomerId}
            onBack={() => handleNavigate("customers")}
          />
        ) : (
          <CustomersPage onNavigateToCustomer={navigateToCustomer} />
        );
      case "accounts":
        return <AccountsPage />;
      case "audit-logs":
        return <AuditLogsPage />;
      case "maintenance":
        return <MaintenancePage />;
      default:
        return <DashboardPage />;
    }
  }

  if (isLoading) {
    return (
      <div className="app-loading">
        <LoadingSpinner />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={login} />;
  }

  return (
    <AppLayout
      activePage={activePage}
      onNavigate={handleNavigate}
      username={username}
      onLogout={() => void logout()}
    >
      {renderPage()}
    </AppLayout>
  );
}
