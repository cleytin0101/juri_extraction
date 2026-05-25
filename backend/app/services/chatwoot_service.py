import logging
import httpx

from ..config import settings

_META_MIME = {
    "audio": "audio/ogg",
    "image": "image/jpeg",
    "video": "video/mp4",
    "document": "application/octet-stream",
    "sticker": "image/webp",
}
_META_EXT = {"audio": "ogg", "image": "jpg", "video": "mp4", "document": "bin", "sticker": "webp"}

logger = logging.getLogger(__name__)


def _enabled() -> bool:
    return bool(settings.chatwoot_url and settings.chatwoot_api_token and settings.chatwoot_account_id and settings.chatwoot_inbox_id)


def _headers() -> dict:
    return {"api_access_token": settings.chatwoot_api_token, "Content-Type": "application/json"}


def _base() -> str:
    return f"{settings.chatwoot_url.rstrip('/')}/api/v1/accounts/{settings.chatwoot_account_id}"


async def _get_or_create_contact(client: httpx.AsyncClient, telefone: str, nome: str) -> int | None:
    phone = telefone if telefone.startswith("+") else f"+{telefone}"
    search = await client.get(f"{_base()}/contacts/search", params={"q": phone, "include_contacts": "true"})
    if search.is_success:
        payload = search.json()
        raw = payload.get("payload", [])
        contacts = raw.get("contacts", []) if isinstance(raw, dict) else raw
        if contacts:
            return contacts[0]["id"]

    create = await client.post(f"{_base()}/contacts", json={"phone_number": phone, "name": nome or phone})
    if create.is_success:
        data = create.json()
        contact_id = (
            data.get("id")
            or data.get("payload", {}).get("id")
            or (data.get("payload", {}).get("contact") or {}).get("id")
        )
        if not contact_id:
            logger.warning(f"[Chatwoot] Contato criado mas ID nao encontrado. Resposta: {str(data)[:300]}")
        return contact_id
    logger.warning(f"[Chatwoot] Falha ao criar contato {phone}: {create.status_code} {create.text[:200]}")
    return None


async def _get_or_create_conversation(client: httpx.AsyncClient, contact_id: int) -> int | None:
    convs = await client.get(f"{_base()}/contacts/{contact_id}/conversations")
    if convs.is_success:
        items = convs.json().get("payload", [])
        matching = [c for c in items if c.get("inbox_id") == int(settings.chatwoot_inbox_id)]
        if matching:
            return matching[0]["id"]

    create = await client.post(f"{_base()}/conversations", json={
        "contact_id": contact_id,
        "inbox_id": int(settings.chatwoot_inbox_id),
    })
    if create.is_success:
        data = create.json()
        return data.get("id") or data.get("payload", {}).get("id")
    logger.warning(f"[Chatwoot] Falha ao criar conversa para contato {contact_id}: {create.text}")
    return None


