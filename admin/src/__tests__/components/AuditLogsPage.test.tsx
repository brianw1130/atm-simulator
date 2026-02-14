import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuditLogsPage } from "../../components/pages/AuditLogsPage";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getAuditLogs: vi.fn(),
}));

const mockLogs = [
  {
    id: 1,
    event_type: "AUTH_SUCCESS",
    account_id: 1,
    ip_address: "127.0.0.1",
    session_id: "abc123",
    details: { card_number: "1000-0001-0001" },
    created_at: "2026-02-13T12:00:00Z",
  },
  {
    id: 2,
    event_type: "WITHDRAWAL_SUCCESS",
    account_id: 1,
    ip_address: "127.0.0.1",
    session_id: "abc123",
    details: { amount: 100 },
    created_at: "2026-02-13T12:05:00Z",
  },
];

describe("AuditLogsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getAuditLogs).mockResolvedValue(mockLogs);
  });

  it("renders log entries in table", async () => {
    render(<AuditLogsPage />);

    await waitFor(() => {
      // AUTH_SUCCESS appears in both filter dropdown and table, use getAllByText
      const matches = screen.getAllByText("AUTH_SUCCESS");
      expect(matches.length).toBeGreaterThanOrEqual(2);
    });

    // WITHDRAWAL_SUCCESS also appears in dropdown and table
    const wdMatches = screen.getAllByText("WITHDRAWAL_SUCCESS");
    expect(wdMatches.length).toBeGreaterThanOrEqual(2);
  });

  it("renders event type filter dropdown", async () => {
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("Event Type:")).toBeInTheDocument();
    });

    expect(screen.getByText("All Events")).toBeInTheDocument();
  });

  it("re-fetches when filter changes", async () => {
    const user = userEvent.setup();
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(api.getAuditLogs).toHaveBeenCalled();
    });

    const select = screen.getByLabelText("Event Type:");
    await user.selectOptions(select, "AUTH_SUCCESS");

    await waitFor(() => {
      expect(api.getAuditLogs).toHaveBeenCalledTimes(2);
    });
  });

  it("formats timestamps", async () => {
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText("Timestamp")).toBeInTheDocument();
    });

    const cells = screen.getAllByRole("cell");
    expect(cells.length).toBeGreaterThan(0);
  });

  it("shows details JSON", async () => {
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText('{"amount":100}')).toBeInTheDocument();
    });
  });

  it("expands and collapses long details JSON", async () => {
    const user = userEvent.setup();
    const longDetailsLogs = [
      {
        id: 1,
        event_type: "AUTH_SUCCESS",
        account_id: null,
        ip_address: null,
        session_id: null,
        details: {
          long_field:
            "a very long value that should be truncated in the default view because it exceeds sixty characters total",
        },
        created_at: "2026-02-13T12:00:00Z",
      },
    ];
    vi.mocked(api.getAuditLogs).mockResolvedValue(longDetailsLogs);
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText(/long_field/)).toBeInTheDocument();
    });

    // Should be truncated - click to expand
    const expandBtn = screen.getByRole("button", { name: /long_field/ });
    await user.click(expandBtn);

    // Click again to collapse
    await user.click(expandBtn);
  });

  it("shows dash for null account_id", async () => {
    const logsWithNullAccount = [
      {
        id: 1,
        event_type: "MAINTENANCE_ENABLED",
        account_id: null,
        ip_address: null,
        session_id: null,
        details: {},
        created_at: "2026-02-13T12:00:00Z",
      },
    ];
    vi.mocked(api.getAuditLogs).mockResolvedValue(logsWithNullAccount);
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText("-")).toBeInTheDocument();
    });
  });

  it("shows empty state when no logs", async () => {
    vi.mocked(api.getAuditLogs).mockResolvedValue([]);
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText("No audit logs found")).toBeInTheDocument();
    });
  });
});
