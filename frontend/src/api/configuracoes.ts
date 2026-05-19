import client from "./client";

export interface ConfiguracoesData {
  advogado_nome: string;
  advogado_contato: string;
  whatsapp_provider: string;
}

export interface ConfiguracoesUpdate {
  advogado_nome?: string;
  advogado_contato?: string;
}

export async function getConfiguracoes(): Promise<ConfiguracoesData> {
  const { data } = await client.get<ConfiguracoesData>("/configuracoes");
  return data;
}

export async function saveConfiguracoes(body: ConfiguracoesUpdate): Promise<void> {
  await client.post("/configuracoes", body);
}

export async function testWhatsapp(params: {
  telefone: string;
  empresa_nome: string;
  data_audiencia: string;
}): Promise<{ ok: boolean; erro?: string }> {
  const { data } = await client.post<{ ok: boolean; erro?: string }>("/whatsapp/test", params);
  return data;
}
