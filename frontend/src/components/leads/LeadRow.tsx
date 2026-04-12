import { useState } from "react";
import { MessageCircle, FileText, UserCheck, UserX } from "lucide-react";
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

function pdfValido(lead: Lead): boolean {
  if (!lead.pdf_url || !lead.pdf_expires_at) return false;
  return new Date(lead.pdf_expires_at) > new Date();
}

export function LeadRow({ lead }: { lead: Lead }) {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <tr className="border-b border-surface-600 hover:bg-surface-700/50 transition-colors">
        <td className="px-4 py-3">
          <div className="font-medium text-white text-sm">{lead.empresa_nome}</div>
          <div className="text-gray-500 text-xs">{lead.numero_processo}</div>
          {/* Badge: tem advogado */}
          {lead.tem_advogado ? (
            <span className="inline-flex items-center gap-1 mt-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-red-900/40 text-red-400">
              <UserCheck size={10} /> Com advogado
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 mt-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-900/30 text-green-400">
              <UserX size={10} /> Sem advogado
            </span>
          )}
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
          <div className="flex items-center gap-2">
            {pdfValido(lead) && (
              <a
                href={lead.pdf_url!}
                target="_blank"
                rel="noopener noreferrer"
                title="Ver PDF do processo (válido por 24h)"
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
              >
                <FileText size={13} />
                PDF
              </a>
            )}
            {lead.status === "novo" && !lead.tem_advogado && (
              <button
                onClick={() => setShowModal(true)}
                className="flex items-center gap-1 text-xs text-accent-green hover:text-green-300 transition-colors"
              >
                <MessageCircle size={13} />
                Enviar
              </button>
            )}
          </div>
        </td>
      </tr>

      {showModal && (
        <SendMessageModal lead={lead} onClose={() => setShowModal(false)} />
      )}
    </>
  );
}
