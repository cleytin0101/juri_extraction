"""
Serviço de armazenamento de PDFs de processos no Supabase Storage.

Bucket: processos-pdf (privado)
Cada PDF fica disponível por 24h e é deletado automaticamente pelo cleanup job.

Pré-requisito: criar o bucket 'processos-pdf' no painel do Supabase:
  Storage → New Bucket → nome: processos-pdf → desmarcar "Public bucket" → Create
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

BUCKET = "processos-pdf"
PDF_TTL_HOURS = 24
SIGNED_URL_EXPIRES_IN = 3600  # URL assinada válida por 1h


async def upload_pdf(sb, numero_processo: str, pdf_bytes: bytes) -> Optional[str]:
    """
    Faz upload do PDF para o Supabase Storage.
    Retorna o path do arquivo no bucket (ex: '0000173-15.2026.5.07.0027.pdf').
    Retorna None em caso de erro.
    """
    if not pdf_bytes:
        return None

    # Limpar número do processo para usar como nome de arquivo
    safe_name = numero_processo.replace("/", "_").replace(" ", "_") + ".pdf"
    path = safe_name

    try:
        sb.storage.from_(BUCKET).upload(
            path=path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )
        logger.info(f"PDF enviado ao Supabase Storage: {path}")
        return path
    except Exception as e:
        logger.error(f"Erro ao fazer upload do PDF {safe_name}: {e}")
        return None


def get_signed_url(sb, pdf_path: str, expires_in: int = SIGNED_URL_EXPIRES_IN) -> Optional[str]:
    """
    Gera uma URL assinada temporária para o PDF (válida por `expires_in` segundos).
    Retorna None se o arquivo não existir ou em caso de erro.
    """
    if not pdf_path:
        return None
    try:
        result = sb.storage.from_(BUCKET).create_signed_url(pdf_path, expires_in)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception as e:
        logger.warning(f"Erro ao gerar URL assinada para {pdf_path}: {e}")
        return None


async def delete_pdf(sb, pdf_path: str) -> bool:
    """Remove um PDF do Supabase Storage. Retorna True se deletado com sucesso."""
    if not pdf_path:
        return False
    try:
        sb.storage.from_(BUCKET).remove([pdf_path])
        logger.info(f"PDF deletado do Storage: {pdf_path}")
        return True
    except Exception as e:
        logger.warning(f"Erro ao deletar PDF {pdf_path}: {e}")
        return False


async def cleanup_expired_pdfs(sb) -> int:
    """
    Deleta do Supabase Storage todos os PDFs cujo pdf_expires_at já passou.
    Limpa o campo pdf_url nos registros correspondentes.
    Retorna o número de PDFs removidos.
    """
    now = datetime.now(timezone.utc).isoformat()
    try:
        result = (
            sb.table("processos")
            .select("id, pdf_url")
            .not_.is_("pdf_url", "null")
            .lt("pdf_expires_at", now)
            .execute()
        )
        expirados = result.data or []
    except Exception as e:
        logger.error(f"Erro ao buscar PDFs expirados: {e}")
        return 0

    deletados = 0
    for proc in expirados:
        pdf_path = proc.get("pdf_url")
        if not pdf_path:
            continue

        await delete_pdf(sb, pdf_path)

        # Limpar campos no banco
        try:
            sb.table("processos").update(
                {"pdf_url": None, "pdf_expires_at": None}
            ).eq("id", proc["id"]).execute()
            deletados += 1
        except Exception as e:
            logger.warning(f"Erro ao limpar pdf_url do processo {proc['id']}: {e}")

    if deletados:
        logger.info(f"Cleanup: {deletados} PDFs expirados removidos do Storage.")
    return deletados


def pdf_expires_at() -> str:
    """Retorna o timestamp de expiração do PDF (now + 24h) em formato ISO."""
    return (datetime.now(timezone.utc) + timedelta(hours=PDF_TTL_HOURS)).isoformat()
