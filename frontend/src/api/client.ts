import axios from "axios";

// Em produção (Render), VITE_API_URL aponta para o backend.
// Em desenvolvimento local, usa proxy do vite.config.ts ("/api" → localhost:8000).
const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

const client = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

// Retry automático em falhas transientes:
// - 502/503: Render free tier dormindo (cold start ~50s) ou redeploy em andamento
// - sem resposta (net::ERR_*): servidor reiniciando, conexão recusada/resetada
// Retentamos 4× com 12s de espera (48s total).
const TRANSIENT_STATUSES = new Set([502, 503]);
const MAX_RETRIES = 4;
const RETRY_DELAY_MS = 12_000;

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const status: number | undefined = error.response?.status;
    const isNetworkError = !error.response && error.request;
    const isTransient = (status && TRANSIENT_STATUSES.has(status)) || isNetworkError;
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
