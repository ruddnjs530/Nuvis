import type { ReactNode } from 'react';

// ── Types ─────────────────────────────────────────────────────────────────────
interface SensorStatCardProps {
  title: string;
  value: string;
  unit?: string;
  description?: string;
  icon: ReactNode;
}

// ── Component ─────────────────────────────────────────────────────────────────
export function SensorStatCard({
  title,
  value,
  unit,
  description,
  icon,
}: SensorStatCardProps) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-border-default bg-surface p-4 shadow-card">
      {/* 우상단 블러 오버레이 */}
      <div className="pointer-events-none absolute -right-4 -top-4 h-24 w-24 rounded-full bg-brand-subtle blur-sm" />

      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <p className="text-sm text-fg-muted">{title}</p>

          <div className="flex items-baseline gap-1.5 pt-1">
            <span className="text-4xl font-bold tracking-tight text-fg-strong">
              {value}
            </span>
            {unit && (
              <span className="text-sm text-fg-muted">{unit}</span>
            )}
          </div>

          {description && (
            <p className="text-xs text-fg-muted">{description}</p>
          )}
        </div>

        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-subtle text-brand">
          {icon}
        </div>
      </div>
    </div>
  );
}
