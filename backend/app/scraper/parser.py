import io
import logging
import re
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


TIPO_MAP = {
    "instrução": "instrucao",
    "instrucao": "instrucao",
    "una": "una",
    "conciliação": "conciliacao",
    "conciliacao": "conciliacao",
}

PROCESSO_REGEX = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
CNPJ_REGEX = re.compile(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}")
VALOR_REGEX = re.compile(r"R?\$?\s*[\d.,]+")
TELEFONE_REGEX = re.compile(
    r"(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\s?\d{4}|\d{4})-?\d{4}"
)


def parse_numero_processo(text: str) -> Optional[str]:
    match = PROCESSO_REGEX.search(text)
    return match.group() if match else None


def extract_cnpj(text: str) -> Optional[str]:
    match = CNPJ_REGEX.search(text)
    if match:
        digits = re.sub(r"\D", "", match.group())
        return digits if len(digits) == 14 else None
    return None


def parse_valor_causa(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = re.sub(r"[R$\s]", "", text).replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_tipo_audiencia(text: str) -> str:
    if not text:
        return "outra"
    key = text.strip().lower()
    return TIPO_MAP.get(key, "outra")


def parse_data_audiencia(text: str) -> Optional[datetime]:
    formats = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]
    text = text.strip()
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


DATA_AUDIENCIA_REGEX = re.compile(
    r"(?:data|audi[eê]ncia|designad[ao]|marcad[ao])\D{0,30}?(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)",
    re.IGNORECASE,
)

NOTIFICACAO_POSTAL_REGEX = re.compile(
    r"NOTIFICA[CÇ][ÃA]O\s+POSTAL"
    r"|CARTA\s+DE\s+INTIMA[CÇ][ÃA]O"
    r"|INTIMA[CÇ][ÃA]O\s+POSTAL"
    r"|AVISO\s+DE\s+RECEBIMENTO",
    re.IGNORECASE,
)

MODALIDADE_REGEX = re.compile(
    r"\b(presencial|online|telepresencial|videoconfer[eê]ncia|virtual)\b",
    re.IGNORECASE,
)


def _extract_audiencia_from_notificacao(pages_text: list) -> dict:
    """
    Busca em páginas de notificação postal a data oficial da audiência.
    Retorna dict com 'data_audiencia' e opcionalmente 'modalidade'.
    Retorna {} se nenhuma notificação postal com data for encontrada.
    """
    for page in pages_text:
        if not NOTIFICACAO_POSTAL_REGEX.search(page):
            continue
        data_m = DATA_AUDIENCIA_REGEX.search(page)
        if not data_m:
            continue
        parsed_date = parse_data_audiencia(data_m.group(1))
        if not parsed_date:
            continue
        result: dict = {"data_audiencia": parsed_date}
        modalidade_m = MODALIDADE_REGEX.search(page)
        if modalidade_m:
            result["modalidade"] = modalidade_m.group(1).lower()
        return result
    return {}


def check_tem_advogado_reclamado(text: str) -> bool:
    """Retorna True apenas se o RECLAMADO possui advogado — ignora advogados do RECLAMANTE."""
    reclamado_m = re.search(r"RECLAMAD[AO][:\s]", text, re.IGNORECASE)
    if not reclamado_m:
        return False
    reclamado_start = reclamado_m.start()
    end_m = re.search(
        r"(?:DESPACHO|DECIS[ÃA]O|SENTEN[ÇC]A|RELAT[ÓO]RIO|CONCLUS[ÃA]O|PEDIDOS|DO\s+PROCESSO)",
        text[reclamado_start:],
        re.IGNORECASE,
    )
    if end_m:
        reclamado_section = text[reclamado_start : reclamado_start + end_m.start()]
    else:
        reclamado_section = text[reclamado_start : reclamado_start + 800]
    return bool(re.search(r"ADVOGAD[AO]", reclamado_section, re.IGNORECASE))


