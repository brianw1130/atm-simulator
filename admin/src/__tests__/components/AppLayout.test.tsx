import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AppLayout } from "../../components/layout/AppLayout";

describe("AppLayout", () => {
  it("renders sidebar nav items", () => {
    render(
      <AppLayout
        activePage="dashboard"
        onNavigate={vi.fn()}
        username="admin"
        onLogout={vi.fn()}
      >
        <div>Content</div>
      </AppLayout>,
    );

    const sidebar = screen.getByRole("navigation", {
      name: "Admin navigation",
    });
    expect(sidebar).toBeInTheDocument();
    // Check that sidebar contains all nav labels
    expect(screen.getByText("Accounts")).toBeInTheDocument();
    expect(screen.getByText("Audit Logs")).toBeInTheDocument();
    expect(screen.getByText("Maintenance")).toBeInTheDocument();
  });

  it("highlights active page in sidebar", () => {
    render(
      <AppLayout
        activePage="accounts"
        onNavigate={vi.fn()}
        username="admin"
        onLogout={vi.fn()}
      >
        <div>Content</div>
      </AppLayout>,
    );

    const accountsBtn = screen.getByRole("button", {
      name: /Accounts/,
    });
    expect(accountsBtn.className).toContain("sidebar__link--active");
  });

  it("calls onNavigate when sidebar item is clicked", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    render(
      <AppLayout
        activePage="dashboard"
        onNavigate={onNavigate}
        username="admin"
        onLogout={vi.fn()}
      >
        <div>Content</div>
      </AppLayout>,
    );

    await user.click(screen.getByRole("button", { name: /Accounts/ }));
    expect(onNavigate).toHaveBeenCalledWith("accounts");
  });

  it("displays username in topbar", () => {
    render(
      <AppLayout
        activePage="dashboard"
        onNavigate={vi.fn()}
        username="testadmin"
        onLogout={vi.fn()}
      >
        <div>Content</div>
      </AppLayout>,
    );

    expect(screen.getByTestId("topbar-username")).toHaveTextContent(
      "testadmin",
    );
  });

  it("calls onLogout when logout button is clicked", async () => {
    const user = userEvent.setup();
    const onLogout = vi.fn();
    render(
      <AppLayout
        activePage="dashboard"
        onNavigate={vi.fn()}
        username="admin"
        onLogout={onLogout}
      >
        <div>Content</div>
      </AppLayout>,
    );

    await user.click(screen.getByRole("button", { name: "Logout" }));
    expect(onLogout).toHaveBeenCalled();
  });

  it("renders page content", () => {
    render(
      <AppLayout
        activePage="dashboard"
        onNavigate={vi.fn()}
        username="admin"
        onLogout={vi.fn()}
      >
        <div data-testid="page-content">Hello World</div>
      </AppLayout>,
    );

    expect(screen.getByTestId("page-content")).toBeInTheDocument();
  });
});
