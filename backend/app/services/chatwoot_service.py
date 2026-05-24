import logging
import httpx

from ..config import settings

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
        contacts = payload.get("payload", {}).get("contacts", [])
        if contacts:
            return contacts[0]["id"]

    create = await client.post(f"{_base()}/contacts", json={"phone_number": phone, "name": nome or phone})
    if create.is_success:
        data = create.json()
        return data.get("id") or data.get("payload", {}).get("id")
    logger.warning(f"[Chatwoot] Falha ao criar contato {phone}: {create.text}")
    return None


async def _get_or_create_conversation(client: httpx.AsyncClient, contact_id: int) -> int | None:
    convs = await client.get(f"{_base()}/contacts/{contact_id}/conversations")
    if convs.is_success:
        items = convs.json().get("payload", [])
        if items:
            return items[0]["id"]

    create = await client.post(f"{_base()}/conversations", json={
        "contact_id": contact_id,
        "inbox_id": int(settings.chatwoot_inbox_id),
    })
    if create.is_success:
        data = create.json()
        return data.get("id") or data.get("payload", {}).get("id")
    logger.warning(f"[Chatwoot] Falha ao criar conversa para contato {contact_id}: {create.text}")
    return None


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
            await client.post(f"{_base()}/conversations/{conv_id}/messages", json={
                "content": texto,
                "message_type": "incoming",
                "private": False,
            })
            logger.info(f"[Chatwoot] Mensagem recebida registrada — conversa {conv_id}")
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
                "private": False,
            })
            logger.info(f"[Chatwoot] Mensagem registrada — conversa {conv_id} contato {contact_id}")
    except Exception as exc:
        logger.error(f"[Chatwoot] Erro ao registrar mensagem para {telefone}: {exc}")
