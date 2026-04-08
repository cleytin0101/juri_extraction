import clsx from "clsx";
import type { LeadStatus } from "../../types/lead";

const TABS: { label: string; value: LeadStatus | undefined }[] = [
  { label: "Todos", value: undefined },
  { label: "Novo", value: "novo" },
  { label: "Enviado", value: "enviado" },
  { label: "Respondido", value: "respondido" },
  { label: "Convertido", value: "convertido" },
];

interface Props {
  active: LeadStatus | undefined;
  onChange: (s: LeadStatus | undefined) => void;
}

export function FilterTabs({ active, onChange }: Props) {
  return (
    <div className="flex gap-1 bg-surface-700 rounded-lg p-1">
      {TABS.map((tab) => (
        <button
          key={tab.label}
          onClick={() => onChange(tab.value)}
          className={clsx(
            "px-4 py-1.5 rounded text-sm font-medium transition-colors",
            active === tab.value
              ? "bg-surface-800 text-white shadow"
              : "text-gray-400 hover:text-white"
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
