import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { NotificationToast } from "../../components/shared/Notification";

describe("NotificationToast", () => {
  it("renders nothing when notification is null", () => {
    const { container } = render(
      <NotificationToast notification={null} onDismiss={vi.fn()} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders success notification", () => {
    render(
      <NotificationToast
        notification={{ message: "Saved!", type: "success" }}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText("Saved!")).toBeInTheDocument();
    expect(screen.getByRole("alert").className).toContain("success");
  });

  it("renders error notification", () => {
    render(
      <NotificationToast
        notification={{ message: "Failed!", type: "error" }}
        onDismiss={vi.fn()}
      />,
    );
    expect(screen.getByText("Failed!")).toBeInTheDocument();
    expect(screen.getByRole("alert").className).toContain("error");
  });

  it("calls onDismiss when dismiss button is clicked", () => {
    const onDismiss = vi.fn();
    render(
      <NotificationToast
        notification={{ message: "Test", type: "success" }}
        onDismiss={onDismiss}
      />,
    );
    fireEvent.click(screen.getByLabelText("Dismiss"));
    expect(onDismiss).toHaveBeenCalledOnce();
  });
});
