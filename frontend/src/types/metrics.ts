export interface FunnelStep {
  label: string;
  count: number;
  color: string;
}

export interface DayCount {
  dia: string;
  multiplas: number;
  unica: number;
}

export interface TipoCount {
  tipo: string;
  count: number;
  color: string;
}

export interface DashboardMetrics {
  processos_hoje: number;
  leads_capturados: number;
  audiencias_encontradas: number;
  valor_total: number;
  funnel: FunnelStep[];
  audiencias_por_dia: DayCount[];
  tipos_audiencia: TipoCount[];
}
