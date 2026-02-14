interface StatsCardProps {
  label: string;
  value: string | number;
  variant?: "default" | "success" | "warning" | "danger";
}

export function StatsCard({ label, value, variant = "default" }: StatsCardProps) {
  return (
    <div className={`stats-card stats-card--${variant}`}>
      <span className="stats-card__label">{label}</span>
      <span className="stats-card__value">{value}</span>
    </div>
  );
}
