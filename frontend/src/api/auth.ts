import client from "./client";

export interface StatusResponse {
  status: "iniciando" | "aguardando_otp" | "sucesso" | "erro";
  mensagem: string;
}

export interface ConnectionStatusResponse {
  conectado: boolean;
  salvo_em: string | null;
}

export async function iniciarLogin(cpf?: string, senha?: string): Promise<{ session_id: string }> {
  const { data } = await client.post("/auth/pdpj/iniciar", { cpf, senha });
  return data;
}

export async function getLoginStatus(sessionId: string): Promise<StatusResponse> {
  const { data } = await client.get(`/auth/pdpj/status/${sessionId}`);
  return data;
}

export async function submitOtp(sessionId: string, codigo: string): Promise<{ ok: boolean; erro?: string }> {
  const { data } = await client.post("/auth/pdpj/submit-otp", { session_id: sessionId, codigo });
  return data;
}

export async function getConnectionStatus(): Promise<ConnectionStatusResponse> {
  const { data } = await client.get("/auth/pdpj/connection-status");
  return data;
}