def parse_pdf_text(pdf_bytes: bytes) -> dict:
    """
    Extrai campos estruturados de um PDF do PJe.
    Retorna: reclamante_nome, empresa_nome, empresa_cnpj, valor_causa,
             resumo_caso, tem_advogado, orgao_julgador, data_audiencia.
    """
    result: dict = {
        "reclamante_nome": "",
        "empresa_nome": "",
        "empresa_cnpj": None,
        "valor_causa": None,
        "resumo_caso": "",
        "tem_advogado": False,
        "orgao_julgador": "",
        "data_audiencia": None,
        "modalidade_audiencia": None,
    }
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = [p.extract_text() or "" for p in pdf.pages]
            full_text = "\n".join(pages_text)
    except Exception as e:
        logger.warning(f"Erro ao ler PDF: {e}")
        return result

    # RECLAMANTE
    m = re.search(
        r"RECLAMANTE[:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇa-záàâãéêíóôõúüç\s]+?)(?=RECLAMAD|CPF|$)",
        full_text,
        re.IGNORECASE,
    )
    if m:
        result["reclamante_nome"] = m.group(1).strip()

    # RECLAMADO / empresa — aceita nomes com pontos, barras e hífens
    m = re.search(
        r"RECLAMAD[AO][:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇa-záàâãéêíóôõúüç\s\-\.\/&]+?)(?=\n|CPF|CNPJ|$)",
        full_text,
        re.IGNORECASE,
    )
    if m:
        result["empresa_nome"] = m.group(1).strip()

    # CNPJ — prioriza "CNPJ: XX.XXX.XXX/XXXX-XX" próximo ao reclamado
    reclamado_pos = full_text.lower().find("reclamad")
    nearby = full_text[reclamado_pos: reclamado_pos + 600] if reclamado_pos >= 0 else full_text
    labeled = re.search(
        r"CNPJ[:\s]+(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",
        nearby,
        re.IGNORECASE,
    )
    if labeled:
        digits = re.sub(r"\D", "", labeled.group(1))
        if len(digits) == 14:
            result["empresa_cnpj"] = digits
    else:
        search_full = full_text[reclamado_pos:] if reclamado_pos >= 0 else full_text
        cnpj_m = CNPJ_REGEX.search(search_full)
        if cnpj_m:
            digits = re.sub(r"\D", "", cnpj_m.group())
            if len(digits) == 14:
                result["empresa_cnpj"] = digits

    # Valor da causa — várias grafias possíveis
    valor_m = re.search(
        r"[Vv]alor\s+da\s+[Cc]ausa[:\s]+R?\$?\s*([\d.,]+)",
        full_text,
    )
    if valor_m:
        result["valor_causa"] = parse_valor_causa(valor_m.group(1))

    # Órgão julgador
    orgao_m = re.search(
        r"(?:VARA|JUÍZO|TRIBUNAL)[^\n]{0,60}(?:TRABALHO|TRABALHISTA)[^\n]*",
        full_text,
        re.IGNORECASE,
    )
    if orgao_m:
        result["orgao_julgador"] = orgao_m.group().strip()[:100]

    # Resumo: primeiro parágrafo após DESPACHO/DECISÃO/SENTENÇA
    resumo_m = re.search(
        r"(?:DESPACHO|DECISÃO|SENTENÇA)[^\n]*\n(.{50,500})",
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if resumo_m:
        result["resumo_caso"] = resumo_m.group(1).strip()[:500]

    # Data de audiência — prioriza notificação postal, cai no geral se não encontrar
    audiencia_info = _extract_audiencia_from_notificacao(pages_text)
    if audiencia_info:
        result["data_audiencia"] = audiencia_info["data_audiencia"]
        if audiencia_info.get("modalidade"):
            result["modalidade_audiencia"] = audiencia_info["modalidade"]
    else:
        data_m = DATA_AUDIENCIA_REGEX.search(full_text)
        if data_m:
            result["data_audiencia"] = parse_data_audiencia(data_m.group(1))

    result["tem_advogado"] = check_tem_advogado_reclamado(full_text)

    return result
