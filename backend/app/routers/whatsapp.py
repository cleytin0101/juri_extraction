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

                _marcar_lead_respondido(telefone_remetente)
                tipo = message.get("type", "text")
                logger.info(f"[Webhook Meta] Mensagem recebida de {telefone_remetente} tipo={tipo}")

                if tipo == "text":
                    texto = message.get("text", {}).get("body", "") or "(mensagem recebida)"
                    await chatwoot_service.registrar_mensagem_recebida(telefone_remetente, texto)
                elif tipo in ("audio", "image", "video", "document", "sticker"):
                    media_id = (message.get(tipo) or {}).get("id")
                    caption = (message.get("image") or message.get("video") or {}).get("caption", "")
                    filename = (message.get("document") or {}).get("filename", "")
                    if media_id:
                        await chatwoot_service.registrar_midia_recebida(
                            telefone=telefone_remetente,
                            media_id=media_id,
                            tipo=tipo,
                            caption=caption,
                            filename=filename,
                        )
                    else:
                        await chatwoot_service.registrar_mensagem_recebida(telefone_remetente, f"[{tipo} recebido]")
                else:
                    await chatwoot_service.registrar_mensagem_recebida(telefone_remetente, f"[{tipo} recebido]")

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
        attachments = body.get("attachments") or []
        if not content and not attachments:
            return {"status": "ignored"}
        # telefone do contato pode estar em meta.sender OU conversation.meta.sender
        conv_meta = body.get("conversation", {}).get("meta", {})
        phone = phone or (conv_meta.get("sender", {}).get("phone_number") or "").strip()
        logger.info(f"[Chatwoot Webhook] Outgoing — phone={phone!r} content={content[:60]!r} attachments={len(attachments)}")
        if not phone:
            logger.warning("[Chatwoot Webhook] Mensagem outgoing sem telefone do contato")
            return {"status": "no_phone"}
        if attachments:
            logger.info(f"[Chatwoot Webhook] Attachments recebidos: {[{k: v for k, v in a.items() if k in ('file_type', 'extension', 'data_url')} for a in attachments]}")
            for att in attachments:
                att_url = att.get("data_url", "")
                file_type = att.get("file_type", "document")
                ext = att.get("extension", "")
                if att_url:
                    result = await _send_attachment_to_whatsapp(phone, att_url, file_type, ext)
                    logger.info(f"[Chatwoot Webhook] Attachment {file_type} → {phone}: {result}")
        if content:
            from ..services.whatsapp.meta_cloud_provider import send_text_message
            result = await send_text_message(phone, content)
            logger.info(f"[Chatwoot Webhook] Resultado envio texto para {phone}: {result}")
        return {"status": "ok"}

    return {"status": "ignored"}


_EXT_MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp",
    "mp4": "video/mp4", "3gp": "video/3gpp",
    "ogg": "audio/ogg", "mp3": "audio/mpeg", "aac": "audio/aac",
    "amr": "audio/amr", "m4a": "audio/mp4", "webm": "video/webm",
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def _send_attachment_to_whatsapp(phone: str, chatwoot_url: str, file_type: str, ext: str) -> dict:
    """Baixa attachment do Chatwoot e envia via Meta Cloud API para o WhatsApp do cliente."""
    import httpx as _httpx

    logger.info(f"[CW→WA] Iniciando: file_type={file_type!r} ext={ext!r} url={chatwoot_url[:100]!r}")

    # WebM não é suportado pelo WhatsApp para áudio
    if file_type == "audio" and ext.lower() == "webm":
        logger.warning("[CW→WA] Formato WebM não suportado pelo WhatsApp — áudio não enviado")
        return {"success": False, "erro": "Formato WebM não suportado pelo WhatsApp. Envie em OGG, MP3 ou AAC."}

    cw_headers = {"api_access_token": settings.chatwoot_api_token}
    try:
        async with _httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            dl = await client.get(chatwoot_url, headers=cw_headers)
        if not dl.is_success:
            return {"success": False, "erro": f"download falhou: {dl.status_code}"}
        file_bytes = dl.content
        mime_type = _EXT_MIME.get(ext.lower(), "application/octet-stream")
        logger.info(f"[CW→WA] Baixados {len(file_bytes)} bytes de Chatwoot, mime={mime_type}, ext={ext}")
    except Exception as exc:
        return {"success": False, "erro": f"download error: {exc}"}

    meta_auth = {"Authorization": f"Bearer {settings.meta_access_token}"}
    upload_url = f"https://graph.facebook.com/v19.0/{settings.meta_phone_number_id}/media"
    fname = f"file.{ext}" if ext else "file"
    try:
        async with _httpx.AsyncClient(timeout=30) as client:
            up = await client.post(
                upload_url,
                data={"messaging_product": "whatsapp", "type": mime_type},
                files={"file": (fname, file_bytes, mime_type)},
                headers=meta_auth,
            )
        if not up.is_success:
            return {"success": False, "erro": f"upload meta falhou: {up.text[:200]}"}
        media_id = up.json().get("id")
        if not media_id:
            return {"success": False, "erro": "media_id não retornado pelo Meta"}
    except Exception as exc:
        return {"success": False, "erro": f"upload error: {exc}"}

    wa_type = {"audio": "audio", "image": "image", "video": "video", "document": "document"}.get(file_type, "document")
    numero = phone.lstrip("+")
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": wa_type,
        wa_type: {"id": media_id},
    }
    try:
        async with _httpx.AsyncClient(timeout=15) as client:
            send = await client.post(
                f"https://graph.facebook.com/v19.0/{settings.meta_phone_number_id}/messages",
                json=payload,
                headers={**meta_auth, "Content-Type": "application/json"},
            )
        if send.is_success:
            return {"success": True}
        return {"success": False, "erro": send.text[:200]}
    except Exception as exc:
        return {"success": False, "erro": f"send error: {exc}"}


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
