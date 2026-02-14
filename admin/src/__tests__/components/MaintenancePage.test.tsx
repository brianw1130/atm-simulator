import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MaintenancePage } from "../../components/pages/MaintenancePage";
import * as api from "../../api/endpoints";

vi.mock("../../api/endpoints", () => ({
  getMaintenanceStatus: vi.fn(),
  enableMaintenance: vi.fn(),
  disableMaintenance: vi.fn(),
}));

describe("MaintenancePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays OFF status when maintenance is disabled", async () => {
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    render(<MaintenancePage />);

    await waitFor(() => {
      expect(screen.getByText("OFF")).toBeInTheDocument();
    });
  });

  it("displays ON status with reason when maintenance is enabled", async () => {
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: true,
      reason: "Scheduled update",
    });
    render(<MaintenancePage />);

    await waitFor(() => {
      expect(screen.getByText("ON")).toBeInTheDocument();
    });

    expect(screen.getByText("Reason: Scheduled update")).toBeInTheDocument();
  });

  it("calls enableMaintenance API with reason", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    vi.mocked(api.enableMaintenance).mockResolvedValue({
      message: "Maintenance enabled",
    });
    render(<MaintenancePage />);

    await waitFor(() => {
      expect(
        screen.getByText("Enable Maintenance Mode"),
      ).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(
      "Reason for maintenance (optional)",
    );
    await user.type(input, "System upgrade");
    await user.click(screen.getByText("Enable Maintenance Mode"));

    expect(api.enableMaintenance).toHaveBeenCalledWith("System upgrade");
  });

  it("shows reason input when maintenance is off", async () => {
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: false,
      reason: null,
    });
    render(<MaintenancePage />);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Reason for maintenance (optional)"),
      ).toBeInTheDocument();
    });
  });

  it("calls disableMaintenance API on disable", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getMaintenanceStatus).mockResolvedValue({
      enabled: true,
      reason: "Update",
    });
    vi.mocked(api.disableMaintenance).mockResolvedValue({
      message: "Maintenance disabled",
    });
    render(<MaintenancePage />);

    await waitFor(() => {
      expect(
        screen.getByText("Disable Maintenance Mode"),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByText("Disable Maintenance Mode"));
    expect(api.disableMaintenance).toHaveBeenCalled();
  });

  it("refreshes after toggling maintenance", async () => {
    const user = userEvent.setup();
    vi.mocked(api.getMaintenanceStatus)
      .mockResolvedValueOnce({ enabled: false, reason: null })
      .mockResolvedValue({ enabled: true, reason: null });
    vi.mocked(api.enableMaintenance).mockResolvedValue({
      message: "Maintenance enabled",
    });
    render(<MaintenancePage />);

    await waitFor(() => {
      expect(
        screen.getByText("Enable Maintenance Mode"),
      ).toBeInTheDocument();
    });

    await user.click(screen.getByText("Enable Maintenance Mode"));

    await waitFor(() => {
      expect(api.getMaintenanceStatus).toHaveBeenCalledTimes(2);
    });
  });
});
