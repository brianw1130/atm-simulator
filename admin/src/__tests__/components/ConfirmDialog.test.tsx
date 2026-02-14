import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConfirmDialog } from "../../components/shared/ConfirmDialog";

describe("ConfirmDialog", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    title: "Confirm Action",
    message: "Are you sure?",
  };

  it("renders nothing when not open", () => {
    const { container } = render(
      <ConfirmDialog {...defaultProps} isOpen={false} />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders title and message", () => {
    render(<ConfirmDialog {...defaultProps} />);
    expect(screen.getByText("Confirm Action")).toBeInTheDocument();
    expect(screen.getByText("Are you sure?")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button is clicked", () => {
    const onConfirm = vi.fn();
    render(<ConfirmDialog {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText("Confirm"));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("calls onClose when cancel button is clicked", () => {
    const onClose = vi.fn();
    render(<ConfirmDialog {...defaultProps} onClose={onClose} />);
    fireEvent.click(screen.getByText("Cancel"));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("uses custom confirm label", () => {
    render(<ConfirmDialog {...defaultProps} confirmLabel="Delete" />);
    expect(screen.getByText("Delete")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(<ConfirmDialog {...defaultProps} isLoading={true} />);
    expect(screen.getByText("Processing...")).toBeInTheDocument();
    expect(screen.getByText("Processing...")).toBeDisabled();
    expect(screen.getByText("Cancel")).toBeDisabled();
  });

  it("applies danger variant class", () => {
    render(
      <ConfirmDialog {...defaultProps} variant="danger" confirmLabel="Delete" />,
    );
    const btn = screen.getByText("Delete");
    expect(btn.className).toContain("btn--danger");
  });

  it("applies warning variant class", () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        variant="warning"
        confirmLabel="Proceed"
      />,
    );
    const btn = screen.getByText("Proceed");
    expect(btn.className).toContain("btn--warning");
  });
});
