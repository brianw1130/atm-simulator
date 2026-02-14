interface StatusBadgeProps {
  status: "ACTIVE" | "FROZEN" | "CLOSED";
}

const STATUS_CLASSES: Record<string, string> = {
  ACTIVE: "badge badge--active",
  FROZEN: "badge badge--frozen",
  CLOSED: "badge badge--closed",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const className = STATUS_CLASSES[status] ?? "badge";
  return <span className={className}>{status}</span>;
}
