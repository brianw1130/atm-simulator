interface SidebarProps {
  activePage: string;
  onNavigate: (page: string) => void;
}

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "\u2302" },
  { id: "accounts", label: "Accounts", icon: "\u2630" },
  { id: "audit-logs", label: "Audit Logs", icon: "\u2637" },
  { id: "maintenance", label: "Maintenance", icon: "\u2699" },
] as const;

export function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <nav className="sidebar" aria-label="Admin navigation">
      <div className="sidebar__brand">ATM Admin</div>
      <ul className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <li key={item.id}>
            <button
              className={`sidebar__link ${activePage === item.id ? "sidebar__link--active" : ""}`}
              onClick={() => onNavigate(item.id)}
              aria-current={activePage === item.id ? "page" : undefined}
            >
              <span className="sidebar__icon">{item.icon}</span>
              <span className="sidebar__label">{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
}
