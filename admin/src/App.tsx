import { useState } from "react";
import { useAuth } from "./hooks/useAuth";
import { LoginPage } from "./components/pages/LoginPage";
import { DashboardPage } from "./components/pages/DashboardPage";
import { AccountsPage } from "./components/pages/AccountsPage";
import { AuditLogsPage } from "./components/pages/AuditLogsPage";
import { MaintenancePage } from "./components/pages/MaintenancePage";
import { AppLayout } from "./components/layout/AppLayout";
import { LoadingSpinner } from "./components/shared/LoadingSpinner";

function renderPage(page: string) {
  switch (page) {
    case "dashboard":
      return <DashboardPage />;
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

export default function App() {
  const { isAuthenticated, isLoading, username, login, logout } = useAuth();
  const [activePage, setActivePage] = useState("dashboard");

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
      onNavigate={setActivePage}
      username={username}
      onLogout={() => void logout()}
    >
      {renderPage(activePage)}
    </AppLayout>
  );
}
