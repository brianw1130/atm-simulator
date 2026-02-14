import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { StatsCard } from "../../components/shared/StatsCard";
import { DataTable } from "../../components/shared/DataTable";
import { LoadingSpinner } from "../../components/shared/LoadingSpinner";

describe("StatusBadge", () => {
  it("renders ACTIVE status with correct class", () => {
    render(<StatusBadge status="ACTIVE" />);
    const badge = screen.getByText("ACTIVE");
    expect(badge.className).toContain("badge--active");
  });

  it("renders FROZEN status with correct class", () => {
    render(<StatusBadge status="FROZEN" />);
    const badge = screen.getByText("FROZEN");
    expect(badge.className).toContain("badge--frozen");
  });

  it("renders CLOSED status with correct class", () => {
    render(<StatusBadge status="CLOSED" />);
    const badge = screen.getByText("CLOSED");
    expect(badge.className).toContain("badge--closed");
  });
});

describe("StatsCard", () => {
  it("renders label and value", () => {
    render(<StatsCard label="Total" value={42} />);
    expect(screen.getByText("Total")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("applies variant class", () => {
    const { container } = render(
      <StatsCard label="Active" value={5} variant="success" />,
    );
    const card = container.querySelector(".stats-card");
    expect(card?.className).toContain("stats-card--success");
  });

  it("uses default variant when not specified", () => {
    const { container } = render(<StatsCard label="Test" value="N/A" />);
    const card = container.querySelector(".stats-card");
    expect(card?.className).toContain("stats-card--default");
  });
});

describe("DataTable", () => {
  interface TestRow {
    id: number;
    name: string;
  }

  const columns = [
    { key: "id", header: "ID", render: (row: TestRow) => row.id },
    { key: "name", header: "Name", render: (row: TestRow) => row.name },
  ];

  it("renders headers and rows", () => {
    const rows: TestRow[] = [
      { id: 1, name: "Alice" },
      { id: 2, name: "Bob" },
    ];
    render(
      <DataTable columns={columns} rows={rows} keyExtractor={(r) => r.id} />,
    );
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("shows empty message when no rows", () => {
    render(
      <DataTable
        columns={columns}
        rows={[]}
        keyExtractor={(r) => r.id}
        emptyMessage="Nothing here"
      />,
    );
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });

  it("uses default empty message", () => {
    render(
      <DataTable columns={columns} rows={[]} keyExtractor={(r) => r.id} />,
    );
    expect(screen.getByText("No data available")).toBeInTheDocument();
  });
});

describe("LoadingSpinner", () => {
  it("renders with aria-label", () => {
    render(<LoadingSpinner />);
    expect(screen.getByLabelText("Loading")).toBeInTheDocument();
  });
});
