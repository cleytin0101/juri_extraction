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


ADVOGADO_PATTERNS = re.compile(
    r"habilita[çc][aã]o|contesta[çc][aã]o|petição\s+de\s+habilita|peti[çc][aã]o\s+de\s+habilita",
    re.IGNORECASE,
)


def check_tem_advogado(text: str) -> bool:
    return bool(ADVOGADO_PATTERNS.search(text))


def parse_pdf_text(pdf_bytes: bytes) -> dict:
    """
    Extrai campos estruturados de um PDF do PJe.
    Retorna: reclamante_nome, empresa_nome, empresa_cnpj, valor_causa,
             resumo_caso, tem_advogado, orgao_julgador.
    """
    result: dict = {
        "reclamante_nome": "",
        "empresa_nome": "",
        "empresa_cnpj": None,
        "valor_causa": None,
        "resumo_caso": "",
        "tem_advogado": False,
        "orgao_julgador": "",
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

    # CNPJ — primeiro CNPJ válido após keyword RECLAMADO
    reclamado_pos = full_text.lower().find("reclamad")
    search_text = full_text[reclamado_pos:] if reclamado_pos >= 0 else full_text
    cnpj_m = CNPJ_REGEX.search(search_text)
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

    result["tem_advogado"] = check_tem_advogado(full_text)

    return result
