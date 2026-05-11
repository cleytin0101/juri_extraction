from typing import Optional, Literal
from pydantic import BaseModel


class DocumentoProcessado(BaseModel):
    filename: str
    numero_processo: Optional[str] = None
    empresa_nome: Optional[str] = None
    empresa_cnpj: Optional[str] = None
    reclamante_nome: Optional[str] = None
    telefone: Optional[str] = None
    telefone_fonte: Optional[Literal["cnpj_ws", "documento"]] = None
    valor_causa: Optional[float] = None
    resumo_caso: Optional[str] = None
    tem_advogado: bool = False
    lead_id: Optional[str] = None
    status: Literal["criado", "ja_existe", "tem_advogado", "erro"] = "erro"
    erro_msg: Optional[str] = None
