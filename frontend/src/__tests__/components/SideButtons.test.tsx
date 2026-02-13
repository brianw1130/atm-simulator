import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SideButtons } from "../../components/atm-housing/SideButtons";

describe("SideButtons", () => {
  it("renders 4 buttons on the left side", () => {
    render(<SideButtons side="left" buttons={[null, null, null, null]} />);
    const container = screen.getByTestId("side-buttons-left");
    const buttons = container.querySelectorAll("button");
    expect(buttons).toHaveLength(4);
  });

  it("renders labeled buttons as enabled", () => {
    const onClick = vi.fn();
    render(
      <SideButtons
        side="left"
        buttons={[{ label: "Balance", onClick }, null, null, null]}
      />,
    );
    const btn = screen.getByTestId("side-btn-left-balance");
    expect(btn).not.toBeDisabled();
  });

  it("renders null slots as disabled", () => {
    render(<SideButtons side="right" buttons={[null, null, null, null]} />);
    const container = screen.getByTestId("side-buttons-right");
    const buttons = container.querySelectorAll("button");
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it("calls onClick when a labeled button is clicked", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(
      <SideButtons
        side="right"
        buttons={[{ label: "Logout", onClick }, null, null, null]}
      />,
    );
    await user.click(screen.getByTestId("side-btn-right-logout"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("pads to 4 slots when fewer are provided", () => {
    render(<SideButtons side="left" buttons={[]} />);
    const container = screen.getByTestId("side-buttons-left");
    expect(container.querySelectorAll("button")).toHaveLength(4);
  });
});
