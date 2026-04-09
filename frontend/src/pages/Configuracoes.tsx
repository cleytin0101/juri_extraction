import { useState, useEffect, useRef } from "react";
import { Save, Eye, EyeOff, CheckCircle, AlertCircle, Loader2, Wifi, WifiOff, KeyRound } from "lucide-react";
import { getConfiguracoes, saveConfiguracoes } from "../api/configuracoes";
import {
  iniciarLogin,
  getLoginStatus,
  submitOtp,
  getConnectionStatus,
} from "../api/auth";
import type { StatusResponse } from "../api/auth";

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

  // Estado da conexão PJe
  const [connected, setConnected] = useState(false);
  const [connectedSince, setConnectedSince] = useState<string | null>(null);
  const [loginStatus, setLoginStatus] = useState<StatusResponse | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [otpCode, setOtpCode] = useState("");
  const [otpError, setOtpError] = useState("");
  const [connecting, setConnecting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getConfiguracoes()
      .then((data) => {
        setAdvogadoNome(data.advogado_nome);
        setAdvogadoContato(data.advogado_contato);
        setPjeCpf(data.pje_cpf);
        setSenhaConfigurada(data.pje_senha_configurada);
      })
      .catch(() => {/* silently ignore load errors */});

    getConnectionStatus()
      .then((data) => {
        setConnected(data.conectado);
        setConnectedSince(data.salvo_em);
      })
      .catch(() => {});
  }, []);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startPolling = (sid: string) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const status = await getLoginStatus(sid);
        setLoginStatus(status);
        if (status.status === "sucesso") {
          stopPolling();
          setConnecting(false);
          setConnected(true);
          setConnectedSince(new Date().toISOString());
          setSessionId(null);
        } else if (status.status === "erro") {
          stopPolling();
          setConnecting(false);
        }
      } catch {
        // ignore transient errors
      }
    }, 2000);
  };

  const handleConectar = async () => {
    setConnecting(true);
    setLoginStatus(null);
    setOtpCode("");
    setOtpError("");
    try {
      const { session_id } = await iniciarLogin(pjeCpf || undefined, pjeSenha || undefined);
      setSessionId(session_id);
      startPolling(session_id);
    } catch {
      setConnecting(false);
      setLoginStatus({ status: "erro", mensagem: "Erro ao iniciar conexão. Backend offline?" });
    }
  };

  const handleSubmitOtp = async () => {
    if (!sessionId || !otpCode.trim()) return;
    setOtpError("");
    const result = await submitOtp(sessionId, otpCode.trim());
    if (!result.ok) {
      setOtpError(result.erro || "Erro ao enviar código.");
    }
    setOtpCode("");
  };

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

        {/* Conexão PJe */}
        <div className="bg-surface-800 rounded-xl border border-surface-600 p-6 space-y-4">
          <h2 className="text-white font-semibold text-sm uppercase tracking-wide text-accent-blue">
            Conexão PJe
          </h2>

          {/* Status */}
          <div className="flex items-center gap-2 text-sm">
            {connected ? (
              <>
                <Wifi size={16} className="text-accent-green" />
                <span className="text-accent-green font-medium">Conectado</span>
                {connectedSince && (
                  <span className="text-gray-500 text-xs ml-1">
                    (sessão salva em {new Date(connectedSince).toLocaleString("pt-BR")})
                  </span>
                )}
              </>
            ) : (
              <>
                <WifiOff size={16} className="text-gray-500" />
                <span className="text-gray-400">Desconectado</span>
              </>
            )}
          </div>

          {/* Progresso / mensagem de status */}
          {loginStatus && (
            <div className={`flex items-start gap-2 text-sm rounded-lg px-3 py-2 ${
              loginStatus.status === "erro"
                ? "bg-red-900/30 text-accent-red"
                : loginStatus.status === "sucesso"
                ? "bg-green-900/30 text-accent-green"
                : "bg-surface-700 text-gray-300"
            }`}>
              {loginStatus.status === "iniciando" && (
                <Loader2 size={14} className="mt-0.5 animate-spin shrink-0" />
              )}
              {loginStatus.status === "aguardando_otp" && (
                <KeyRound size={14} className="mt-0.5 shrink-0 text-yellow-400" />
              )}
              <span>{loginStatus.mensagem}</span>
            </div>
          )}

          {/* Campo OTP — aparece quando o PDPJ pede o código */}
          {loginStatus?.status === "aguardando_otp" && (
            <div className="space-y-2">
              <label className="text-gray-300 text-sm block">
                Código do app autenticador
                <span className="text-gray-500 text-xs ml-2">(muda a cada 30 segundos)</span>
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={8}
                  placeholder="000000"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmitOtp()}
                  className="flex-1 bg-surface-700 border border-yellow-500/50 rounded-lg px-3 py-2 text-white text-sm font-mono tracking-widest focus:outline-none focus:border-yellow-400"
                  autoFocus
                />
                <button
                  onClick={handleSubmitOtp}
                  disabled={otpCode.length < 6}
                  className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
                >
                  Confirmar
                </button>
              </div>
              {otpError && (
                <p className="text-accent-red text-xs flex items-center gap-1">
                  <AlertCircle size={12} /> {otpError}
                </p>
              )}
            </div>
          )}

          <button
            onClick={handleConectar}
            disabled={connecting || loginStatus?.status === "aguardando_otp"}
            className="flex items-center gap-2 px-4 py-2 bg-surface-700 hover:bg-surface-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg border border-surface-500 transition-colors"
          >
            {connecting && loginStatus?.status !== "aguardando_otp" ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Wifi size={14} />
            )}
            {connected ? "Reconectar ao PJe" : "Conectar ao PJe"}
          </button>
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
