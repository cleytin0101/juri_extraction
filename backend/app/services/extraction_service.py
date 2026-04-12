import asyncio
import logging
from datetime import date, datetime, timezone
from typing import List

from ..config import settings
from ..database import get_supabase
from ..scraper.pje_scraper import scrape_pauta
from ..scraper.enricher import enrich_empresa
from .storage_service import upload_pdf, pdf_expires_at

logger = logging.getLogger(__name__)


async def run_extraction(vara_id: str, data_audiencia: date) -> dict:
    """
    Orquestra o pipeline completo:
    scraper → parser → enricher (CNPJ.ws) → inserções no Supabase
    """
    sb = get_supabase()
    errors: List[str] = []
    processos_encontrados = 0
    leads_criados = 0

    # Buscar dados da vara
    vara_result = sb.table("varas").select("*").eq("id", vara_id).single().execute()
    if not vara_result.data:
        return {"processos_encontrados": 0, "leads_criados": 0, "errors": [f"Vara {vara_id} não encontrada"]}

    vara = vara_result.data
    vara_nome = vara["nome"]

    # Criar ou recuperar registro de pauta
    pauta_id = _upsert_pauta(sb, vara_id, data_audiencia)

    # Scraping
    logger.info(f"Iniciando scraping: vara={vara_nome}, data={data_audiencia}")
    try:
        processos_raw = await scrape_pauta(vara_nome, data_audiencia, cpf=settings.pje_cpf, senha=settings.pje_senha)
    except Exception as e:
        errors.append(f"Erro no scraping: {e}")
        logger.error(f"Scraping falhou: {e}")
        return {"processos_encontrados": 0, "leads_criados": 0, "errors": errors}

    processos_encontrados = len(processos_raw)
    logger.info(f"{processos_encontrados} processos encontrados")

    leads_criados = 0
    processos_com_advogado = 0

    # Processar cada processo
    for proc_data in processos_raw:
        try:
            result = await _process_single(sb, pauta_id, proc_data)
            if result == "lead_criado":
                leads_criados += 1
            elif result == "tem_advogado":
                processos_com_advogado += 1
        except Exception as e:
            num = proc_data.get("numero_processo", "?")
            errors.append(f"Erro no processo {num}: {e}")
            logger.error(f"Erro ao processar {num}: {e}")

        await asyncio.sleep(0.5)

    logger.info(
        f"Extração concluída: {leads_criados} leads, "
        f"{processos_com_advogado} com advogado, {len(errors)} erros"
    )
    return {
        "processos_encontrados": processos_encontrados,
        "leads_criados": leads_criados,
        "processos_com_advogado": processos_com_advogado,
        "errors": errors,
    }


def _upsert_pauta(sb, vara_id: str, data_audiencia: date) -> str:
    result = (
        sb.table("pautas")
        .upsert(
            {"vara_id": vara_id, "data_pauta": data_audiencia.isoformat()},
            on_conflict="vara_id,data_pauta",
        )
        .execute()
    )
    return result.data[0]["id"]


async def _process_single(sb, pauta_id: str, proc_data: dict) -> str:
    """
    Processa um processo individual.
    Retorna: 'lead_criado', 'tem_advogado', 'duplicado' ou 'ignorado'.
    """
    numero = proc_data.get("numero_processo", "")
    if not numero:
        return "ignorado"

    data_aud = proc_data.get("data_audiencia")
    if data_aud is None:
        return "ignorado"

    tem_advogado = bool(proc_data.get("tem_advogado", False))

    # Upload do PDF ao Supabase Storage (se disponível)
    pdf_bytes = proc_data.get("pdf_bytes")
    pdf_path = None
    pdf_exp = None
    if pdf_bytes:
        pdf_path = await upload_pdf(sb, numero, pdf_bytes)
        if pdf_path:
            pdf_exp = pdf_expires_at()

    # Upsert processo
    processo_row = {
        "pauta_id": pauta_id,
        "numero_processo": numero,
        "orgao_julgador": proc_data.get("orgao_julgador"),
        "valor_causa": proc_data.get("valor_causa"),
        "data_audiencia": data_aud.isoformat() if hasattr(data_aud, "isoformat") else str(data_aud),
        "tipo_audiencia": proc_data.get("tipo_audiencia", "outra"),
        "resumo_caso": proc_data.get("resumo_caso"),
        "reclamante_nome": proc_data.get("reclamante_nome"),
        "tem_advogado": tem_advogado,
        "pdf_url": pdf_path,
        "pdf_expires_at": pdf_exp,
        "raw_data": proc_data.get("raw_data"),
    }

    proc_result = (
        sb.table("processos")
        .upsert(processo_row, on_conflict="numero_processo")
        .execute()
    )
    processo_id = proc_result.data[0]["id"]

    # Se já tem advogado, não cria lead (mas processo fica salvo)
    if tem_advogado:
        logger.info(f"Processo {numero}: já tem advogado — lead não criado.")
        return "tem_advogado"

    # Verificar se lead já existe
    existing = (
        sb.table("leads")
        .select("id")
        .eq("processo_id", processo_id)
        .execute()
    )
    if existing.data:
        return "duplicado"

    # Enriquecer empresa via API de CNPJ
    cnpj = proc_data.get("empresa_cnpj", "")
    enrichment = await enrich_empresa(cnpj) if cnpj else {}

    empresa_nome = (
        enrichment.get("nome")
        or proc_data.get("empresa_nome")
        or "Empresa não identificada"
    )

    empresa_row = {
        "processo_id": processo_id,
        "nome": empresa_nome,
        "cnpj": cnpj or None,
        "telefones": enrichment.get("telefones") or [],
        "email": enrichment.get("email") or None,
        "endereco": enrichment.get("endereco") or None,
        "cnpj_data": enrichment.get("cnpj_data") or None,
        "enriched_at": datetime.now(timezone.utc).isoformat() if enrichment else None,
    }

    empresa_result = sb.table("empresas").insert(empresa_row).execute()
    empresa_id = empresa_result.data[0]["id"]

    sb.table("leads").insert({
        "processo_id": processo_id,
        "empresa_id": empresa_id,
        "status": "novo",
    }).execute()

    return "lead_criado"
