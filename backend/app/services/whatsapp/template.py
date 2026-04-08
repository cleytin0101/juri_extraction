from datetime import datetime
from typing import Optional


TEMPLATE = (
    "Olá, tudo bem?\n\n"
    "Sou advogado trabalhista e localizei que a empresa *{empresa_nome}* "
    "possui uma audiência trabalhista marcada para o dia *{data_audiencia}*, "
    "na {orgao_julgador} do TRT-7.\n\n"
    "O processo nº {numero_processo} envolve {reclamante_nome} e o valor da causa é de *{valor_causa}*.\n\n"
    "Ofereço assistência jurídica especializada em defesa de empresas em ações trabalhistas. "
    "Posso analisar o caso sem compromisso e apresentar uma proposta de honorários.\n\n"
    "Teria disponibilidade para uma conversa rápida?"
)


def render_mensagem(lead: dict) -> str:
    return TEMPLATE.format(
        empresa_nome=lead.get("empresa_nome") or "sua empresa",
        data_audiencia=_fmt_data(lead.get("data_audiencia")),
        orgao_julgador=lead.get("orgao_julgador") or "Vara do Trabalho",
        numero_processo=lead.get("numero_processo") or "—",
        reclamante_nome=lead.get("reclamante_nome") or "um reclamante",
        valor_causa=_fmt_valor(lead.get("valor_causa")),
    )


def _fmt_data(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y às %H:%M")
    if isinstance(value, str) and value:
        return value
    return "data a confirmar"


def _fmt_valor(value) -> str:
    if value is None:
        return "valor a confirmar"
    try:
        v = float(value)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(value)
