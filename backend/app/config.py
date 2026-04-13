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
    pje_base_url: str = "https://pje.trt7.jus.br/consultaprocessual"
    cnpj_api_url: str = "https://publica.cnpj.ws/cnpj"
    whatsapp_provider: str = "mock"
    cors_origins: List[str] = ["http://localhost:5173", "https://juri-frontend.onrender.com"]
    scrape_schedule_cron: str = "0 7 * * 1-5"
    # Credenciais do advogado para PJe (opcional — pautas públicas não precisam)
    pje_cpf: str = ""
    pje_senha: str = ""
    pje_totp_secret: str = ""
    # Dados do advogado para template WhatsApp
    advogado_nome: str = ""
    advogado_contato: str = ""
    # Token da API Infosimples (substitui CAPTCHA na ETAPA 2)
    infosimples_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()


def load_runtime_credentials() -> None:
    """
    Lê credentials.json (se existir) e sobrescreve os campos correspondentes
    em settings. Chamado uma vez no startup e após salvar novas credenciais.
    Campos do arquivo têm prioridade sobre .env apenas se estiverem preenchidos.
    """
    if not CREDENTIALS_FILE.exists():
        return
    try:
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        for field in ("pje_cpf", "pje_senha", "pje_totp_secret", "advogado_nome", "advogado_contato", "infosimples_token"):
            value = data.get(field, "")
            if value:
                object.__setattr__(settings, field, value)
        logger.info("Credenciais carregadas de credentials.json")
    except Exception as e:
        logger.warning(f"Erro ao ler credentials.json: {e}")


def save_runtime_credentials(pje_cpf: str = "", pje_senha: str = "",
                              pje_totp_secret: str = "",
                              advogado_nome: str = "", advogado_contato: str = "",
                              infosimples_token: str = "") -> None:
    """
    Persiste as credenciais em credentials.json e atualiza settings em memória.
    Campos vazios sobrescrevem os anteriores (para permitir limpar valores).
    """
    # Ler dados existentes para não perder campos não enviados
    existing: dict = {}
    if CREDENTIALS_FILE.exists():
        try:
            existing = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Atualizar apenas os campos enviados (string não-None)
    updated = {**existing}
    if pje_cpf is not None:
        updated["pje_cpf"] = pje_cpf
    if pje_senha is not None:
        updated["pje_senha"] = pje_senha
    if pje_totp_secret is not None:
        updated["pje_totp_secret"] = pje_totp_secret
    if advogado_nome is not None:
        updated["advogado_nome"] = advogado_nome
    if advogado_contato is not None:
        updated["advogado_contato"] = advogado_contato
    if infosimples_token is not None:
        updated["infosimples_token"] = infosimples_token

    CREDENTIALS_FILE.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")

    # Atualizar settings em memória
    load_runtime_credentials()
    logger.info("Credenciais salvas e recarregadas")
