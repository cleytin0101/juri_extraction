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

export default client;
