import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Query, HTTPException, Request
from pydantic import BaseModel

from ..config import settings
from ..database import get_supabase
from ..services.whatsapp import get_whatsapp_provider
from ..services import chatwoot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


class TesteRequest(BaseModel):
    telefone: str


@router.post("/test")
async def testar_conexao(body: TesteRequest):
    """
    Envia o template audiencia_trabalhista para o número informado para verificar a integração.
    """
    telefone = body.telefone.strip().lstrip("+")
    if not telefone.isdigit() or len(telefone) < 12:
        raise HTTPException(
            status_code=422,
            detail="Número inválido. Inclua o DDI do Brasil (55) na frente. Ex: 5588981035842",
        )

    provider = get_whatsapp_provider()
    result = await provider.send_message(f"+{telefone}", "")

    if result.get("success"):
        await chatwoot_service.registrar_mensagem_enviada(
            telefone=f"+{telefone}",
            nome="Teste de conexão",
            texto="[Mensagem de teste enviada via painel]",
        )
        return {"ok": True}
    return {"ok": False, "erro": result.get("erro", "Falha no envio")}


@router.get("/webhook")
def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Verificação do webhook pelo Meta Developers.
    O Meta faz um GET nesse endpoint quando você cadastra a URL do webhook.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        logger.info("[Webhook Meta] Verificação concluída com sucesso.")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificação inválido.")


@router.post("/webhook")
async def receber_webhook(request: Request):
    """
    Recebe eventos do Meta Cloud API:
    - Confirmação de entrega (DELIVERED)
    - Leitura (READ)
    - Resposta do cliente (mensagem recebida)

    Quando o cliente responde, busca o lead pelo número e marca como 'respondido'.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido.")

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            # Mensagem recebida do cliente (resposta ao disparo)
            for message in value.get("messages", []):
                telefone_remetente = message.get("from")
                if not telefone_remetente:
                    continue

                texto = message.get("text", {}).get("body", "(mensagem recebida)")
                logger.info(f"[Webhook Meta] Mensagem recebida de {telefone_remetente}")
                _marcar_lead_respondido(telefone_remetente)
                await chatwoot_service.registrar_mensagem_recebida(telefone_remetente, texto)

            # Atualizações de status de entrega/leitura
            for status_update in value.get("statuses", []):
                provider_ref = status_update.get("id")
                status = status_update.get("status")
                logger.info(f"[Webhook Meta] Status atualizado: ref={provider_ref} status={status}")

    return {"status": "ok"}


@router.post("/chatwoot-webhook")
async def chatwoot_webhook(request: Request):
    """
    Recebe eventos do Chatwoot (webhook de saída do inbox juri_api).
    - incoming (0): cliente respondeu → marca lead como respondido
    - outgoing (1): agente respondeu → envia mensagem via WhatsApp
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido.")

    event = body.get("event")
    if event != "message_created":
        return {"status": "ignored"}

    msg_type = body.get("message_type")
    meta = body.get("meta", {})
    phone = (meta.get("sender", {}).get("phone_number") or "").strip()

    if msg_type in ("incoming", 0):
        if phone:
            logger.info(f"[Chatwoot Webhook] Mensagem recebida de {phone}")
            _marcar_lead_respondido(phone)
        return {"status": "ok"}

    if msg_type in ("outgoing", 1):
        if body.get("private"):
            return {"status": "ignored"}
        content = (body.get("content") or "").strip()
        if not content or not phone:
            return {"status": "ignored"}
        from ..services.whatsapp.meta_cloud_provider import send_text_message
        logger.info(f"[Chatwoot Webhook] Agente respondeu para {phone}: {content[:80]}")
        result = await send_text_message(phone, content)
        return {"status": "ok" if result.get("success") else "error"}

    return {"status": "ignored"}


def _marcar_lead_respondido(telefone: str) -> None:
    """
    Busca o lead mais recente com aquele número de telefone e atualiza para 'respondido'.
    Normaliza o número removendo '+' para comparação.
    """
    try:
        sb = get_supabase()
        numero = telefone.lstrip("+")
        numero_com_plus = f"+{numero}"

        # Busca empresa com esse telefone
        result = (
            sb.table("empresas")
            .select("id")
            .or_(f"telefones.cs.{{\"{numero}\"}},telefones.cs.{{\"{numero_com_plus}\"}}")
            .execute()
        )

        if not result.data:
            logger.warning(f"[Webhook Meta] Nenhuma empresa encontrada para {telefone}")
            return

        empresa_ids = [r["id"] for r in result.data]

        # Busca o lead mais recente com status 'enviado' para essa empresa
        lead_result = (
            sb.table("leads")
            .select("id")
            .in_("empresa_id", empresa_ids)
            .eq("status", "enviado")
            .order("enviado_em", desc=True)
            .limit(1)
            .execute()
        )

        if not lead_result.data:
            logger.info(f"[Webhook Meta] Nenhum lead 'enviado' encontrado para {telefone}")
            return

        lead_id = lead_result.data[0]["id"]
        now = datetime.now(timezone.utc).isoformat()

        sb.table("leads").update({
            "status": "respondido",
            "respondido_em": now,
            "updated_at": now,
        }).eq("id", lead_id).execute()

        logger.info(f"[Webhook Meta] Lead {lead_id} marcado como 'respondido' (tel: {telefone})")

    except Exception as exc:
        logger.error(f"[Webhook Meta] Erro ao marcar respondido para {telefone}: {exc}")
