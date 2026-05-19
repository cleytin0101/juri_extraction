TEMPLATE = (
    "Olá, tudo bem?\n\n"
    "Somos o escritório Queiroz & Santos Advocacia, especialistas em assessoria "
    "jurídica empresarial aqui da região.\n\n"
    "Ao analisar publicações recentes da Justiça do Trabalho, vimos que a empresa "
    "de vocês possui uma audiência marcada para os próximos dias.\n\n"
    "Como atuamos somente na defesa de empresas, resolvemos entrar em contato caso "
    "ainda não estejam sendo assessorados no processo.\n\n"
    "Se já estiverem acompanhados de advogado, agradeço desde já a atenção. Mas, "
    "caso tenham interesse, podemos explicar rapidamente como funciona nosso trabalho.\n\n"
    "Instagram profissional: @queirozesantosadvocacia"
)


def render_mensagem(lead: dict) -> str:
    return TEMPLATE
