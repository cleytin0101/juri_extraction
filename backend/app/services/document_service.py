import asyncio
import logging
import re
from datetime import datetime, timezone

from ..database import get_supabase
from ..scraper.parser import parse_pdf_text, parse_numero_processo, PROCESSO_REGEX
from ..scraper.enricher import enrich_empresa
from ..services.storage_service import upload_pdf, pdf_expires_at

logger = logging.getLogger(__name__)


async def process_document(pdf_bytes: bytes, filename: str, responsavel: str | None = None) -> dict:
    """
    Processa um PDF de processo judicial:
    1. Extrai campos com pdfplumber
    2. Sempre enriquece via CNPJ.ws (independente de ter advogado)
    3. Persiste processo, empresa e lead para TODOS os documentos
       - tem_advogado=True  → lead com status="descartado"
       - tem_advogado=False → lead com status="novo"
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

    # Fase 1: primeiras 6 páginas
    try:
        parsed = await asyncio.to_thread(parse_pdf_text, pdf_bytes, 6)
    except Exception as e:
        result["erro_msg"] = f"Falha ao ler PDF: {e}"
        return result

    # Se os campos-chave não foram encontrados, lê até 12 páginas (Fase 2)
    # 12 páginas cobre partes + decisão em qualquer ATOrd do PJe sem ler
    # os certificados ICP-Brasil e assinaturas embutidas nas páginas finais.
    if not (bool(parsed.get("empresa_nome")) and parsed.get("data_audiencia") is not None):
        try:
            parsed_full = await asyncio.to_thread(parse_pdf_text, pdf_bytes, 12)
            parsed = parsed_full
        except Exception:
            pass  # usa o resultado parcial da Fase 1

    result.update({
        "empresa_nome": parsed.get("empresa_nome") or None,
        "empresa_cnpj": parsed.get("empresa_cnpj") or None,
        "reclamante_nome": parsed.get("reclamante_nome") or None,
        "valor_causa": parsed.get("valor_causa"),
        "resumo_caso": parsed.get("resumo_caso") or None,
        "tem_advogado": parsed.get("tem_advogado", False),
    })

    # Número do processo: tenta pelo nome do arquivo, depois pelo texto
    numero = parse_numero_processo(filename)
    if not numero:
        text_sample = await asyncio.to_thread(_extract_text_sample, pdf_bytes)
        m = PROCESSO_REGEX.search(text_sample)
        numero = m.group() if m else filename.replace(".pdf", "")
    result["numero_processo"] = numero

    # Enriquecimento — sempre, independente de ter advogado
    # Cascata: CNPJ.ws por CNPJ → cnpja.com por CNPJ → cnpja.com por nome
    enrichment: dict = {}
    try:
        enrichment = await enrich_empresa(
            result["empresa_cnpj"] or "",
            nome=result["empresa_nome"] or "",
        ) or {}
    except Exception as e:
        logger.warning(f"Enriquecimento falhou para {result['empresa_cnpj']}: {e}")

    if enrichment.get("nome"):
        result["empresa_nome"] = enrichment["nome"]

    telefones: list = enrichment.get("telefones") or []
    if telefones:
        result["telefone"] = telefones[0]
        result["telefone_fonte"] = "cnpj_ws"

    sb = get_supabase()

    # Upload PDF
    pdf_path = await upload_pdf(sb, numero, pdf_bytes)

    # Upsert processo
    processo_data = {
        "numero_processo": numero,
        "orgao_julgador": parsed.get("orgao_julgador") or "",
        "valor_causa": result["valor_causa"],
        "data_audiencia": parsed["data_audiencia"].isoformat() if parsed.get("data_audiencia") else None,
        "resumo_caso": result["resumo_caso"],
        "reclamante_nome": result["reclamante_nome"],
        "tem_advogado": result["tem_advogado"],
        "pdf_url": pdf_path,
        "pdf_expires_at": pdf_expires_at() if pdf_path else None,
        "raw_data": {
            "origem": "upload_manual",
            "filename": filename,
            "modalidade_audiencia": parsed.get("modalidade_audiencia"),
        },
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
    existing = sb.table("leads").select("id").eq("processo_id", processo_id).execute()
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

    # Criar lead para TODOS os documentos
    # tem_advogado=True → "descartado" (info salva, mas não enviar WhatsApp)
    # tem_advogado=False → "novo" (pronto para contato)
    lead_status = "descartado" if result["tem_advogado"] else "novo"
    try:
        lead_result = sb.table("leads").insert({
            "processo_id": processo_id,
            "empresa_id": empresa_id,
            "status": lead_status,
            "responsavel": responsavel,
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
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join(p.extract_text() or "" for p in reader.pages[:2])[:max_chars]
    except Exception:
        return ""
