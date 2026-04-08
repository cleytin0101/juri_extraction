import clsx from "clsx";
import type { LeadStatus } from "../../types/lead";

const CONFIG: Record<LeadStatus, { label: string; cls: string }> = {
  novo: { label: "Novo", cls: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  enviado: { label: "Enviado", cls: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  respondido: { label: "Respondido", cls: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  convertido: { label: "Convertido", cls: "bg-green-500/20 text-green-400 border-green-500/30" },
  descartado: { label: "Descartado", cls: "bg-gray-500/20 text-gray-400 border-gray-500/30" },
};

export function StatusBadge({ status }: { status: LeadStatus }) {
  const cfg = CONFIG[status] ?? CONFIG.novo;
  return (
    <span
      className={clsx(
        "px-2 py-0.5 rounded text-xs font-medium border",
        cfg.cls
      )}
    >
      {cfg.label}
    </span>
  );
}
