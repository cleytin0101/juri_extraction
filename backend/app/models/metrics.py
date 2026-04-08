from pydantic import BaseModel
from typing import List


class FunnelStep(BaseModel):
    label: str
    count: int
    color: str


class DayCount(BaseModel):
    dia: str
    multiplas: int
    unica: int


class TipoCount(BaseModel):
    tipo: str
    count: int
    color: str


class DashboardMetrics(BaseModel):
    processos_hoje: int
    leads_capturados: int
    audiencias_encontradas: int
    valor_total: float
    funnel: List[FunnelStep]
    audiencias_por_dia: List[DayCount]
    tipos_audiencia: List[TipoCount]
