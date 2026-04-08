from abc import ABC, abstractmethod


class WhatsAppProvider(ABC):
    @abstractmethod
    async def send_message(self, telefone: str, mensagem: str) -> dict:
        """
        Envia mensagem WhatsApp para o número.
        Retorna: {'success': bool, 'provider_ref': str | None, 'erro': str | None}
        """
        ...

    @abstractmethod
    async def check_status(self, provider_ref: str) -> str:
        """
        Consulta status de entrega de uma mensagem enviada.
        Retorna string de status: 'sent', 'delivered', 'read', 'failed'
        """
        ...
