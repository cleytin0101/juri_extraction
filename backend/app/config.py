import json
import logging
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

logger = logging.getLogger(__name__)

CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials.json"


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    cnpj_api_url: str = "https://publica.cnpj.ws/cnpj"
    cnpja_api_url: str = "https://api.cnpja.com"
    cnpja_api_key: str = ""
    whatsapp_provider: str = "mock"
    meta_phone_number_id: str = ""
    meta_access_token: str = ""
    meta_webhook_verify_token: str = "juri_webhook_token"
    cors_origins: List[str] = ["http://localhost:5173", "https://juri-frontend.onrender.com"]
    # Dados do advogado para template WhatsApp
    advogado_nome: str = ""
    advogado_contato: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()


def load_runtime_credentials() -> None:
    if not CREDENTIALS_FILE.exists():
        return
    try:
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        for field in ("advogado_nome", "advogado_contato"):
            value = data.get(field, "")
            if value:
                object.__setattr__(settings, field, value)
        logger.info("Credenciais carregadas de credentials.json")
    except Exception as e:
        logger.warning(f"Erro ao ler credentials.json: {e}")


def save_runtime_credentials(advogado_nome: str = "", advogado_contato: str = "") -> None:
    existing: dict = {}
    if CREDENTIALS_FILE.exists():
        try:
            existing = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    updated = {**existing}
    if advogado_nome is not None:
        updated["advogado_nome"] = advogado_nome
    if advogado_contato is not None:
        updated["advogado_contato"] = advogado_contato

    CREDENTIALS_FILE.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    load_runtime_credentials()
    logger.info("Credenciais salvas e recarregadas")
