import axios from "axios";

// Em produção (Render), VITE_API_URL aponta para o backend.
// Em desenvolvimento local, usa proxy do vite.config.ts ("/api" → localhost:8000).
const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

const client = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  // Sem timeout o Render pode segurar a conexão por 15+ min antes de retornar 502.
  // Com 15s abortamos cedo e o retry cobre o cold start (~60s) em 4 tentativas.
  timeout: 15_000,
});

// Retry automático em falhas transientes:
// - 502/503: Render retornou erro de gateway
// - ECONNABORTED: timeout de 15s atingido (servidor dormindo ou lento)
// - sem resposta (net::ERR_*): servidor reiniciando, conexão recusada/resetada
// 4 retries × (15s timeout + 5s espera) ≈ 80s total — cobre o cold start do Render (~60s).
const TRANSIENT_STATUSES = new Set([502, 503]);
const MAX_RETRIES = 4;
const RETRY_DELAY_MS = 5_000;

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const status: number | undefined = error.response?.status;
    const isTimeout = error.code === "ECONNABORTED";
    const isNetworkError = !error.response && error.request;
    const isTransient =
      (status && TRANSIENT_STATUSES.has(status)) || isTimeout || isNetworkError;
    const cfg = error.config as typeof error.config & { _retryCount?: number };
    if (isTransient && cfg) {
      cfg._retryCount = (cfg._retryCount ?? 0) + 1;
      if (cfg._retryCount <= MAX_RETRIES) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        return client(cfg);
      }
    }
    return Promise.reject(error);
  }
);

export default client;
