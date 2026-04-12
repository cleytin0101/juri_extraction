import io
import logging
import re
from typing import Optional, List
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


def parse_numero_processo(text: str) -> Optional[str]:
    match = PROCESSO_REGEX.search(text)
    return match.group() if match else None


def extract_cnpj(text: str) -> Optional[str]:
    match = CNPJ_REGEX.search(text)
    if match:
        return re.sub(r"\D", "", match.group())  # somente dígitos
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
    """Tenta parsear data no formato brasileiro: dd/MM/yyyy HH:mm"""
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


def parse_processo_from_json(raw: dict) -> dict:
    """
    Converte dado cru interceptado do XHR do PJe para o formato interno.
    Os nomes de campos podem variar — ajustar conforme resposta real do PJe.
    """
    numero = (
        raw.get("numeroProcesso")
        or raw.get("numero_processo")
        or raw.get("numProcesso")
        or ""
    )

    valor_raw = (
        raw.get("valorCausa")
        or raw.get("valor_causa")
        or raw.get("vlCausa")
        or ""
    )

    data_raw = (
        raw.get("dataAudiencia")
        or raw.get("data_audiencia")
        or raw.get("dtAudiencia")
        or ""
    )

    tipo_raw = (
        raw.get("tipoAudiencia")
        or raw.get("tipo_audiencia")
        or raw.get("descTipoAudiencia")
        or ""
    )

    partes: List[dict] = raw.get("partes", raw.get("parts", []))
    reclamante = next(
        (p.get("nome", p.get("name", "")) for p in partes if _is_reclamante(p)), ""
    )
    reclamado = next(
        (p for p in partes if _is_reclamado(p)), {}
    )

    empresa_nome = reclamado.get("nome", reclamado.get("name", ""))
    empresa_cnpj = extract_cnpj(reclamado.get("cpfCnpj", reclamado.get("cnpj", "")))

    return {
        "numero_processo": parse_numero_processo(numero) or numero,
        "orgao_julgador": raw.get("orgaoJulgador", raw.get("orgao_julgador", "")),
        "valor_causa": parse_valor_causa(str(valor_raw)),
        "data_audiencia": parse_data_audiencia(str(data_raw)),
        "tipo_audiencia": normalize_tipo_audiencia(str(tipo_raw)),
        "resumo_caso": raw.get("assunto", raw.get("resumo", "")),
        "reclamante_nome": reclamante,
        "empresa_nome": empresa_nome,
        "empresa_cnpj": empresa_cnpj,
        "raw_data": raw,
    }


def _is_reclamante(parte: dict) -> bool:
    polo = parte.get("polo", parte.get("tipoParte", "")).lower()
    return "reclamante" in polo or "ativo" in polo


def _is_reclamado(parte: dict) -> bool:
    polo = parte.get("polo", parte.get("tipoParte", "")).lower()
    return "reclamado" in polo or "passivo" in polo or "reu" in polo


ADVOGADO_PATTERNS = re.compile(
    r"habilita[çc][aã]o|contesta[çc][aã]o|peticao\s+de\s+habilita|peti[çc][aã]o\s+de\s+habilita",
    re.IGNORECASE,
)


def check_tem_advogado(text: str) -> bool:
    """
    Verifica se o texto do PDF contém sinais de que a empresa já tem advogado:
    - Petição de habilitação (advogado se habilitando para defender a empresa)
    - Contestação (defesa já apresentada)
    Retorna True se encontrar algum desses indicadores.
    """
    return bool(ADVOGADO_PATTERNS.search(text))


def parse_pdf_text(pdf_bytes: bytes) -> dict:
    """
    Extrai campos estruturados do PDF completo do processo (baixado via 'Baixar processo na íntegra').
    Retorna dict com: reclamante_nome, empresa_nome, empresa_cnpj, valor_causa, resumo_caso,
    tem_advogado.
    Campos não encontrados ficam como None/"".
    """
    result: dict = {
        "reclamante_nome": "",
        "empresa_nome": "",
        "empresa_cnpj": None,
        "valor_causa": None,
        "resumo_caso": "",
        "tem_advogado": False,
    }
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages_text.append(text)
            full_text = "\n".join(pages_text)
    except Exception as e:
        logger.warning(f"Erro ao ler PDF com pdfplumber: {e}")
        return result

    # RECLAMANTE
    m = re.search(
        r"RECLAMANTE[:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇa-záàâãéêíóôõúüç\s]+?)(?=RECLAMAD|CPF|$)",
        full_text,
        re.IGNORECASE,
    )
    if m:
        result["reclamante_nome"] = m.group(1).strip()

    # RECLAMADO / empresa
    m = re.search(
        r"RECLAMAD[AO][:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇa-záàâãéêíóôõúüç\s\-\.\/]+?)(?=\n|CPF|CNPJ|$)",
        full_text,
        re.IGNORECASE,
    )
    if m:
        result["empresa_nome"] = m.group(1).strip()

    # CNPJ — primeiro encontrado após RECLAMADO
    reclamado_pos = full_text.lower().find("reclamad")
    search_text = full_text[reclamado_pos:] if reclamado_pos >= 0 else full_text
    cnpj_m = CNPJ_REGEX.search(search_text)
    if cnpj_m:
        result["empresa_cnpj"] = re.sub(r"\D", "", cnpj_m.group())

    # Valor da causa
    valor_m = re.search(
        r"[Vv]alor\s+da\s+[Cc]ausa[:\s]+R?\$?\s*([\d.,]+)",
        full_text,
    )
    if valor_m:
        result["valor_causa"] = parse_valor_causa(valor_m.group(1))

    # Resumo: pegar as primeiras linhas do primeiro despacho/decisão
    resumo_m = re.search(
        r"(?:DESPACHO|DECISÃO|SENTENÇA)[^\n]*\n(.{50,500})",
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if resumo_m:
        result["resumo_caso"] = resumo_m.group(1).strip()[:500]

    # Verificar se empresa já tem advogado
    result["tem_advogado"] = check_tem_advogado(full_text)

    return result
