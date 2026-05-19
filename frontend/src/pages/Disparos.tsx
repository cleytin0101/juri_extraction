import { useState } from "react";
import { Send, CheckSquare, Square, ChevronLeft, ChevronRight, Phone, X } from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { useLeads, useSendLote } from "../hooks/useLeads";
import { StatusBadge } from "../components/leads/StatusBadge";
import type { Lead, LeadStatus } from "../types/lead";
import type { LoteResult } from "../types/documento";

const PAGE_SIZE = 50;

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
    return format(new Date(d), "dd/MM/yy HH:mm", { locale: ptBR });
  } catch {
    return d;
  }
}

interface Filters {
  status: LeadStatus | "";
  valor_min: string;
  valor_max: string;
  data_de: string;
  data_ate: string;
}

const DEFAULT_FILTERS: Filters = {
  status: "novo",
  valor_min: "",
  valor_max: "",
  data_de: "",
  data_ate: "",
};

export function Disparos() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<LoteResult | null>(null);

  const sendLote = useSendLote();

  const { data, isLoading } = useLeads(
    filters.status || undefined,
    page,
    PAGE_SIZE,
    filters.valor_min ? Number(filters.valor_min) : undefined,
    filters.valor_max ? Number(filters.valor_max) : undefined,
    filters.data_de || undefined,
    filters.data_ate || undefined,
  );

  const leads: Lead[] = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const eligibleIds = leads
    .filter((l) => l.empresa_telefones && l.empresa_telefones.length > 0)
    .map((l) => l.lead_id);

  const allPageSelected =
    eligibleIds.length > 0 && eligibleIds.every((id) => selected.has(id));

  function toggleAll() {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allPageSelected) {
        eligibleIds.forEach((id) => next.delete(id));
      } else {
        eligibleIds.forEach((id) => next.add(id));
      }
      return next;
    });
  }

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function handleFilterChange(key: keyof Filters, value: string) {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
    setSelected(new Set());
    setResult(null);
  }

  function handleClearFilters() {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
    setSelected(new Set());
    setResult(null);
  }

  function handleConfirm() {
    sendLote.mutate([...selected], {
      onSuccess: (res) => {
        setResult(res);
        setSelected(new Set());
        setConfirming(false);
      },
    });
  }

  const hasActiveFilters =
    filters.status !== "novo" ||
    filters.valor_min ||
    filters.valor_max ||
    filters.data_de ||
    filters.data_ate;

  return (
    <div className="p-6 space-y-4 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Disparos WhatsApp</h1>
        <span className="text-gray-500 text-sm">{total} leads encontrados</span>
      </div>

      {/* Filtros */}
      <div className="bg-surface-800 rounded-xl border border-surface-600 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-semibold text-gray-400">Filtros</span>
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-white transition-colors"
            >
              <X size={12} /> Limpar filtros
            </button>
          )}
        </div>
        <div className="flex flex-wrap gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange("status", e.target.value)}
              className="bg-surface-700 border border-surface-600 text-white text-sm rounded px-2 py-1.5 min-w-[120px]"
            >
              <option value="">Todos</option>
              <option value="novo">Novo</option>
              <option value="enviado">Enviado</option>
              <option value="respondido">Respondido</option>
              <option value="convertido">Convertido</option>
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Valor mín. (R$)</label>
            <input
              type="number"
              placeholder="0"
              value={filters.valor_min}
              onChange={(e) => handleFilterChange("valor_min", e.target.value)}
              className="bg-surface-700 border border-surface-600 text-white text-sm rounded px-2 py-1.5 w-32"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Valor máx. (R$)</label>
            <input
              type="number"
              placeholder="Sem limite"
              value={filters.valor_max}
              onChange={(e) => handleFilterChange("valor_max", e.target.value)}
              className="bg-surface-700 border border-surface-600 text-white text-sm rounded px-2 py-1.5 w-32"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Audiência de</label>
            <input
              type="date"
              value={filters.data_de}
              onChange={(e) => handleFilterChange("data_de", e.target.value)}
              className="bg-surface-700 border border-surface-600 text-white text-sm rounded px-2 py-1.5"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500">Audiência até</label>
            <input
              type="date"
              value={filters.data_ate}
              onChange={(e) => handleFilterChange("data_ate", e.target.value)}
              className="bg-surface-700 border border-surface-600 text-white text-sm rounded px-2 py-1.5"
            />
          </div>
        </div>
      </div>

      {/* Banner de resultado */}
      {result && (
        <div className="bg-green-900/30 border border-green-700/50 rounded-xl p-4 flex items-start justify-between gap-4">
          <div>
            <p className="text-green-400 font-semibold">Disparo concluído</p>
            <p className="text-gray-300 text-sm mt-1">
              <span className="text-white font-medium">{result.enviados}</span> enviados ·{" "}
              <span className="text-yellow-400">{result.sem_telefone}</span> sem telefone ·{" "}
              <span className="text-red-400">{result.erros}</span> erros — de {result.total} selecionados
            </p>
            {result.detalhes_erros.length > 0 && (
              <details className="mt-2">
                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-300">
                  Ver detalhes dos erros ({result.detalhes_erros.length})
                </summary>
                <ul className="mt-1 space-y-0.5 pl-2">
                  {result.detalhes_erros.map((e) => (
                    <li key={e.lead_id} className="text-xs text-red-400">
                      {e.erro}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
          <button
            onClick={() => setResult(null)}
            className="text-gray-500 hover:text-white transition-colors flex-shrink-0"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Tabela de leads */}
      <div className="bg-surface-800 rounded-xl border border-surface-600">
        {/* Cabeçalho da tabela */}
        <div className="flex items-center justify-between p-4 border-b border-surface-600">
          <div className="flex items-center gap-3">
            <button
              onClick={toggleAll}
              title={allPageSelected ? "Desselecionar página" : "Selecionar todos com telefone nesta página"}
              className="text-gray-400 hover:text-white transition-colors"
            >
              {allPageSelected ? (
                <CheckSquare size={16} className="text-green-400" />
              ) : (
                <Square size={16} />
              )}
            </button>
            <span className="text-white font-semibold text-sm">
              {selected.size > 0
                ? `${selected.size} de ${total} selecionados`
                : `${total} leads`}
            </span>
          </div>

          <button
            onClick={() => setConfirming(true)}
            disabled={selected.size === 0 || sendLote.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm rounded-lg font-medium transition-colors"
          >
            <Send size={14} />
            {selected.size > 0 ? `Disparar (${selected.size})` : "Disparar"}
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-600 text-gray-500 text-xs uppercase tracking-wide">
                <th className="px-4 py-3 text-left w-10"></th>
                <th className="px-4 py-3 text-left">Empresa</th>
                <th className="px-4 py-3 text-left">Audiência</th>
                <th className="px-4 py-3 text-left">Tipo</th>
                <th className="px-4 py-3 text-left">Valor</th>
                <th className="px-4 py-3 text-left">Telefone</th>
                <th className="px-4 py-3 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-gray-500">
                    Carregando...
                  </td>
                </tr>
              )}
              {!isLoading && leads.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-10 text-center text-gray-500">
                    Nenhum lead encontrado com esses filtros
                  </td>
                </tr>
              )}
              {leads.map((lead) => {
                const hasTel =
                  lead.empresa_telefones && lead.empresa_telefones.length > 0;
                const isSelected = selected.has(lead.lead_id);

                return (
                  <tr
                    key={lead.lead_id}
                    onClick={() => hasTel && toggleOne(lead.lead_id)}
                    className={[
                      "border-b border-surface-600 transition-colors",
                      hasTel ? "cursor-pointer" : "cursor-not-allowed opacity-50",
                      isSelected
                        ? "bg-green-900/10"
                        : hasTel
                        ? "hover:bg-surface-700/50"
                        : "",
                    ].join(" ")}
                  >
                    <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => hasTel && toggleOne(lead.lead_id)}
                        disabled={!hasTel}
                        className="text-gray-400 hover:text-white disabled:cursor-not-allowed transition-colors"
                      >
                        {isSelected ? (
                          <CheckSquare size={15} className="text-green-400" />
                        ) : (
                          <Square size={15} />
                        )}
                      </button>
                    </td>

                    <td className="px-4 py-3">
                      <div className="font-medium text-white text-sm">{lead.empresa_nome}</div>
                      <div className="text-gray-500 text-xs">{lead.numero_processo}</div>
                      {lead.reclamante_nome && (
                        <div className="text-gray-500 text-xs">
                          Rec: <span className="text-gray-300">{lead.reclamante_nome}</span>
                        </div>
                      )}
                    </td>

                    <td className="px-4 py-3 text-gray-300 text-sm">
                      {lead.data_audiencia ? fmtData(lead.data_audiencia) : "—"}
                    </td>

                    <td className="px-4 py-3 text-gray-300 text-sm capitalize">
                      {lead.tipo_audiencia ?? "—"}
                    </td>

                    <td className="px-4 py-3 text-accent-blue font-medium text-sm">
                      {fmtValor(lead.valor_causa)}
                    </td>

                    <td className="px-4 py-3">
                      {hasTel ? (
                        <span className="inline-flex items-center gap-1 text-xs text-yellow-400">
                          <Phone size={10} />
                          {lead.empresa_telefones![0]}
                          {lead.empresa_telefones!.length > 1 && (
                            <span className="text-gray-500">
                              +{lead.empresa_telefones!.length - 1}
                            </span>
                          )}
                        </span>
                      ) : (
                        <span className="text-xs text-red-500">Sem telefone</span>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      <StatusBadge status={lead.status} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Paginação */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-surface-600">
            <span className="text-gray-500 text-xs">
              {total} leads · página {page} de {totalPages}
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => p - 1)}
                disabled={page <= 1}
                className="p-1 rounded hover:bg-surface-700 text-gray-400 disabled:opacity-30 transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= totalPages}
                className="p-1 rounded hover:bg-surface-700 text-gray-400 disabled:opacity-30 transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal de confirmação */}
      {confirming && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-800 border border-surface-600 rounded-xl p-6 w-full max-w-sm space-y-4">
            <h2 className="text-white font-semibold text-lg">Confirmar disparo</h2>
            <p className="text-gray-300 text-sm leading-relaxed">
              Você está prestes a enviar{" "}
              <strong className="text-white">{selected.size} mensagens</strong> via
              WhatsApp. Cada empresa receberá uma mensagem personalizada com os dados
              do seu processo.
            </p>
            <p className="text-gray-500 text-xs">
              Esta ação não pode ser desfeita. Os leads serão marcados como "Enviado".
            </p>

            {sendLote.isError && (
              <p className="text-red-400 text-xs bg-red-900/20 px-3 py-2 rounded">
                {String((sendLote.error as Error)?.message ?? "Erro ao enviar")}
              </p>
            )}

            <div className="flex gap-2 pt-1">
              <button
                onClick={handleConfirm}
                disabled={sendLote.isPending}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm rounded-lg font-medium transition-colors"
              >
                <Send size={14} />
                {sendLote.isPending ? "Enviando..." : "Confirmar"}
              </button>
              <button
                onClick={() => setConfirming(false)}
                disabled={sendLote.isPending}
                className="flex-1 py-2.5 bg-surface-700 hover:bg-surface-600 disabled:opacity-50 text-gray-300 text-sm rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
