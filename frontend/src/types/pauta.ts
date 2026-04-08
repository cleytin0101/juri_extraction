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
  vara_id: string;
  data: string;
}

export interface ExtrairResponse {
  processos_encontrados: number;
  leads_criados: number;
  errors: string[];
  vara_id: string;
  data: string;
}
