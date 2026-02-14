import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginPage } from "../../components/pages/LoginPage";

describe("LoginPage", () => {
  it("renders username and password inputs", () => {
    render(<LoginPage onLogin={vi.fn()} />);
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("submit button is disabled when fields are empty", () => {
    render(<LoginPage onLogin={vi.fn()} />);
    const btn = screen.getByRole("button", { name: "Sign In" });
    expect(btn).toBeDisabled();
  });

  it("calls onLogin with username and password on submit", async () => {
    const user = userEvent.setup();
    const onLogin = vi.fn().mockResolvedValue(undefined);
    render(<LoginPage onLogin={onLogin} />);

    await user.type(screen.getByLabelText("Username"), "admin");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(onLogin).toHaveBeenCalledWith("admin", "secret");
  });

  it("shows error message on login failure", async () => {
    const user = userEvent.setup();
    const onLogin = vi.fn().mockRejectedValue(new Error("Bad credentials"));
    render(<LoginPage onLogin={onLogin} />);

    await user.type(screen.getByLabelText("Username"), "admin");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(
      await screen.findByText("Invalid username or password"),
    ).toBeInTheDocument();
  });

  it("shows loading state during login", async () => {
    const user = userEvent.setup();
    const onLogin = vi.fn().mockReturnValue(new Promise(() => {}));
    render(<LoginPage onLogin={onLogin} />);

    await user.type(screen.getByLabelText("Username"), "admin");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(screen.getByText("Signing in...")).toBeInTheDocument();
  });

  it("clears error when user types after failure", async () => {
    const user = userEvent.setup();
    const onLogin = vi.fn().mockRejectedValueOnce(new Error("Bad"));
    render(<LoginPage onLogin={onLogin} />);

    await user.type(screen.getByLabelText("Username"), "admin");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign In" }));

    expect(
      await screen.findByText("Invalid username or password"),
    ).toBeInTheDocument();

    await user.type(screen.getByLabelText("Username"), "x");
    expect(
      screen.queryByText("Invalid username or password"),
    ).not.toBeInTheDocument();
  });
});
