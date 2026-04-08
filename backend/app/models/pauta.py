from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class Vara(BaseModel):
    id: str
    codigo: str
    nome: str


class ExtrairRequest(BaseModel):
    vara_id: str
    data: date


class ExtrairResponse(BaseModel):
    processos_encontrados: int
    leads_criados: int
    errors: List[str]
    vara_id: str
    data: date


class PautasResponse(BaseModel):
    varas: List[Vara]
    datas_disponiveis: List[date]
