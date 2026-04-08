# Seletores do PJe TRT-7 — atualizar aqui se o layout do site mudar
# Use: playwright codegen https://pje.trt7.jus.br/consultaprocessual/pautas
# para redescobrir seletores após mudanças de UI.

SELECTORS = {
    # Dropdown de seleção de vara/órgão julgador
    "vara_dropdown": "select[name='codigoOrgaoJulgador'], #codigoOrgaoJulgador",
    # Input de data
    "data_input": "input[name='dataAudiencia'], input[type='date']",
    # Botão pesquisar
    "btn_pesquisar": "button[type='submit'], input[type='submit']",
    # Container de resultados
    "resultado_container": ".pautas-container, #resultado-pautas, table.pauta",
    # Linha de cada audiência
    "audiencia_row": "tr.pauta-row, tr[class*='audiencia']",
    # Link para detalhe do processo
    "processo_link": "a[href*='processo'], a[class*='processo']",
}

# Padrões de URL da API interna do PJe (interceptar XHR)
API_PATTERNS = [
    "/pje-consulta-api/",
    "/seam/resource/",
    "/api/pauta",
    "/consultaprocessual/pauta",
]
