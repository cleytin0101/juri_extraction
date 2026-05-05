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

// Retry automático em 502/503: o Render free tier dorme após inatividade e
// demora ~50s para acordar — retentamos 4× com 12s de espera (48s total).
const TRANSIENT_STATUSES = new Set([502, 503]);
const MAX_RETRIES = 4;
const RETRY_DELAY_MS = 12_000;

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const status: number | undefined = error.response?.status;
    const cfg = error.config as typeof error.config & { _retryCount?: number };
    if (status && TRANSIENT_STATUSES.has(status)) {
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
