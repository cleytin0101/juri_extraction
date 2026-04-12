from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class Vara(BaseModel):
    id: str
    codigo: str
    nome: str


class ExtrairRequest(BaseModel):
    vara_ids: List[str]
    datas: List[date]


class ExtrairJobStatus(BaseModel):
    key: str
    vara_id: str
    vara_nome: str = ""
    data: date
    status: str  # "running" | "done" | "error"
    processos_encontrados: int = 0
    leads_criados: int = 0
    processos_com_advogado: int = 0
    errors: List[str] = []


class ExtrairResponse(BaseModel):
    jobs_iniciados: int
    keys: List[str]


class PautasResponse(BaseModel):
    varas: List[Vara]
    datas_disponiveis: List[date]
