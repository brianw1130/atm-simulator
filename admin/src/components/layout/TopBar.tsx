interface TopBarProps {
  title: string;
  username: string | null;
  onLogout: () => void;
}

export function TopBar({ title, username, onLogout }: TopBarProps) {
  return (
    <header className="topbar">
      <h1 className="topbar__title">{title}</h1>
      <div className="topbar__actions">
        {username && (
          <span className="topbar__user" data-testid="topbar-username">
            {username}
          </span>
        )}
        <button className="topbar__logout" onClick={onLogout} aria-label="Logout">
          Logout
        </button>
      </div>
    </header>
  );
}
