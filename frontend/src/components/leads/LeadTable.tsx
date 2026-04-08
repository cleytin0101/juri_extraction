import { FilterTabs } from "./FilterTabs";
import { LeadRow } from "./LeadRow";
import { useLeads } from "../../hooks/useLeads";
import { useFilterStore } from "../../store/filterStore";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function LeadTable() {
  const { activeStatus, page, setStatus, setPage } = useFilterStore();
  const { data, isLoading } = useLeads(activeStatus, page);

  const total = data?.total ?? 0;
  const pageSize = data?.page_size ?? 20;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="bg-surface-800 rounded-xl border border-surface-600">
      <div className="flex items-center justify-between p-4 border-b border-surface-600">
        <h3 className="text-white font-semibold">Leads Recentes</h3>
        <FilterTabs active={activeStatus} onChange={setStatus} />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-600 text-gray-500 text-xs uppercase tracking-wide">
              <th className="px-4 py-3 text-left">Empresa</th>
              <th className="px-4 py-3 text-left">Data</th>
              <th className="px-4 py-3 text-left">Tipo</th>
              <th className="px-4 py-3 text-left">Valor</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Ação</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Carregando...
                </td>
              </tr>
            )}
            {!isLoading && (!data?.items || data.items.length === 0) && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Nenhum lead encontrado
                </td>
              </tr>
            )}
            {data?.items?.map((lead) => (
              <LeadRow key={lead.lead_id} lead={lead} />
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-surface-600">
          <span className="text-gray-500 text-xs">
            {total} leads · página {page} de {totalPages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page <= 1}
              className="p-1 rounded hover:bg-surface-700 text-gray-400 disabled:opacity-30"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= totalPages}
              className="p-1 rounded hover:bg-surface-700 text-gray-400 disabled:opacity-30"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
