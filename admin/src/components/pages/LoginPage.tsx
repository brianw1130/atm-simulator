import { type FormEvent, useState } from "react";

interface LoginPageProps {
  onLogin: (username: string, password: string) => Promise<void>;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await onLogin(username, password);
    } catch {
      setError("Invalid username or password");
    } finally {
      setIsLoading(false);
    }
  };

  const isSubmitDisabled = !username.trim() || !password.trim() || isLoading;

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-card__title">ATM Admin</h1>
        <form onSubmit={(e) => void handleSubmit(e)} className="login-form">
          {error && (
            <div className="login-form__error" role="alert">
              {error}
            </div>
          )}
          <label className="login-form__label" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            className="login-form__input"
            type="text"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
              setError(null);
            }}
            autoComplete="username"
            disabled={isLoading}
          />
          <label className="login-form__label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="login-form__input"
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError(null);
            }}
            autoComplete="current-password"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="login-form__submit"
            disabled={isSubmitDisabled}
          >
            {isLoading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
