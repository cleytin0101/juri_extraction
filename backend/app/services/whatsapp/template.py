from datetime import datetime
from typing import Optional


TEMPLATE = (
    "Olá! Aqui é o Dr. Diego Queiroz, advogado trabalhista.\n\n"
    "Identifiquei que a empresa *{empresa_nome}* possui uma demanda trabalhista "
    "em andamento com audiência prevista para {data_audiencia}.\n\n"
    "Sou especializado na defesa de empresas reclamadas e atuo exclusivamente nessa área há anos.\n\n"
    "Uma estratégia jurídica bem estruturada antes da audiência pode ajudar a reduzir "
    "possíveis condenações e gerar uma economia significativa para a empresa.\n\n"
    "Caso tenha interesse, posso explicar rapidamente os riscos envolvidos e quais "
    "estratégias podem ser adotadas para este caso, sem compromisso.\n\n"
    "Teria disponibilidade para uma conversa rápida?"
)


def render_mensagem(lead: dict) -> str:
    return TEMPLATE.format(
        empresa_nome=lead.get("empresa_nome") or "sua empresa",
        data_audiencia=_fmt_data(lead.get("data_audiencia")),
    )


def _fmt_data(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str) and value:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y")
        except ValueError:
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
