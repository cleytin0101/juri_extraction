import { useState } from "react";
import { X, Send } from "lucide-react";
import { useSendMensagem } from "../../hooks/useLeads";
import type { Lead } from "../../types/lead";

interface Props {
  lead: Lead;
  onClose: () => void;
}

export function SendMessageModal({ lead, onClose }: Props) {
  const telefones = lead.empresa_telefones ?? [];
  const [selected, setSelected] = useState(telefones[0] ?? "");
  const [custom, setCustom] = useState("");
  const { mutate, isPending, isSuccess, isError } = useSendMensagem();

  const finalTelefone = custom.trim() || selected;

  const handleSend = () => {
    mutate({ leadId: lead.lead_id, telefone: finalTelefone });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-surface-800 rounded-2xl p-6 w-full max-w-lg border border-surface-600 shadow-2xl">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-white font-semibold text-lg">Enviar Mensagem WhatsApp</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X size={20} />
          </button>
        </div>

        <div className="mb-4">
          <p className="text-gray-400 text-sm mb-1">Empresa</p>
          <p className="text-white font-medium">{lead.empresa_nome}</p>
        </div>

        {telefones.length > 0 && (
          <div className="mb-4">
            <p className="text-gray-400 text-sm mb-2">Telefones disponíveis</p>
            <div className="flex flex-wrap gap-2">
              {telefones.map((t) => (
                <button
                  key={t}
                  onClick={() => { setSelected(t); setCustom(""); }}
                  className={`px-3 py-1 rounded text-sm border transition-colors ${
                    selected === t && !custom
                      ? "bg-accent-blue/20 border-accent-blue text-accent-blue"
                      : "border-surface-600 text-gray-300 hover:border-gray-400"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mb-5">
          <label className="text-gray-400 text-sm block mb-1">
            Ou digitar número manualmente
          </label>
          <input
            type="text"
            placeholder="+5585999999999"
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
          />
        </div>

        <div className="mb-5 bg-surface-700 rounded-lg p-3 text-gray-300 text-xs leading-relaxed max-h-32 overflow-y-auto">
          <p className="text-gray-500 text-xs mb-1 uppercase tracking-wide">Pré-visualização</p>
          <p>Olá, tudo bem? Sou advogado trabalhista e localizei que a empresa <strong>{lead.empresa_nome}</strong> possui uma audiência... (mensagem completa será enviada pelo backend)</p>
        </div>

        {isSuccess && (
          <p className="text-accent-green text-sm mb-3">Mensagem enviada com sucesso!</p>
        )}
        {isError && (
          <p className="text-accent-red text-sm mb-3">Erro ao enviar. Tente novamente.</p>
        )}

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-surface-600 text-gray-300 text-sm hover:bg-surface-700"
          >
            Cancelar
          </button>
          <button
            onClick={handleSend}
            disabled={!finalTelefone || isPending || isSuccess}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-green text-black text-sm font-medium hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={14} />
            {isPending ? "Enviando..." : "Confirmar Envio"}
          </button>
        </div>
      </div>
    </div>
  );
}
