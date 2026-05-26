import { useState } from "react";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { useFilterStore } from "../../store/filterStore";
import { useVaras } from "../../hooks/useLeads";

export function LeadFilters() {
  const [open, setOpen] = useState(false);
  const {
    orgaoJulgador, valorMin, valorMax, dataAudienciaDe, dataAudienciaAte,
    setOrgaoJulgador, setValorMin, setValorMax,
    setDataAudienciaDe, setDataAudienciaAte, clearFilters,
  } = useFilterStore();

  const { data: varas = [] } = useVaras();

  const hasFilters = !!(orgaoJulgador || valorMin || valorMax || dataAudienciaDe || dataAudienciaAte);

  return (
    <div className="text-sm">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors"
      >
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        Filtros avançados
        {hasFilters && (
          <span className="ml-1 px-1.5 py-0.5 text-xs bg-indigo-500/20 text-indigo-300 rounded-full border border-indigo-500/30">
            ativos
          </span>
        )}
      </button>

      {open && (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Vara */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500 uppercase tracking-wide">Vara</label>
            <select
              value={orgaoJulgador ?? ""}
              onChange={(e) => setOrgaoJulgador(e.target.value || undefined)}
              className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="">Todas as varas</option>
              {varas.map((v) => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>

          {/* Valor mínimo */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500 uppercase tracking-wide">Valor mín. (R$)</label>
            <input
              type="number"
              min={0}
              placeholder="0"
              value={valorMin ?? ""}
              onChange={(e) => setValorMin(e.target.value ? Number(e.target.value) : undefined)}
              className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Valor máximo */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500 uppercase tracking-wide">Valor máx. (R$)</label>
            <input
              type="number"
              min={0}
              placeholder="sem limite"
              value={valorMax ?? ""}
              onChange={(e) => setValorMax(e.target.value ? Number(e.target.value) : undefined)}
              className="bg-surface-700 border border-surface-600 rounded-lg px-3 py-1.5 text-white text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Intervalo de data */}
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500 uppercase tracking-wide">Audiência — período</label>
            <div className="flex gap-1">
              <input
                type="date"
                value={dataAudienciaDe ?? ""}
                onChange={(e) => setDataAudienciaDe(e.target.value || undefined)}
                className="flex-1 bg-surface-700 border border-surface-600 rounded-lg px-2 py-1.5 text-white text-xs focus:outline-none focus:border-indigo-500"
              />
              <span className="text-slate-500 self-center">–</span>
              <input
                type="date"
                value={dataAudienciaAte ?? ""}
                onChange={(e) => setDataAudienciaAte(e.target.value || undefined)}
                className="flex-1 bg-surface-700 border border-surface-600 rounded-lg px-2 py-1.5 text-white text-xs focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {hasFilters && (
            <div className="flex items-end sm:col-span-2 lg:col-span-4">
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors"
              >
                <X size={12} />
                Limpar filtros
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
