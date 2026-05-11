import logging
from supabase import create_client, Client
from .config import settings

logger = logging.getLogger(__name__)


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_KEY precisam estar configuradas. "
            "Verifique as Environment Variables no Render (aba Environment do serviço)."
        )
    return create_client(settings.supabase_url, settings.supabase_key)
