from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..config import settings

router = APIRouter(prefix="/api/configuracoes", tags=["configuracoes"])


class ConfiguracoesResponse(BaseModel):
    advogado_nome: str
    advogado_contato: str
    pje_cpf: str
    pje_senha_configurada: bool  # não retorna a senha, só se está configurada
    whatsapp_provider: str


class ConfiguracoesUpdate(BaseModel):
    advogado_nome: Optional[str] = None
    advogado_contato: Optional[str] = None
    pje_cpf: Optional[str] = None
    pje_senha: Optional[str] = None


@router.get("", response_model=ConfiguracoesResponse)
def get_configuracoes():
    return ConfiguracoesResponse(
        advogado_nome=settings.advogado_nome,
        advogado_contato=settings.advogado_contato,
        pje_cpf=settings.pje_cpf,
        pje_senha_configurada=bool(settings.pje_senha),
        whatsapp_provider=settings.whatsapp_provider,
    )
