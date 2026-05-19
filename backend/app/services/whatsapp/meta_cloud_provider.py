import logging
import httpx
from .interface import WhatsAppProvider
from .template import _fmt_data, _fmt_valor
from ...config import settings

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com/v19.0"
TEMPLATE_NAME = "audiencia_trabalhista"


class MetaCloudProvider(WhatsAppProvider):
    """
    Provider oficial Meta Cloud API (WhatsApp Business Platform).
    Requer META_PHONE_NUMBER_ID e META_ACCESS_TOKEN no .env.
    """

    async def send_message(self, telefone: str, mensagem: str, lead: dict = None) -> dict:
        url = f"{GRAPH_API_URL}/{settings.meta_phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        numero = telefone.lstrip("+")

        if lead:
            payload = {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "template",
                "template": {
                    "name": TEMPLATE_NAME,
                    "language": {"code": "pt_BR"},
                    "components": [{"type": "body", "parameters": [
                        {"type": "text", "text": lead.get("empresa_nome") or "sua empresa"},
                        {"type": "text", "text": _fmt_data(lead.get("data_audiencia"))},
                    ]}],
                },
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "text",
                "text": {"body": mensagem},
            }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                provider_ref = (
                    data.get("messages", [{}])[0].get("id")
                    if data.get("messages")
                    else None
                )
                logger.info(f"[MetaCloud] Mensagem enviada → {telefone} | ref={provider_ref}")
                return {"success": True, "provider_ref": provider_ref, "erro": None}
        except httpx.HTTPStatusError as exc:
            erro = exc.response.text
            logger.error(f"[MetaCloud] Erro HTTP ao enviar para {telefone}: {erro}")
            return {"success": False, "provider_ref": None, "erro": erro}
        except Exception as exc:
            erro = str(exc)
            logger.error(f"[MetaCloud] Erro ao enviar para {telefone}: {erro}")
            return {"success": False, "provider_ref": None, "erro": erro}

    async def check_status(self, provider_ref: str) -> str:
        # O Meta não expõe endpoint de consulta de status individual.
        # Status chegam via webhook. Retornamos 'sent' como padrão.
        return "sent"
