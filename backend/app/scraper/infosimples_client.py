"""
Cliente HTTP para a API da Infosimples — Tribunal / TRT-7 / Consulta Processual.

Documentação do serviço: https://infosimples.com/consultas/tribunal-trt7-processo/

A API recebe grau + numero_processo e retorna detalhes completos do processo
(polo_ativo, polo_passivo, valor_causa, assuntos, expedientes, etc.) sem
necessidade de CAPTCHA ou Playwright.
"""

import logging
from typing import Optional

import httpx

# Endpoint da Infosimples — confirme na sua conta em infosimples.com
INFOSIMPLES_API_URL = "https://api.infosimples.com/api/v2/consultas/tribunal/trt7/processo"

logger = logging.getLogger(__name__)


async def fetch_processo_infosimples(
    numero_processo: str,
    token: str,
    grau: int = 1,
) -> Optional[dict]:
    """
    Consulta detalhes de um processo via API da Infosimples.

    Retorna dicionário mapeado para o formato interno do projeto, ou None em caso
    de falha ou token ausente.
    """
    if not token:
        logger.warning("infosimples_token não configurado — pulando consulta")
        return None

    payload = {
        "token": token,
        "grau": str(grau),
        "numero_processo": numero_processo,
        "timeout": 600,
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(INFOSIMPLES_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()

        # Infosimples retorna code=200 para consulta bem-sucedida
        if data.get("code") != 200:
            logger.warning(
                f"Infosimples retornou erro para {numero_processo}: "
                f"code={data.get('code')}, errors={data.get('errors')}"
            )
            return None

        results = data.get("data", [])
        if not results:
            logger.warning(f"Infosimples: nenhum resultado para {numero_processo}")
            return None

        return _map_resultado(results[0])

    except httpx.HTTPStatusError as e:
        logger.error(f"Infosimples HTTP {e.response.status_code} para {numero_processo}: {e}")
    except httpx.RequestError as e:
        logger.error(f"Infosimples erro de conexão para {numero_processo}: {e}")
    except Exception as e:
        logger.error(f"Infosimples erro inesperado para {numero_processo}: {e}")

    return None


def _map_resultado(result: dict) -> dict:
    """Mapeia a resposta da Infosimples para o formato interno do projeto."""
    detalhes = result.get("detalhes", {})

    # Polo ativo = reclamante(s); polo passivo = reclamado(s) / empresa(s)
    polo_ativo: list = detalhes.get("polo_ativo") or []
    polo_passivo: list = detalhes.get("polo_passivo") or []

    reclamante_nome = polo_ativo[0].get("nome", "") if polo_ativo else ""

    empresa_nome = ""
    empresa_cnpj = None
    if polo_passivo:
        empresa_nome = polo_passivo[0].get("nome", "")
        doc = polo_passivo[0].get("documento", "")
        doc_digits = "".join(c for c in doc if c.isdigit())
        if len(doc_digits) == 14:
            empresa_cnpj = doc_digits

    # Valor da causa: preferir campo normalizado (float) quando disponível
    valor_causa = None
    valor_raw = detalhes.get("normalizado_valor_causa") or detalhes.get("valor_causa")
    if valor_raw is not None:
        try:
            # Pode vir como float ou string "1.234,56"
            if isinstance(valor_raw, (int, float)):
                valor_causa = float(valor_raw)
            else:
                valor_causa = float(
                    str(valor_raw).replace("R$", "").strip().replace(".", "").replace(",", ".")
                )
        except (ValueError, TypeError):
            pass

    return {
        "reclamante_nome": reclamante_nome,
        "empresa_nome": empresa_nome,
        "empresa_cnpj": empresa_cnpj,
        "valor_causa": valor_causa,
        "resumo_caso": "",
        # Campos extras da Infosimples (armazenados em raw_data)
        "orgao_julgador": detalhes.get("orgao_julgador"),
        "assuntos": detalhes.get("assuntos") or [],
        "data_distribuicao": detalhes.get("data_distribuicao"),
        "outros_interessados": detalhes.get("outros_interessados") or [],
        "raw_infosimples": result,
    }
