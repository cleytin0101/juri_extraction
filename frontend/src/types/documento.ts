export type DocumentoStatus = "criado" | "ja_existe" | "tem_advogado" | "erro";

export interface DocumentoProcessado {
  filename: string;
  numero_processo: string | null;
  empresa_nome: string | null;
  empresa_cnpj: string | null;
  reclamante_nome: string | null;
  telefone: string | null;
  telefone_fonte: "cnpj_ws" | "documento" | null;
  valor_causa: number | null;
  resumo_caso: string | null;
  tem_advogado: boolean;
  lead_id: string | null;
  status: DocumentoStatus;
  erro_msg: string | null;
}

export interface LoteRequest {
  lead_ids: string[];
}

export interface LoteResult {
  total: number;
  enviados: number;
  sem_telefone: number;
  erros: number;
  detalhes_erros: { lead_id: string; erro: string }[];
}
