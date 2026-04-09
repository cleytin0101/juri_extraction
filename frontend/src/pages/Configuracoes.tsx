import { useState, useEffect } from "react";
import { Save, Eye, EyeOff, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { getConfiguracoes, saveConfiguracoes } from "../api/configuracoes";

export function Configuracoes() {
  const [advogadoNome, setAdvogadoNome] = useState("");
  const [advogadoContato, setAdvogadoContato] = useState("");
  const [pjeCpf, setPjeCpf] = useState("");
  const [pjeSenha, setPjeSenha] = useState("");
  const [showSenha, setShowSenha] = useState(false);
  const [senhaConfigurada, setSenhaConfigurada] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getConfiguracoes()
      .then((data) => {
        setAdvogadoNome(data.advogado_nome);
        setAdvogadoContato(data.advogado_contato);
        setPjeCpf(data.pje_cpf);
        setSenhaConfigurada(data.pje_senha_configurada);
      })
      .catch(() => {/* silently ignore load errors */});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError("");
    setSaved(false);
    try {
      await saveConfiguracoes({
        advogado_nome: advogadoNome,
        advogado_contato: advogadoContato,
        pje_cpf: pjeCpf,
        // Only send senha if user typed something new
        ...(pjeSenha ? { pje_senha: pjeSenha } : {}),
      });
      setSaved(true);
      setSenhaConfigurada(senhaConfigurada || !!pjeSenha);
      setPjeSenha("");
      setTimeout(() => setSaved(false), 4000);
    } catch {
      setError("Erro ao salvar. Verifique se o backend está rodando.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-900 text-white p-6">
      <div className="max-w-lg mx-auto space-y-6">
        <h1 className="text-xl font-bold">Configurações</h1>

        {/* Dados do advogado */}
        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-4">
          <h2 className="text-white font-semibold text-sm uppercase tracking-wide text-accent-blue">
            Dados do Advogado
          </h2>
          <p className="text-gray-500 text-xs">
            Usados no template de mensagem WhatsApp enviada às empresas.
          </p>

          <div>
            <label className="text-gray-400 text-sm block mb-1">Nome completo</label>
            <input
              type="text"
              placeholder="Dr. João Silva"
              value={advogadoNome}
              onChange={(e) => setAdvogadoNome(e.target.value)}
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>

          <div>
            <label className="text-gray-400 text-sm block mb-1">Contato (WhatsApp/telefone)</label>
            <input
              type="text"
              placeholder="+55 85 99999-9999"
              value={advogadoContato}
              onChange={(e) => setAdvogadoContato(e.target.value)}
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue"
            />
          </div>
        </div>

        {/* Credenciais PJe */}
        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-4">
          <h2 className="text-white font-semibold text-sm uppercase tracking-wide text-accent-blue">
            Acesso PJe (Advogado)
          </h2>
          <p className="text-gray-500 text-xs">
            Login do advogado no PJe via PDPJ para acessar e baixar os documentos dos processos.
          </p>

          <div>
            <label className="text-gray-400 text-sm block mb-1">CPF do advogado</label>
            <input
              type="text"
              placeholder="000.000.000-00"
              value={pjeCpf}
              onChange={(e) => setPjeCpf(e.target.value)}
              className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-accent-blue font-mono"
            />
          </div>

          <div>
            <label className="text-gray-400 text-sm block mb-1">
              Senha do PJe
              {senhaConfigurada && !pjeSenha && (
                <span className="ml-2 text-accent-green text-xs font-normal">● configurada</span>
              )}
            </label>
            <div className="relative">
              <input
                type={showSenha ? "text" : "password"}
                placeholder={senhaConfigurada ? "••••••• (deixe em branco para manter)" : "••••••••"}
                value={pjeSenha}
                onChange={(e) => setPjeSenha(e.target.value)}
                className="w-full bg-surface-700 border border-surface-600 rounded-lg px-3 py-2 pr-10 text-white text-sm focus:outline-none focus:border-accent-blue"
              />
              <button
                type="button"
                onClick={() => setShowSenha(!showSenha)}
                className="absolute right-3 top-2.5 text-gray-400 hover:text-white"
              >
                {showSenha ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>
        </div>

        {/* Preview da mensagem */}
        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-3">
          <h2 className="text-white font-semibold text-sm uppercase tracking-wide text-accent-blue">
            Preview da Mensagem WhatsApp
          </h2>
          <div className="bg-surface-700 rounded-lg p-4 text-sm text-gray-300 leading-relaxed whitespace-pre-line">
{`Olá, tudo bem?

Sou advogado trabalhista e localizei que a empresa *[EMPRESA]* possui uma audiência trabalhista marcada para o dia *[DATA]*, na [VARA] do TRT-7.

O processo nº [NÚMERO] envolve [RECLAMANTE] e o valor da causa é de *[VALOR]*.

Ofereço assistência jurídica especializada em defesa de empresas em ações trabalhistas. Posso analisar o caso sem compromisso e apresentar uma proposta de honorários.

${advogadoNome || "[SEU NOME]"}
${advogadoContato || "[SEU CONTATO]"}`}
          </div>
        </div>

        {saved && (
          <div className="flex items-center gap-2 text-accent-green text-sm">
            <CheckCircle size={16} />
            Configurações salvas com sucesso!
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-accent-red text-sm">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full flex items-center justify-center gap-2 bg-accent-blue hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors"
        >
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {saving ? "Salvando..." : "Salvar Configurações"}
        </button>
      </div>
    </div>
  );
}
