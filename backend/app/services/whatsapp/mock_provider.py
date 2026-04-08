import logging
import uuid
from .interface import WhatsAppProvider

logger = logging.getLogger(__name__)


class MockProvider(WhatsAppProvider):
    """
    Provider simulado para desenvolvimento e testes.
    Loga a mensagem no console e retorna sucesso imediatamente.
    Substitua por EvolutionProvider, ZAPIProvider, etc. em produção.
    """

    async def send_message(self, telefone: str, mensagem: str) -> dict:
        ref = str(uuid.uuid4())
        logger.info(
            f"[MOCK WhatsApp] → {telefone}\n"
            f"{'─' * 40}\n{mensagem}\n{'─' * 40}\nref: {ref}"
        )
        return {"success": True, "provider_ref": ref, "erro": None}

    async def check_status(self, provider_ref: str) -> str:
        return "sent"
