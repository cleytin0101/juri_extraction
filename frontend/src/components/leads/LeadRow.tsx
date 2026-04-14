import { useState } from "react";
import { MessageCircle, FileText, UserCheck, UserX, Phone } from "lucide-react";
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

function fmtCnpj(cnpj: string) {
  const d = cnpj.replace(/\D/g, "");
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
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
          {/* Reclamante */}
          {lead.reclamante_nome && (
            <div className="text-gray-500 text-xs mt-1">
              Reclamante: <span className="text-gray-300">{lead.reclamante_nome}</span>
            </div>
          )}
          {/* CNPJ */}
          {lead.empresa_cnpj && (
            <div className="text-gray-500 text-xs">
              CNPJ: <span className="text-gray-300">{fmtCnpj(lead.empresa_cnpj)}</span>
            </div>
          )}
          {/* Telefones */}
          {lead.empresa_telefones && lead.empresa_telefones.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {lead.empresa_telefones.slice(0, 3).map((tel, i) => (
                <span key={i} className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-yellow-900/30 text-yellow-400">
                  <Phone size={9} /> {tel}
                  <span className="text-gray-500 ml-0.5">via CNPJ</span>
                </span>
              ))}
              {lead.empresa_telefones.length > 3 && (
                <span className="text-[10px] text-gray-500">+{lead.empresa_telefones.length - 3}</span>
              )}
            </div>
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
