import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

const PAGE_TITLES: Record<string, string> = {
  dashboard: "Dashboard",
  accounts: "Accounts",
  "audit-logs": "Audit Logs",
  maintenance: "Maintenance",
};

interface AppLayoutProps {
  activePage: string;
  onNavigate: (page: string) => void;
  username: string | null;
  onLogout: () => void;
  children: ReactNode;
}

export function AppLayout({
  activePage,
  onNavigate,
  username,
  onLogout,
  children,
}: AppLayoutProps) {
  const title = PAGE_TITLES[activePage] ?? "Admin";

  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />
      <div className="app-layout__main">
        <TopBar title={title} username={username} onLogout={onLogout} />
        <main className="app-layout__content">{children}</main>
      </div>
    </div>
  );
}
