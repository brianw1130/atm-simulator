import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AccountsPage } from "../../components/pages/AccountsPage";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getAccounts: vi.fn(),
  freezeAccount: vi.fn(),
  unfreezeAccount: vi.fn(),
  closeAccount: vi.fn(),
}));

const mockAccounts = [
  {
    id: 1,
    account_number: "1000-0001-0001",
    account_type: "CHECKING" as const,
    balance: "5250.00",
    available_balance: "5250.00",
    status: "ACTIVE" as const,
    customer_name: "Alice Johnson",
  },
  {
    id: 2,
    account_number: "1000-0002-0001",
    account_type: "CHECKING" as const,
    balance: "850.75",
    available_balance: "850.75",
    status: "FROZEN" as const,
    customer_name: "Bob Williams",
  },
  {
    id: 3,
    account_number: "1000-0003-0001",
    account_type: "CHECKING" as const,
    balance: "0.00",
    available_balance: "0.00",
    status: "CLOSED" as const,
    customer_name: "Charlie Davis",
  },
];

describe("AccountsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all accounts in table", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Alice Johnson")).toBeInTheDocument();
    });

    expect(screen.getByText("Bob Williams")).toBeInTheDocument();
    expect(screen.getByText("Charlie Davis")).toBeInTheDocument();
  });

  it("shows StatusBadge for each account status", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    });

    expect(screen.getByText("FROZEN")).toBeInTheDocument();
    expect(screen.getByText("CLOSED")).toBeInTheDocument();
  });

  it("shows Freeze button for ACTIVE accounts", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Freeze")).toBeInTheDocument();
    });
  });

  it("shows Unfreeze button for FROZEN accounts", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Unfreeze")).toBeInTheDocument();
    });
  });

  it("calls freezeAccount API and shows notification on freeze", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    vi.mocked(api.freezeAccount).mockResolvedValue({ message: "Frozen" });
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Freeze")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Freeze"));
    expect(api.freezeAccount).toHaveBeenCalledWith(1);

    await waitFor(() => {
      expect(screen.getByText("Account frozen")).toBeInTheDocument();
    });
  });

  it("calls unfreezeAccount API and shows notification on unfreeze", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    vi.mocked(api.unfreezeAccount).mockResolvedValue({ message: "Unfrozen" });
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Unfreeze")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Unfreeze"));
    expect(api.unfreezeAccount).toHaveBeenCalledWith(2);

    await waitFor(() => {
      expect(screen.getByText("Account unfrozen")).toBeInTheDocument();
    });
  });

  it("shows N/A for CLOSED accounts", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("N/A")).toBeInTheDocument();
    });
  });

  it("shows Close button for ACTIVE accounts", async () => {
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Close")).toBeInTheDocument();
    });
  });

  it("close button opens confirm dialog", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Close")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Close"));

    expect(
      screen.getByText(/Are you sure you want to close account 1000-0001-0001/),
    ).toBeInTheDocument();
  });

  it("shows error notification on freeze failure", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getAccounts).mockResolvedValue(mockAccounts);
    vi.mocked(api.freezeAccount).mockRejectedValue(new Error("fail"));
    render(<AccountsPage />);

    await waitFor(() => {
      expect(screen.getByText("Freeze")).toBeInTheDocument();
    });

    await user.click(screen.getByText("Freeze"));

    await waitFor(() => {
      expect(screen.getByText("Failed to freeze account")).toBeInTheDocument();
    });
  });
});
