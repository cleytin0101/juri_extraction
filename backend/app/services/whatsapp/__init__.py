from ...config import settings
from .interface import WhatsAppProvider
from .mock_provider import MockProvider


def get_whatsapp_provider() -> WhatsAppProvider:
    provider = settings.whatsapp_provider
    if provider == "mock":
        return MockProvider()
    # Adicionar outros providers aqui:
    # elif provider == "evolution":
    #     from .evolution_provider import EvolutionProvider
    #     return EvolutionProvider()
    raise ValueError(f"WhatsApp provider desconhecido: '{provider}'")
