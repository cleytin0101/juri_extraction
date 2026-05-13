import { useState, useEffect } from "react";
import { Save, CheckCircle, AlertCircle, Loader2, MessageSquare, User } from "lucide-react";
import { getConfiguracoes, saveConfiguracoes } from "../api/configuracoes";

export function Configuracoes() {
  const [advogadoNome, setAdvogadoNome] = useState("");
  const [advogadoContato, setAdvogadoContato] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getConfiguracoes()
      .then((data) => {
        setAdvogadoNome(data.advogado_nome);
        setAdvogadoContato(data.advogado_contato);
      })
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      await saveConfiguracoes({
        advogado_nome: advogadoNome,
        advogado_contato: advogadoContato,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 4000);
    } catch {
      setError("Erro ao salvar. Verifique se o backend está rodando.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-white p-6">
      <div className="max-w-lg mx-auto space-y-6 pt-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Configurações</h1>
          <p className="text-slate-500 text-sm mt-1">Dados usados no template de mensagem WhatsApp.</p>
        </div>

        {/* Dados do advogado */}
        <div className="bg-surface-800/60 rounded-2xl border border-white/5 p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-1.5 bg-indigo-500/10 rounded-lg">
              <User size={16} className="text-indigo-400" />
            </div>
            <h2 className="text-white font-semibold text-sm uppercase tracking-wide">
              Dados do Advogado
            </h2>
          </div>

          <div>
            <label className="text-slate-400 text-sm block mb-1.5">Nome completo</label>
            <input
              type="text"
              placeholder="Dr. João Silva"
              value={advogadoNome}
              onChange={(e) => setAdvogadoNome(e.target.value)}
              className="w-full bg-surface-700 border border-white/5 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
          </div>

          <div>
            <label className="text-slate-400 text-sm block mb-1.5">Contato (WhatsApp / telefone)</label>
            <input
              type="text"
              placeholder="+55 85 99999-9999"
              value={advogadoContato}
              onChange={(e) => setAdvogadoContato(e.target.value)}
              className="w-full bg-surface-700 border border-white/5 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
          </div>
        </div>

        {/* Preview da mensagem */}
        <div className="bg-surface-800/60 rounded-2xl border border-white/5 p-6 space-y-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-1.5 bg-green-500/10 rounded-lg">
              <MessageSquare size={16} className="text-green-400" />
            </div>
            <h2 className="text-white font-semibold text-sm uppercase tracking-wide">
              Preview da Mensagem WhatsApp
            </h2>
          </div>
          <div className="bg-[#0a0f1e] rounded-xl p-4 text-sm text-slate-300 leading-relaxed whitespace-pre-line border border-white/5">
{`Olá, tudo bem?

Sou advogado trabalhista e localizei que a empresa *[EMPRESA]* possui uma audiência trabalhista marcada para o dia *[DATA]*, na [VARA] do TRT-7.

O processo nº [NÚMERO] envolve [RECLAMANTE] e o valor da causa é de *[VALOR]*.

Ofereço assistência jurídica especializada em defesa de empresas em ações trabalhistas. Posso analisar o caso sem compromisso e apresentar uma proposta de honorários.

${advogadoNome || "[SEU NOME]"}
${advogadoContato || "[SEU CONTATO]"}`}
          </div>
        </div>

        {/* Feedback */}
        {saved && (
          <div className="flex items-center gap-2 text-accent-green text-sm bg-accent-green/10 border border-accent-green/20 rounded-xl px-4 py-3">
            <CheckCircle size={16} />
            Configurações salvas com sucesso!
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-accent-red text-sm bg-accent-red/10 border border-accent-red/20 rounded-xl px-4 py-3">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-xl transition-colors"
        >
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {saving ? "Salvando..." : "Salvar Configurações"}
        </button>
      </div>
    </div>
  );
}
