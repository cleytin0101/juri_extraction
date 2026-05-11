import logging
from datetime import datetime, timezone
from typing import Optional

from ..database import get_supabase
from ..scraper.parser import parse_pdf_text, parse_numero_processo
from ..scraper.enricher import enrich_empresa
from ..services.storage_service import upload_pdf, pdf_expires_at

logger = logging.getLogger(__name__)


async def process_document(pdf_bytes: bytes, filename: str) -> dict:
    """
    Processa um PDF de processo judicial:
    1. Extrai texto e campos com pdfplumber
    2. Enriquece empresa via CNPJ.ws se CNPJ encontrado
    3. Persiste processo, empresa e lead no banco
    4. Faz upload do PDF para Storage

    Retorna dict com os dados extraídos e status do lead.
    """
    result = {
        "filename": filename,
        "numero_processo": None,
        "empresa_nome": None,
        "empresa_cnpj": None,
        "reclamante_nome": None,
        "telefone": None,
        "telefone_fonte": None,
        "valor_causa": None,
        "resumo_caso": None,
        "tem_advogado": False,
        "lead_id": None,
        "status": "erro",
        "erro_msg": None,
    }

    try:
        parsed = parse_pdf_text(pdf_bytes)
    except Exception as e:
        result["erro_msg"] = f"Falha ao ler PDF: {e}"
        return result

    result.update({
        "empresa_nome": parsed.get("empresa_nome") or None,
        "empresa_cnpj": parsed.get("empresa_cnpj") or None,
        "reclamante_nome": parsed.get("reclamante_nome") or None,
        "valor_causa": parsed.get("valor_causa"),
        "resumo_caso": parsed.get("resumo_caso") or None,
        "tem_advogado": parsed.get("tem_advogado", False),
    })

    # Extrair número do processo do nome do arquivo como fallback
    numero = parse_numero_processo(filename)
    if not numero:
        # Tenta extrair do texto do PDF
        import re
        from ..scraper.parser import PROCESSO_REGEX
        text_sample = _extract_text_sample(pdf_bytes)
        m = PROCESSO_REGEX.search(text_sample)
        numero = m.group() if m else filename.replace(".pdf", "")
    result["numero_processo"] = numero

    if result["tem_advogado"]:
        result["status"] = "tem_advogado"
        _upsert_processo_only(result, pdf_bytes)
        return result

    # Enriquecimento via CNPJ.ws
    enrichment = {}
    if result["empresa_cnpj"]:
        try:
            enrichment = await enrich_empresa(result["empresa_cnpj"]) or {}
        except Exception as e:
            logger.warning(f"Enriquecimento CNPJ falhou para {result['empresa_cnpj']}: {e}")

    if enrichment.get("nome") and not result["empresa_nome"]:
        result["empresa_nome"] = enrichment["nome"]

    telefones: list = enrichment.get("telefones") or []
    if telefones:
        result["telefone"] = telefones[0]
        result["telefone_fonte"] = "cnpj_ws"
    else:
        result["telefone"] = None

    sb = get_supabase()

    # Upload PDF
    pdf_path = await upload_pdf(sb, numero, pdf_bytes)

    # Upsert processo
    processo_data = {
        "numero_processo": numero,
        "orgao_julgador": parsed.get("orgao_julgador") or "",
        "valor_causa": result["valor_causa"],
        "resumo_caso": result["resumo_caso"],
        "reclamante_nome": result["reclamante_nome"],
        "tem_advogado": result["tem_advogado"],
        "pdf_url": pdf_path,
        "pdf_expires_at": pdf_expires_at() if pdf_path else None,
        "raw_data": {"origem": "upload_manual", "filename": filename},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        proc_result = (
            sb.table("processos")
            .upsert(processo_data, on_conflict="numero_processo")
            .execute()
        )
        processo_id = proc_result.data[0]["id"] if proc_result.data else None
    except Exception as e:
        result["erro_msg"] = f"Erro ao salvar processo: {e}"
        return result

    if not processo_id:
        result["erro_msg"] = "Processo não retornou ID após upsert"
        return result

    # Checar se já existe lead para este processo
    existing = (
        sb.table("leads").select("id").eq("processo_id", processo_id).execute()
    )
    if existing.data:
        result["lead_id"] = existing.data[0]["id"]
        result["status"] = "ja_existe"
        return result

    # Upsert empresa
    empresa_id = None
    if result["empresa_cnpj"] or result["empresa_nome"]:
        empresa_data = {
            "processo_id": processo_id,
            "nome": result["empresa_nome"] or "Empresa não identificada",
            "cnpj": result["empresa_cnpj"] or "",
            "telefones": telefones,
            "email": enrichment.get("email"),
            "endereco": enrichment.get("endereco"),
            "cnpj_data": enrichment.get("cnpj_data"),
            "enriched_at": datetime.now(timezone.utc).isoformat() if enrichment else None,
        }
        try:
            if result["empresa_cnpj"]:
                emp_result = (
                    sb.table("empresas")
                    .upsert(empresa_data, on_conflict="cnpj")
                    .execute()
                )
            else:
                emp_result = sb.table("empresas").insert(empresa_data).execute()
            empresa_id = emp_result.data[0]["id"] if emp_result.data else None
        except Exception as e:
            logger.warning(f"Erro ao salvar empresa: {e}")

    # Criar lead
    try:
        lead_result = sb.table("leads").insert({
            "processo_id": processo_id,
            "empresa_id": empresa_id,
            "status": "novo",
            "lead_criado_em": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        result["lead_id"] = lead_result.data[0]["id"] if lead_result.data else None
        result["status"] = "criado"
    except Exception as e:
        result["erro_msg"] = f"Erro ao criar lead: {e}"
        return result

    return result


def _extract_text_sample(pdf_bytes: bytes, max_chars: int = 2000) -> str:
    try:
        import io
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = pdf.pages[:2]
            return "\n".join(p.extract_text() or "" for p in pages)[:max_chars]
    except Exception:
        return ""


def _upsert_processo_only(result: dict, pdf_bytes: bytes) -> None:
    """Salva apenas o processo quando tem_advogado=True, sem criar lead."""
    try:
        import asyncio
        sb = get_supabase()
        pdf_path = None
        if pdf_bytes:
            loop = asyncio.get_event_loop()
            pdf_path = loop.run_until_complete(
                upload_pdf(sb, result["numero_processo"], pdf_bytes)
            )
        sb.table("processos").upsert({
            "numero_processo": result["numero_processo"],
            "valor_causa": result["valor_causa"],
            "resumo_caso": result["resumo_caso"],
            "reclamante_nome": result["reclamante_nome"],
            "tem_advogado": True,
            "pdf_url": pdf_path,
            "pdf_expires_at": pdf_expires_at() if pdf_path else None,
            "raw_data": {"origem": "upload_manual"},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="numero_processo").execute()
    except Exception as e:
        logger.warning(f"Erro ao salvar processo com advogado: {e}")
