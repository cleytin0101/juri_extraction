import client from "./client";

export interface ConfiguracoesData {
  advogado_nome: string;
  advogado_contato: string;
  pje_cpf: string;
  pje_senha_configurada: boolean;
  whatsapp_provider: string;
  infosimples_token_configurado: boolean;
}

export interface ConfiguracoesUpdate {
  advogado_nome?: string;
  advogado_contato?: string;
  pje_cpf?: string;
  pje_senha?: string;
  infosimples_token?: string;
}

export async function getConfiguracoes(): Promise<ConfiguracoesData> {
  const { data } = await client.get<ConfiguracoesData>("/configuracoes");
  return data;
}

export async function saveConfiguracoes(body: ConfiguracoesUpdate): Promise<void> {
  await client.post("/configuracoes", body);
}
