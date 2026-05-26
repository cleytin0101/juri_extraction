from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services import lead_service
from ..services.whatsapp import get_whatsapp_provider
from ..services.whatsapp.template import render_mensagem
from ..services import chatwoot_service
from ..config import settings
from ..database import get_supabase

router = APIRouter(prefix="/api/leads", tags=["mensagem"])


class MensagemRequest(BaseModel):
    telefone_override: Optional[str] = None


class LoteRequest(BaseModel):
    lead_ids: List[str]


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
    result = await provider.send_message(telefone, mensagem, lead=lead)

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
        await chatwoot_service.registrar_mensagem_enviada(
            telefone=telefone,
            nome=lead.get("empresa_nome", ""),
            texto=mensagem,
        )

    return {
        "ok": result.get("success"),
        "telefone": telefone,
        "provider_ref": result.get("provider_ref"),
        "mensagem_preview": mensagem[:200] + "..." if len(mensagem) > 200 else mensagem,
    }


@router.post("/mensagem/lote")
async def enviar_mensagem_lote(body: LoteRequest):
    """
    Envia mensagens WhatsApp para uma lista de leads em sequência.
    Retorna relatório com enviados, sem_telefone e erros.
    Cooldown de 24h por número: não reenvia para telefone que já recebeu mensagem recentemente.
    """
    if not body.lead_ids:
        raise HTTPException(status_code=422, detail="Lista de lead_ids vazia.")

    sb = get_supabase()
    provider = get_whatsapp_provider()
    enviados = []
    sem_telefone = []
    erros = []
    ja_contatados = []

    cooldown_desde = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    for lead_id in body.lead_ids:
        lead = lead_service.get_lead_full(lead_id)
        if not lead:
            erros.append({"lead_id": lead_id, "erro": "Lead não encontrado"})
            continue

        telefones: list[str] = lead.get("empresa_telefones") or []
        telefone = telefones[0] if telefones else None

        if not telefone:
            sem_telefone.append(lead_id)
            continue

        # Cooldown: pula se este telefone já recebeu mensagem com sucesso nas últimas 24h
        recente = (
            sb.table("mensagens_log")
            .select("id")
            .eq("telefone", telefone)
            .eq("status", "sent")
            .gte("created_at", cooldown_desde)
            .limit(1)
            .execute()
        )
        if recente.data:
            ja_contatados.append(lead_id)
            continue

        try:
            mensagem = render_mensagem(lead)
            result = await provider.send_message(telefone, mensagem, lead=lead)

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
                enviados.append(lead_id)
                await chatwoot_service.registrar_mensagem_enviada(
                    telefone=telefone,
                    nome=lead.get("empresa_nome", ""),
                    texto=mensagem,
                )
            else:
                erros.append({"lead_id": lead_id, "erro": result.get("erro", "Falha no provider")})
        except Exception as e:
            erros.append({"lead_id": lead_id, "erro": str(e)})

    return {
        "total": len(body.lead_ids),
        "enviados": len(enviados),
        "sem_telefone": len(sem_telefone),
        "ja_contatados": len(ja_contatados),
        "erros": len(erros),
        "detalhes_erros": erros,
    }
