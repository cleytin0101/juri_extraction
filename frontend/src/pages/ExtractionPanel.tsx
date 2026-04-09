import { useState, useMemo } from "react";
import { Download, AlertCircle, CheckCircle, Search } from "lucide-react";
import { usePautas, useExtraction } from "../hooks/useExtraction";

/** Gera lista de datas (yyyy-mm-dd) entre início e fim, excluindo finais de semana */
function workdaysBetween(start: string, end: string): string[] {
  const result: string[] = [];
  const cur = new Date(start + "T00:00:00");
  const last = new Date(end + "T00:00:00");
  while (cur <= last) {
    const dow = cur.getDay();
    if (dow !== 0 && dow !== 6) {
      result.push(cur.toISOString().slice(0, 10));
    }
    cur.setDate(cur.getDate() + 1);
  }
  return result;
}

export function ExtractionPanel() {
  const { data: pautas } = usePautas();
  const { mutate, isPending, isSuccess, isError, data: result } = useExtraction();

  const today = new Date().toISOString().slice(0, 10);
  const [dataInicio, setDataInicio] = useState(today);
  const [dataFim, setDataFim] = useState(today);
  const [selectedVaras, setSelectedVaras] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");

  const filteredVaras = useMemo(() => {
    if (!pautas?.varas) return [];
    const q = search.toLowerCase();
    return pautas.varas.filter((v) => v.nome.toLowerCase().includes(q));
  }, [pautas?.varas, search]);

  const toggleVara = (id: string) => {
    setSelectedVaras((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => setSelectedVaras(new Set(filteredVaras.map((v) => v.id)));
  const clearAll = () => setSelectedVaras(new Set());

  const datas = useMemo(() => workdaysBetween(dataInicio, dataFim), [dataInicio, dataFim]);
  const totalJobs = selectedVaras.size * datas.length;

  const handleExtrair = () => {
    if (selectedVaras.size === 0 || datas.length === 0) return;
    mutate({ vara_ids: Array.from(selectedVaras), datas });
  };

  return (
    <div className="min-h-screen bg-surface-900 text-white p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <h1 className="text-xl font-bold">Extrair Pauta do PJe</h1>

        {/* Período */}
        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-4">
          <h2 className="text-white font-semibold text-sm uppercase tracking-wide text-accent-blue">
            Período
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-gray-400 text-sm block mb-1">Data início</label>
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm block mb-1">Data fim</label>
              <input
                type="date"
                value={dataFim}
                min={dataInicio}
                onChange={(e) => setDataFim(e.target.value)}
                className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
              />
            </div>
          </div>
          {datas.length > 0 && (
            <p className="text-gray-400 text-xs">{datas.length} dia(s) útil(is) selecionado(s)</p>
          )}
        </div>

        {/* Varas */}
        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-white font-semibold text-sm uppercase tracking-wide text-accent-blue">
              Varas ({selectedVaras.size} selecionada{selectedVaras.size !== 1 ? "s" : ""})
            </h2>
            <div className="flex gap-2 text-xs">
              <button onClick={selectAll} className="text-accent-blue hover:underline">
                Todas
              </button>
              <span className="text-gray-600">|</span>
              <button onClick={clearAll} className="text-gray-400 hover:underline">
                Limpar
              </button>
            </div>
          </div>

          {/* Search box */}
          <div className="relative">
            <Search size={14} className="absolute left-3 top-2.5 text-gray-400" />
            <input
              type="text"
              placeholder="Filtrar varas..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-surface-700 border border-surface-600 rounded-lg pl-8 pr-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>

          {/* Checkbox list */}
          <div className="max-h-64 overflow-y-auto space-y-1 pr-1">
            {filteredVaras.map((v) => (
              <label
                key={v.id}
                className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-700 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedVaras.has(v.id)}
                  onChange={() => toggleVara(v.id)}
                  className="accent-accent-blue"
                />
                <span className="text-sm text-gray-200">{v.nome}</span>
              </label>
            ))}
            {filteredVaras.length === 0 && (
              <p className="text-gray-500 text-sm px-3 py-2">Nenhuma vara encontrada</p>
            )}
          </div>
        </div>

        {/* Summary + button */}
        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-4">
          {totalJobs > 0 && (
            <p className="text-gray-300 text-sm">
              <span className="text-white font-semibold">{totalJobs}</span> extração(ões) serão iniciadas
              <span className="text-gray-500 text-xs ml-2">
                ({selectedVaras.size} vara{selectedVaras.size !== 1 ? "s" : ""} × {datas.length} data{datas.length !== 1 ? "s" : ""})
              </span>
            </p>
          )}

          <button
            onClick={handleExtrair}
            disabled={selectedVaras.size === 0 || datas.length === 0 || isPending}
            className="w-full flex items-center justify-center gap-2 bg-accent-blue hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors"
          >
            <Download size={16} />
            {isPending ? "Iniciando extrações..." : "Extrair Pauta"}
          </button>

          {isSuccess && (
            <div className="flex items-start gap-2 text-accent-green text-sm">
              <CheckCircle size={16} className="mt-0.5 shrink-0" />
              <div>
                <p className="font-medium">
                  {result?.jobs_iniciados ?? 0} extração(ões) iniciada(s) em background!
                </p>
                <p className="text-gray-400 text-xs">
                  Acompanhe o progresso no Dashboard.
                </p>
              </div>
            </div>
          )}

          {isError && (
            <div className="flex items-center gap-2 text-accent-red text-sm">
              <AlertCircle size={16} />
              Erro ao iniciar extração. Verifique se o backend está rodando.
            </div>
          )}
        </div>

        {/* Pautas já extraídas */}
        {pautas?.datas_disponiveis && pautas.datas_disponiveis.length > 0 && (
          <div>
            <h3 className="text-gray-400 text-sm mb-2">Pautas já extraídas</h3>
            <div className="flex flex-wrap gap-2">
              {pautas.datas_disponiveis.map((d) => (
                <span
                  key={d}
                  className="px-2 py-1 bg-surface-700 text-gray-300 text-xs rounded border border-surface-600"
                >
                  {d}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
