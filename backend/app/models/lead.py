from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    novo = "novo"
    enviado = "enviado"
    respondido = "respondido"
    convertido = "convertido"
    descartado = "descartado"


class Lead(BaseModel):
    lead_id: str
    status: LeadStatus
    mensagem_texto: Optional[str] = None
    enviado_em: Optional[datetime] = None
    respondido_em: Optional[datetime] = None
    convertido_em: Optional[datetime] = None
    lead_criado_em: datetime
    updated_at: datetime
    notas: Optional[str] = None
    numero_processo: str
    orgao_julgador: Optional[str] = None
    valor_causa: Optional[float] = None
    data_audiencia: datetime
    tipo_audiencia: Optional[str] = None
    resumo_caso: Optional[str] = None
    reclamante_nome: Optional[str] = None
    empresa_nome: str
    empresa_cnpj: Optional[str] = None
    empresa_telefones: Optional[List[str]] = None
    empresa_email: Optional[str] = None
    vara_nome: Optional[str] = None
    vara_codigo: Optional[str] = None


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadListResponse(BaseModel):
    items: List[Lead]
    total: int
    page: int
    page_size: int
