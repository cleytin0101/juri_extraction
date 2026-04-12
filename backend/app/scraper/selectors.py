# Seletores do PJe TRT-7 — confirmados pelas imagens reais da interface
# URL base: https://pje.trt7.jus.br/consultaprocessual

SELECTORS = {
    # --- Página de pautas ---
    # Dropdown "Órgão Julgador *"
    "vara_dropdown": "select",

    # Input "Data *" (formato DD/MM/YYYY)
    "data_input": "input[type='date'], input[placeholder*='data'], input[id*='data']",

    # Botão PESQUISAR
    "btn_pesquisar": "button:has-text('PESQUISAR'), input[value='PESQUISAR']",

    # Tabela de resultados (aparece após pesquisar)
    "tabela_resultado": "table",

    # Linhas da tabela de audiências
    "audiencia_rows": "table tbody tr",

    # Link clicável do número do processo em cada linha
    "processo_link": "td a",

    # --- Página de CAPTCHA ---
    # Imagem do CAPTCHA
    "captcha_img": "img[src*='captcha'], img[alt*='captcha'], img[alt*='CAPTCHA']",

    # Campo de resposta do CAPTCHA
    "captcha_input": "input[placeholder*='Resposta'], input[id*='resposta'], input[name*='captcha'], input[id*='captcha']",

    # Botão enviar CAPTCHA
    "captcha_submit": "button:has-text('ENVIAR'), input[value='ENVIAR']",

    # --- Página de detalhe do processo ---
    # Cabeçalho com número e partes
    "processo_header": "h2, .processo-numero, [class*='processo']",

    # Reclamante (polo ativo)
    "reclamante": "text=RECLAMANTE",

    # Reclamado (polo passivo — empresa)
    "reclamado": "text=RECLAMADO",
}

# Colunas da tabela de pautas (índice 0-based)
TABLE_COLUMNS = {
    "indice": 0,
    "horario": 1,
    "tipo": 2,
    "processo": 3,
    "sala": 4,
    "situacao": 5,
}

# Padrões de URL da API interna do PJe (interceptar XHR — fallback)
API_PATTERNS = [
    "/pje-consulta-api/",
    "/seam/resource/",
    "/api/pauta",
    "/consultaprocessual/pauta",
    "/pautas",
]

# Padrões para interceptação de respostas XHR no Playwright
# Usados para capturar a resposta JSON do Angular antes de ler HTML
API_INTERCEPT_PATTERNS = [
    "/pje-consulta-api/",
    "/api/pauta",
    "/pauta",
    "/audiencia",
    "/consultaprocessual/api",
    "/seam/resource/",
]