async def _download_meta_media(media_id: str) -> tuple[bytes, str] | None:
    meta_headers = {"Authorization": f"Bearer {settings.meta_access_token}"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.get(f"https://graph.facebook.com/v19.0/{media_id}", headers=meta_headers)
        if not r.is_success:
            logger.warning(f"[Chatwoot] Falha ao obter URL da mídia {media_id}: {r.text[:200]}")
            return None
        meta_json = r.json()
        url = meta_json.get("url")
        meta_mime = meta_json.get("mime_type", "")
        if not url:
            logger.warning(f"[Chatwoot] URL de mídia ausente na resposta para {media_id}")
            return None
        r2 = await client.get(url, headers=meta_headers)
        cdn_ct = r2.headers.get("content-type", "")
        logger.info(f"[Chatwoot] CDN status={r2.status_code} bytes={len(r2.content)} mime_meta={meta_mime!r} cdn_ct={cdn_ct!r} media_id={media_id}")
        if not r2.is_success:
            logger.warning(f"[Chatwoot] Falha ao baixar mídia do CDN: status {r2.status_code}")
            return None
        return r2.content, meta_mime


async def registrar_midia_recebida(telefone: str, media_id: str, tipo: str, caption: str = "", filename: str = "") -> None:
    if not _enabled():
        return
    fallback = f"[{tipo} recebido]" + (f": {caption}" if caption else "")
    try:
        result = await _download_meta_media(media_id)
        if not result:
            await registrar_mensagem_recebida(telefone, fallback)
            return
        file_bytes, meta_mime = result
        if not file_bytes:
            logger.warning(f"[Chatwoot] Arquivo vazio do CDN — media_id={media_id}")
            await registrar_mensagem_recebida(telefone, fallback)
            return
        raw_mime = meta_mime or _META_MIME.get(tipo, "application/octet-stream")
        mime = raw_mime.split(";")[0].strip()
        ext = _META_EXT.get(tipo, "bin")
        fname = filename or f"{tipo}.{ext}"
        logger.info(f"[Chatwoot] Upload Chatwoot: tipo={tipo} mime={mime!r} bytes={len(file_bytes)} fname={fname!r}")
        async with httpx.AsyncClient(headers={"api_access_token": settings.chatwoot_api_token}, timeout=30) as client:
            contact_id = await _get_or_create_contact(client, telefone, telefone)
            if not contact_id:
                return
            conv_id = await _get_or_create_conversation(client, contact_id)
            if not conv_id:
                return
            files = {"attachments[]": (fname, file_bytes, mime)}
            data = {"message_type": "incoming", "private": "false", "content": caption or ""}
            resp = await client.post(f"{_base()}/conversations/{conv_id}/messages", data=data, files=files)
            if resp.is_success:
                logger.info(f"[Chatwoot] Mídia {tipo} registrada — conversa {conv_id}")
            else:
                logger.warning(f"[Chatwoot] Falha ao registrar mídia — {resp.status_code}: {resp.text[:300]}")
                await registrar_mensagem_recebida(telefone, fallback)
    except Exception as exc:
        logger.error(f"[Chatwoot] Erro ao registrar mídia de {telefone}: {exc}")
        await registrar_mensagem_recebida(telefone, fallback)


async def registrar_mensagem_recebida(telefone: str, texto: str) -> None:
    if not _enabled():
        return
    try:
        async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
            contact_id = await _get_or_create_contact(client, telefone, telefone)
            if not contact_id:
                logger.warning(f"[Chatwoot] Não foi possível obter/criar contato para {telefone}")
                return
            conv_id = await _get_or_create_conversation(client, contact_id)
            if not conv_id:
                logger.warning(f"[Chatwoot] Não foi possível obter/criar conversa para contato {contact_id}")
                return
            resp = await client.post(f"{_base()}/conversations/{conv_id}/messages", json={
                "content": texto,
                "message_type": "incoming",
                "private": False,
            })
            if resp.is_success:
                logger.info(f"[Chatwoot] Mensagem recebida registrada — conversa {conv_id}")
            else:
                logger.warning(f"[Chatwoot] Falha ao registrar mensagem recebida — status {resp.status_code}: {resp.text[:300]}")
    except Exception as exc:
        logger.error(f"[Chatwoot] Erro ao registrar mensagem recebida de {telefone}: {exc}")


async def registrar_mensagem_enviada(telefone: str, nome: str, texto: str) -> None:
    if not _enabled():
        logger.warning("[Chatwoot] Integração desabilitada — configure CHATWOOT_URL, CHATWOOT_API_TOKEN, CHATWOOT_ACCOUNT_ID e CHATWOOT_INBOX_ID")
        return
    try:
        async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
            contact_id = await _get_or_create_contact(client, telefone, nome)
            if not contact_id:
                logger.warning(f"[Chatwoot] Não foi possível obter/criar contato para {telefone}")
                return
            conv_id = await _get_or_create_conversation(client, contact_id)
            if not conv_id:
                logger.warning(f"[Chatwoot] Não foi possível obter/criar conversa para contato {contact_id}")
                return
            await client.post(f"{_base()}/conversations/{conv_id}/messages", json={
                "content": texto,
                "message_type": "outgoing",
                "private": True,
            })
            logger.info(f"[Chatwoot] Mensagem registrada — conversa {conv_id} contato {contact_id}")
    except Exception as exc:
        logger.error(f"[Chatwoot] Erro ao registrar mensagem para {telefone}: {exc}")
