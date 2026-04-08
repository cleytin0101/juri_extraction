import { useState } from "react";
import { MessageCircle } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { StatusBadge } from "./StatusBadge";
import { SendMessageModal } from "./SendMessageModal";
import type { Lead } from "../../types/lead";

function fmtValor(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(v);
}

function fmtData(d: string) {
  try {
    return format(new Date(d), "dd/MM/yyyy HH:mm", { locale: ptBR });
  } catch {
    return d;
  }
}

export function LeadRow({ lead }: { lead: Lead }) {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <tr className="border-b border-surface-600 hover:bg-surface-700/50 transition-colors">
        <td className="px-4 py-3">
          <div className="font-medium text-white text-sm">{lead.empresa_nome}</div>
          <div className="text-gray-500 text-xs">{lead.numero_processo}</div>
        </td>
        <td className="px-4 py-3 text-gray-300 text-sm">{fmtData(lead.data_audiencia)}</td>
        <td className="px-4 py-3 text-gray-300 text-sm capitalize">
          {lead.tipo_audiencia ?? "—"}
        </td>
        <td className="px-4 py-3 text-accent-blue font-medium text-sm">
          {fmtValor(lead.valor_causa)}
        </td>
        <td className="px-4 py-3">
          <StatusBadge status={lead.status} />
        </td>
        <td className="px-4 py-3">
          {lead.status === "novo" && (
            <button
              onClick={() => setShowModal(true)}
              className="flex items-center gap-1 text-xs text-accent-green hover:text-green-300 transition-colors"
            >
              <MessageCircle size={13} />
              Enviar
            </button>
          )}
        </td>
      </tr>

      {showModal && (
        <SendMessageModal lead={lead} onClose={() => setShowModal(false)} />
      )}
    </>
  );
}
