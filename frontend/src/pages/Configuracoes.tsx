import { useState, useEffect } from "react";
import { Save, CheckCircle, AlertCircle, Loader2, MessageSquare, User, Wifi } from "lucide-react";
import { getConfiguracoes, saveConfiguracoes, testWhatsapp } from "../api/configuracoes";

export function Configuracoes() {
  const [advogadoNome, setAdvogadoNome] = useState("");
  const [advogadoContato, setAdvogadoContato] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const [testTelefone, setTestTelefone] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; erro?: string } | null>(null);

  useEffect(() => {
    getConfiguracoes()
      .then((data) => {
        setAdvogadoNome(data.advogado_nome);
        setAdvogadoContato(data.advogado_contato);
      })
      .catch(() => {});
  }, []);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testWhatsapp(testTelefone);
      setTestResult(result);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Erro ao conectar com o backend";
      setTestResult({ ok: false, erro: msg });
    } finally {
      setTesting(false);
    }
  };

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

Somos o escritório Queiroz & Santos Advocacia, especialistas em assessoria jurídica empresarial aqui da região.

Ao analisar publicações recentes da Justiça do Trabalho, vimos que a empresa de vocês possui uma audiência marcada para os próximos dias.

Como atuamos somente na defesa de empresas, resolvemos entrar em contato caso ainda não estejam sendo assessorados no processo.

Se já estiverem acompanhados de advogado, agradeço desde já a atenção. Mas, caso tenham interesse, podemos explicar rapidamente como funciona nosso trabalho.

Instagram profissional: @queirozesantosadvocacia`}
          </div>
        </div>

        {/* Teste de conexão WhatsApp */}
        <div className="bg-surface-800/60 rounded-2xl border border-white/5 p-6 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-1.5 bg-blue-500/10 rounded-lg">
              <Wifi size={16} className="text-blue-400" />
            </div>
            <h2 className="text-white font-semibold text-sm uppercase tracking-wide">
              Testar Conexão WhatsApp
            </h2>
          </div>
          <p className="text-slate-500 text-xs leading-relaxed">
            Envia o template real para o seu número. Confirma que a integração está funcionando de ponta a ponta.
          </p>

          <div className="space-y-3">
            <div>
              <label className="text-slate-400 text-xs block mb-1">Seu número (com DDI 55)</label>
              <input
                type="text"
                placeholder="5588981035842"
                value={testTelefone}
                onChange={(e) => { setTestTelefone(e.target.value); setTestResult(null); }}
                className="w-full bg-surface-700 border border-white/5 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500/50 transition-colors font-mono"
              />
              <p className="text-slate-600 text-xs mt-1">Inclua o 55 do Brasil. Ex: <span className="font-mono text-slate-500">5588981035842</span></p>
            </div>

            <button
              onClick={handleTest}
              disabled={testing || testTelefone.trim().length < 12}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm rounded-xl font-medium transition-colors"
            >
              {testing ? <Loader2 size={14} className="animate-spin" /> : <Wifi size={14} />}
              {testing ? "Enviando..." : "Enviar mensagem de teste para meu WhatsApp"}
            </button>
          </div>

          {testResult && (
            testResult.ok ? (
              <div className="flex items-center gap-2 text-green-400 text-sm bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-3">
                <CheckCircle size={15} />
                Mensagem enviada! Verifique o seu WhatsApp.
              </div>
            ) : (
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
                  <AlertCircle size={15} />
                  Falha no envio. Verifique as credenciais no .env do backend.
                </div>
                {testResult.erro && (
                  <p className="text-xs text-red-400/70 px-1 font-mono break-all">{testResult.erro}</p>
                )}
              </div>
            )
          )}
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
