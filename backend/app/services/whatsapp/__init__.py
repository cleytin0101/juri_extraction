from ...config import settings
from .interface import WhatsAppProvider
from .mock_provider import MockProvider


def get_whatsapp_provider() -> WhatsAppProvider:
    provider = settings.whatsapp_provider
    if provider == "mock":
        return MockProvider()
    if provider == "meta_cloud":
        from .meta_cloud_provider import MetaCloudProvider
        return MetaCloudProvider()
    raise ValueError(f"WhatsApp provider desconhecido: '{provider}'")
