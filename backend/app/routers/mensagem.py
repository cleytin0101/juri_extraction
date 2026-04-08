from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services import lead_service
from ..services.whatsapp import get_whatsapp_provider
from ..services.whatsapp.template import render_mensagem
from ..config import settings

router = APIRouter(prefix="/api/leads", tags=["mensagem"])


class MensagemRequest(BaseModel):
    telefone_override: Optional[str] = None


@router.post("/{lead_id}/mensagem")
async def enviar_mensagem(lead_id: str, body: MensagemRequest = MensagemRequest()):
    lead = lead_service.get_lead_full(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    telefones: list[str] = lead.get("empresa_telefones") or []
    telefone = body.telefone_override or (telefones[0] if telefones else None)

    if not telefone:
        raise HTTPException(
            status_code=422,
            detail="Nenhum telefone disponível. Use 'telefone_override'.",
        )

    mensagem = render_mensagem(lead)
    provider = get_whatsapp_provider()
    result = await provider.send_message(telefone, mensagem)

    lead_service.log_mensagem(
        lead_id=lead_id,
        telefone=telefone,
        mensagem=mensagem,
        provider=settings.whatsapp_provider,
        provider_ref=result.get("provider_ref"),
        status="sent" if result.get("success") else "failed",
        erro=result.get("erro"),
    )

    if result.get("success"):
        lead_service.mark_enviado(lead_id, mensagem)

    return {
        "ok": result.get("success"),
        "telefone": telefone,
        "provider_ref": result.get("provider_ref"),
        "mensagem_preview": mensagem[:200] + "..." if len(mensagem) > 200 else mensagem,
    }
