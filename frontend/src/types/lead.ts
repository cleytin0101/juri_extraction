export type LeadStatus = "novo" | "enviado" | "respondido" | "convertido" | "descartado";

export interface Lead {
  lead_id: string;
  status: LeadStatus;
  mensagem_texto: string | null;
  enviado_em: string | null;
  respondido_em: string | null;
  convertido_em: string | null;
  lead_criado_em: string;
  updated_at: string;
  notas: string | null;
  numero_processo: string;
  orgao_julgador: string | null;
  valor_causa: number | null;
  data_audiencia: string;
  tipo_audiencia: string | null;
  resumo_caso: string | null;
  reclamante_nome: string | null;
  empresa_nome: string;
  empresa_cnpj: string | null;
  empresa_telefones: string[] | null;
  empresa_email: string | null;
  vara_nome: string | null;
  vara_codigo: string | null;
}

export interface LeadListResponse {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
}
