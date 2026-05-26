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


def _cnpj_valido(digits: str) -> bool:
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(digits[i]) * pesos1[i] for i in range(12))
    r = soma % 11
    d1 = 0 if r < 2 else 11 - r
    if int(digits[12]) != d1:
        return False
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(digits[i]) * pesos2[i] for i in range(13))
    r = soma % 11
    d2 = 0 if r < 2 else 11 - r
    return int(digits[13]) == d2


_PALAVRAS_FRASE = re.compile(
    r"\b(que|foi|pelo|pela|para|como|este|essa|com\s|nos\s|das\s|dos\s|numa|uma\s|sendo|sendo\s|admitido|caracteriza)\b",
    re.IGNORECASE,
)

_SUFIXO_EMPRESA = re.compile(
    r"\b(LTDA|S\.A\.|ME\b|EPP\b|EIRELI|S/A|SOCIEDADE|COMERCIO|COMERCIAL|INDUSTRIA|SERVICOS|SERVICOS|CONSTRUTORA|TRANSPORTES|HOLDING)\b",
    re.IGNORECASE,
)


def _nome_parece_empresa(nome: str) -> bool:
    if not nome or len(nome.strip()) < 4:
        return False
    if len(_PALAVRAS_FRASE.findall(nome)) >= 2:
        return False
    return True


def extract_cnpj(text: str) -> Optional[str]:
    match = CNPJ_REGEX.search(text)
    if match:
        digits = re.sub(r"\D", "", match.group())
        return digits if _cnpj_valido(digits) else None
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

# Verbos explícitos de designação/intimação de audiência futura (mais confiável que o regex genérico)
DESIGNACAO_AUDIENCIA_REGEX = re.compile(
    r"(?:"
    r"DESIGNA(?:NDO|R|DA|DO|M)?\s+(?:a\s+)?AUDI[ÊE]NCIA\s+(?:para\s+)?(?:o\s+dia\s+)?"
    r"|FICA(?:M)?\s+(?:as\s+partes\s+)?(?:INTIMA(?:DA|DO|S|DAS|DOS)?|NOTIFICA(?:DA|DO|S|DAS|DOS)?)\s+[^.\n]{0,60}?"
    r"|INTIMAR\s+as\s+partes[^.\n]{0,80}?"
    r"|audi[êe]ncia\s+designada\s+para\s+(?:o\s+dia\s+)?"
    r")"
    r"(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)",
    re.IGNORECASE,
)

# Palavras que indicam data de registro/autuação — não são datas de audiência
_NEGACAO_DATA_REGEX = re.compile(
    r"(?:autua[çc][aã]o|registro|protocolo|distribui[çc][aã]o|ajuizamento|propositura)\s*[:\-]?\s*\Z",
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
    """Retorna True apenas se o RECLAMADO possui advogado constituído — ignora advogados do RECLAMANTE."""
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

    # Sinal mais confiável: número da OAB na seção do reclamado
    if re.search(r"OAB\s*/?\s*[A-Z]{2}\s*/?\s*\d+", reclamado_section, re.IGNORECASE):
        return True

    # Padrão "Advogado(a): Nome" — dois-pontos indica campo preenchido com nome real
    if re.search(r"ADVOGAD[AO]\s*:\s*[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ]", reclamado_section, re.IGNORECASE):
        return True

    # Sem OAB e sem "Advogado: Nome" → assume sem advogado constituído
    # (evita falsos positivos de "sem advogado", "dispensado de advogado", etc.)
    return False


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
            pages_text = [p.extract_text() or "" for p in pdf.pages[:15]]
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

    # RECLAMADO / empresa — padrão principal + fallback com validação
    m = re.search(
        r"RECLAMAD[AO][:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇa-záàâãéêíóôõúüç\s\-\.\/&]+?)(?=\n|CPF|CNPJ|$)",
        full_text,
        re.IGNORECASE,
    )
    if m and _nome_parece_empresa(m.group(1).strip()):
        result["empresa_nome"] = m.group(1).strip()
    else:
        # Padrão alternativo para ATSum: "Reclamada: EMPRESA LTDA, CNPJ..."
        m2 = re.search(
            r"[Rr]eclama[da][ao]\s*[:\-]?\s*([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][^,\n]{3,80}?(?:LTDA|S\.A\.|ME\b|EPP\b|EIRELI|S/A|COMERCIO|INDUSTRIA|SERVICOS|CONSTRUTORA|TRANSPORTES)[^,\n]{0,40}?)(?=[,\n\(]|CNPJ|CPF|$)",
            full_text,
            re.IGNORECASE,
        )
        if m2:
            result["empresa_nome"] = m2.group(1).strip()

    # CNPJ — cascata de 3 tentativas com validação de dígitos verificadores
    reclamado_pos = full_text.lower().find("reclamad")
    search_scope = full_text[reclamado_pos:] if reclamado_pos >= 0 else full_text

    # Tentativa 1: padrão ATSum "CNPJ sob o n° XX" / "CNPJ nº XX" / "CNPJ: XX"
    t1 = re.search(
        r"CNPJ\s*(?:sob\s+o\s+n[°º.]?\s*|n[°º.]\s*|:\s*)(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})",
        search_scope,
        re.IGNORECASE,
    )
    if t1:
        digits = re.sub(r"\D", "", t1.group(1))
        if _cnpj_valido(digits):
            result["empresa_cnpj"] = digits

    # Tentativa 2: qualquer "CNPJ" seguido do número nos primeiros 600 chars após reclamad
    if not result["empresa_cnpj"]:
        nearby = search_scope[:600]
        t2 = re.search(r"CNPJ[:\s]+(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})", nearby, re.IGNORECASE)
        if t2:
            digits = re.sub(r"\D", "", t2.group(1))
            if _cnpj_valido(digits):
                result["empresa_cnpj"] = digits

    # Tentativa 3: primeiro CNPJ válido após reclamad (fallback)
    if not result["empresa_cnpj"]:
        for m_cnpj in CNPJ_REGEX.finditer(search_scope):
            digits = re.sub(r"\D", "", m_cnpj.group())
            if _cnpj_valido(digits):
                result["empresa_cnpj"] = digits
                break

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

    # Data de audiência — 3 níveis de confiança
    # Nível 1: notificação postal (mais confiável)
    audiencia_info = _extract_audiencia_from_notificacao(pages_text)
    if audiencia_info:
        result["data_audiencia"] = audiencia_info["data_audiencia"]
        if audiencia_info.get("modalidade"):
            result["modalidade_audiencia"] = audiencia_info["modalidade"]
    else:
        # Nível 2: verbos explícitos de designação/intimação de audiência
        d2_m = DESIGNACAO_AUDIENCIA_REGEX.search(full_text)
        if d2_m:
            result["data_audiencia"] = parse_data_audiencia(d2_m.group(1))
        else:
            # Nível 3 (fallback): regex genérico, mas só aceita data futura
            # e rejeita contexto de autuação/registro
            now = datetime.now()
            for data_m in DATA_AUDIENCIA_REGEX.finditer(full_text):
                ctx_start = max(0, data_m.start() - 60)
                ctx = full_text[ctx_start:data_m.start()]
                if _NEGACAO_DATA_REGEX.search(ctx):
                    continue
                parsed = parse_data_audiencia(data_m.group(1))
                if parsed and parsed > now:
                    result["data_audiencia"] = parsed
                    break

    result["tem_advogado"] = check_tem_advogado_reclamado(full_text)

    return result
