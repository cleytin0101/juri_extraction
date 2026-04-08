import type { FunnelStep } from "../../types/metrics";

interface Props {
  steps: FunnelStep[];
}

export function FunnelChart({ steps }: Props) {
  const max = Math.max(...steps.map((s) => s.count), 1);

  return (
    <div className="bg-surface-800 rounded-xl p-5 border border-surface-600">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Funil de Conversão</h3>
      <div className="flex flex-col gap-3">
        {steps.map((step) => (
          <div key={step.label} className="flex items-center gap-3">
            <div className="w-40 text-xs text-gray-300 truncate">{step.label}</div>
            <div className="flex-1 h-6 bg-surface-700 rounded overflow-hidden">
              <div
                className="h-full rounded transition-all duration-500"
                style={{
                  width: `${(step.count / max) * 100}%`,
                  backgroundColor: step.color,
                  opacity: 0.85,
                }}
              />
            </div>
            <div
              className="w-10 text-right text-sm font-bold"
              style={{ color: step.color }}
            >
              {step.count}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
