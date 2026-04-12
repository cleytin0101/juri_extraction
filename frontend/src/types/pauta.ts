export interface Vara {
  id: string;
  codigo: string;
  nome: string;
}

export interface PautasResponse {
  varas: Vara[];
  datas_disponiveis: string[];
}

export interface ExtrairRequest {
  vara_ids: string[];
  datas: string[];
}

export interface ExtrairResponse {
  jobs_iniciados: number;
  keys: string[];
}

export interface ExtrairJobStatus {
  key: string;
  vara_id: string;
  data: string;
  status: "running" | "done" | "error";
  processos_encontrados: number;
  leads_criados: number;
  processos_com_advogado: number;
  errors: string[];
}
