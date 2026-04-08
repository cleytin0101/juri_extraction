import { useState } from "react";
import { Download, AlertCircle, CheckCircle } from "lucide-react";
import { usePautas, useExtraction } from "../hooks/useExtraction";

export function ExtractionPanel() {
  const { data: pautas } = usePautas();
  const { mutate, isPending, isSuccess, isError, data: result } = useExtraction();
  const [varaId, setVaraId] = useState("");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));

  const handleExtrair = () => {
    if (!varaId || !data) return;
    mutate({ vara_id: varaId, data });
  };

  return (
    <div className="min-h-screen bg-surface-900 text-white p-6">
      <div className="max-w-lg mx-auto">
        <h1 className="text-xl font-bold mb-6">Extrair Pauta do PJe</h1>

        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-4">
          <div>
            <label className="text-gray-400 text-sm block mb-1">Vara / Órgão Julgador</label>
            <select
              value={varaId}
              onChange={(e) => setVaraId(e.target.value)}
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
            >
              <option value="">Selecionar vara...</option>
              {pautas?.varas.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.nome}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-gray-400 text-sm block mb-1">Data da Pauta</label>
            <input
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>

          <button
            onClick={handleExtrair}
            disabled={!varaId || !data || isPending}
            className="w-full flex items-center justify-center gap-2 bg-accent-blue hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors"
          >
            <Download size={16} />
            {isPending ? "Extraindo em background..." : "Extrair Pauta"}
          </button>

          {isSuccess && (
            <div className="flex items-start gap-2 text-accent-green text-sm">
              <CheckCircle size={16} className="mt-0.5 shrink-0" />
              <div>
                <p className="font-medium">Extração iniciada!</p>
                <p className="text-gray-400 text-xs">
                  O processo roda em background. Acompanhe no dashboard.
                </p>
              </div>
            </div>
          )}

          {isError && (
            <div className="flex items-center gap-2 text-accent-red text-sm">
              <AlertCircle size={16} />
              Erro ao iniciar extração. Verifique o backend.
            </div>
          )}
        </div>

        {pautas?.datas_disponiveis && pautas.datas_disponiveis.length > 0 && (
          <div className="mt-6">
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
