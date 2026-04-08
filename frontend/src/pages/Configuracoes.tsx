import { useState } from "react";
import { Save, Eye, EyeOff, CheckCircle } from "lucide-react";

export function Configuracoes() {
  const [advogadoNome, setAdvogadoNome] = useState("");
  const [advogadoContato, setAdvogadoContato] = useState("");
  const [pjeCpf, setPjeCpf] = useState("");
  const [pjeSenha, setPjeSenha] = useState("");
  const [showSenha, setShowSenha] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // As credenciais são variáveis de ambiente no backend (Render).
    // Esta tela mostra ao usuário o que precisa configurar lá.
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
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
            Login do advogado no PJe para acessar detalhes dos processos.
            Configure como variáveis de ambiente no Render:
            <span className="text-accent-yellow font-mono"> PJE_CPF</span> e
            <span className="text-accent-yellow font-mono"> PJE_SENHA</span>.
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
            <label className="text-gray-400 text-sm block mb-1">Senha do PJe</label>
            <div className="relative">
              <input
                type={showSenha ? "text" : "password"}
                placeholder="••••••••"
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

          {/* Instruções Render */}
          <div className="bg-surface-700 rounded-lg p-3 text-xs text-gray-400 space-y-1">
            <p className="text-white font-medium mb-2">Como configurar no Render:</p>
            <p>1. Acesse seu serviço <span className="text-accent-blue">juri-backend</span> no Render</p>
            <p>2. Vá em <span className="text-white">Environment → Add Environment Variable</span></p>
            <p>3. Adicione:</p>
            <p className="font-mono text-accent-yellow pl-2">PJE_CPF = seu CPF</p>
            <p className="font-mono text-accent-yellow pl-2">PJE_SENHA = sua senha</p>
            <p className="font-mono text-accent-yellow pl-2">ADVOGADO_NOME = seu nome</p>
            <p className="font-mono text-accent-yellow pl-2">ADVOGADO_CONTATO = seu contato</p>
            <p>4. Clique em <span className="text-white">Save Changes</span> — o serviço reinicia automaticamente</p>
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

${advogadoNome ? advogadoNome : "[SEU NOME]"}
${advogadoContato ? advogadoContato : "[SEU CONTATO]"}`}
          </div>
        </div>

        {saved && (
          <div className="flex items-center gap-2 text-accent-green text-sm">
            <CheckCircle size={16} />
            Salvo! Lembre de configurar as variáveis de ambiente no Render.
          </div>
        )}

        <button
          onClick={handleSave}
          className="w-full flex items-center justify-center gap-2 bg-accent-blue hover:bg-blue-500 text-white font-medium py-2.5 rounded-lg transition-colors"
        >
          <Save size={16} />
          Salvar Configurações
        </button>
      </div>
    </div>
  );
}
