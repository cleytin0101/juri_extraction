from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..config import settings, save_runtime_credentials

router = APIRouter(prefix="/api/configuracoes", tags=["configuracoes"])


class ConfiguracoesResponse(BaseModel):
    advogado_nome: str
    advogado_contato: str
    whatsapp_provider: str


class ConfiguracoesUpdate(BaseModel):
    advogado_nome: Optional[str] = None
    advogado_contato: Optional[str] = None


@router.get("", response_model=ConfiguracoesResponse)
def get_configuracoes():
    return ConfiguracoesResponse(
        advogado_nome=settings.advogado_nome,
        advogado_contato=settings.advogado_contato,
        whatsapp_provider=settings.whatsapp_provider,
    )


@router.post("")
def post_configuracoes(body: ConfiguracoesUpdate):
    save_runtime_credentials(
        advogado_nome=body.advogado_nome if body.advogado_nome is not None else settings.advogado_nome,
        advogado_contato=body.advogado_contato if body.advogado_contato is not None else settings.advogado_contato,
    )
    return {"ok": True}
