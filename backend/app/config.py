from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


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
    # Dados do advogado para template WhatsApp
    advogado_nome: str = ""
    advogado_contato: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
