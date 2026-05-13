import { X, Phone, Mail, FileText, UserCheck, UserX, Building2, Gavel, Calendar } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { StatusBadge } from "./StatusBadge";
import type { Lead } from "../../types/lead";

interface Props {
  lead: Lead;
  onClose: () => void;
}

function fmtValor(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

function fmtData(d: string | null) {
  if (!d) return "—";
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

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-gray-500 text-xs uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-gray-200 text-sm">{value ?? "—"}</p>
    </div>
  );
}

export function LeadDetailModal({ lead, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-surface-800 rounded-2xl w-full max-w-2xl border border-surface-600 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-surface-600">
          <div>
            <h2 className="text-white font-semibold text-lg">{lead.empresa_nome}</h2>
            <p className="text-gray-500 text-xs mt-0.5">{lead.numero_processo}</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={lead.status} />
            <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-5 space-y-5">
          {/* Empresa */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Building2 size={14} className="text-indigo-400" />
              <h3 className="text-white text-xs font-semibold uppercase tracking-wide">Empresa Reclamada</h3>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Nome" value={lead.empresa_nome} />
              <Field label="CNPJ" value={lead.empresa_cnpj ? fmtCnpj(lead.empresa_cnpj) : null} />
              <Field
                label="Telefone(s)"
                value={
                  lead.empresa_telefones?.length
                    ? lead.empresa_telefones.map((t) => (
                        <span key={t} className="inline-flex items-center gap-1 mr-2">
                          <Phone size={11} className="text-yellow-400" /> {t}
                        </span>
                      ))
                    : null
                }
              />
              <Field
                label="Email"
                value={
                  lead.empresa_email ? (
                    <span className="inline-flex items-center gap-1">
                      <Mail size={11} className="text-blue-400" /> {lead.empresa_email}
                    </span>
                  ) : null
                }
              />
            </div>
          </section>

          {/* Processo */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Gavel size={14} className="text-indigo-400" />
              <h3 className="text-white text-xs font-semibold uppercase tracking-wide">Dados do Processo</h3>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Reclamante" value={lead.reclamante_nome} />
              <Field
                label="Representação"
                value={
                  lead.tem_advogado ? (
                    <span className="inline-flex items-center gap-1 text-red-400">
                      <UserCheck size={12} /> Com advogado
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-green-400">
                      <UserX size={12} /> Sem advogado
                    </span>
                  )
                }
              />
              <Field label="Valor da Causa" value={fmtValor(lead.valor_causa)} />
              <Field label="Tipo de Audiência" value={lead.tipo_audiencia} />
              <Field
                label="Data da Audiência"
                value={
                  lead.data_audiencia ? (
                    <span className="inline-flex items-center gap-1">
                      <Calendar size={11} className="text-indigo-400" /> {fmtData(lead.data_audiencia)}
                    </span>
                  ) : null
                }
              />
              <Field label="Órgão Julgador" value={lead.orgao_julgador ?? lead.vara_nome} />
            </div>
          </section>

          {/* Resumo */}
          {lead.resumo_caso && (
            <section>
              <p className="text-gray-500 text-xs uppercase tracking-wide mb-2">Resumo do Caso</p>
              <div className="bg-surface-700 rounded-xl p-3 text-gray-300 text-sm leading-relaxed border border-surface-600">
                {lead.resumo_caso}
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-surface-600">
          <p className="text-gray-600 text-xs">
            Criado: {fmtData(lead.lead_criado_em)}
          </p>
          <div className="flex items-center gap-3">
            {pdfValido(lead) && (
              <a
                href={lead.pdf_url!}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-sm text-gray-300 hover:text-white border border-surface-600 px-3 py-1.5 rounded-lg hover:bg-surface-700 transition-colors"
              >
                <FileText size={14} />
                Ver PDF
              </a>
            )}
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg border border-surface-600 text-gray-300 text-sm hover:bg-surface-700 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
