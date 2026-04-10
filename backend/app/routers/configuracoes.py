from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..config import settings, save_runtime_credentials

router = APIRouter(prefix="/api/configuracoes", tags=["configuracoes"])


class ConfiguracoesResponse(BaseModel):
    advogado_nome: str
    advogado_contato: str
    pje_cpf: str
    pje_senha_configurada: bool  # não retorna a senha, só se está configurada
    whatsapp_provider: str
    infosimples_token_configurado: bool  # não retorna o token, só se está configurado


class ConfiguracoesUpdate(BaseModel):
    advogado_nome: Optional[str] = None
    advogado_contato: Optional[str] = None
    pje_cpf: Optional[str] = None
    pje_senha: Optional[str] = None
    infosimples_token: Optional[str] = None


@router.get("", response_model=ConfiguracoesResponse)
def get_configuracoes():
    return ConfiguracoesResponse(
        advogado_nome=settings.advogado_nome,
        advogado_contato=settings.advogado_contato,
        pje_cpf=settings.pje_cpf,
        pje_senha_configurada=bool(settings.pje_senha),
        whatsapp_provider=settings.whatsapp_provider,
        infosimples_token_configurado=bool(settings.infosimples_token),
    )


@router.post("")
def post_configuracoes(body: ConfiguracoesUpdate):
    save_runtime_credentials(
        pje_cpf=body.pje_cpf if body.pje_cpf is not None else settings.pje_cpf,
        pje_senha=body.pje_senha if body.pje_senha is not None else settings.pje_senha,
        advogado_nome=body.advogado_nome if body.advogado_nome is not None else settings.advogado_nome,
        advogado_contato=body.advogado_contato if body.advogado_contato is not None else settings.advogado_contato,
        infosimples_token=body.infosimples_token if body.infosimples_token is not None else settings.infosimples_token,
    )
    return {"ok": True}
