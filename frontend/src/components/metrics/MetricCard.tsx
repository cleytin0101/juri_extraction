import { type ReactNode } from "react";
import { cn } from "@/lib/utils";
import clsx from "clsx";

interface Props {
  label: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: { value: string; positive: boolean };
  className?: string;
}

export function MetricCard({ label, value, subtitle, icon, trend, className }: Props) {
  return (
    <div className={cn("bg-surface-800 rounded-xl p-5 flex flex-col gap-2 border border-surface-600", className)}>
      <div className="flex items-center justify-between text-gray-400 text-sm">
        <span>{label}</span>
        {icon && <span className="text-accent-blue">{icon}</span>}
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
      <div className="flex items-center gap-2 text-xs">
        {subtitle && <span className="text-gray-500">{subtitle}</span>}
        {trend && (
          <span
            className={clsx(
              "font-medium",
              trend.positive ? "text-accent-green" : "text-accent-red"
            )}
          >
            {trend.positive ? "+" : ""}{trend.value}
          </span>
        )}
      </div>
    </div>
  );
}
