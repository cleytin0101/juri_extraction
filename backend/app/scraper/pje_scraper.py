"""
Scraper do PJe TRT-7 — Login PDPJ + 2 etapas:

ETAPA 0: Login via PDPJ SSO (CPF + Senha do advogado)
  → Acessa pje.trt7.jus.br/primeirograu/login.seam
  → Clica "Entrar com PDPJ" → redireciona para sso.cloud.pje.jus.br
  → Preenche CPF e Senha → redireciona de volta ao PJe autenticado

ETAPA 1: Lista de pautas (com sessão autenticada)
  → Acessa /consultaprocessual/pautas
  → Seleciona vara + data → extrai números de processo, horário, tipo

ETAPA 2: Detalhe de cada processo (requer CAPTCHA)
  → Acessa /captcha/detalhe-processo/{numero}/1
  → Resolve CAPTCHA automaticamente com ddddocr (gratuito, local)
  → Extrai nomes completos: reclamante + empresa reclamada
"""

import asyncio
import logging
import re
from datetime import date
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, Page

from .selectors import SELECTORS, TABLE_COLUMNS
from .captcha_solver import solve_captcha_bytes
from .parser import parse_numero_processo, normalize_tipo_audiencia, parse_data_audiencia, parse_pdf_text
from .infosimples_client import fetch_processo_infosimples
from ..config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://pje.trt7.jus.br/consultaprocessual"
LOGIN_URL = "https://pje.trt7.jus.br/primeirograu/login.seam"
SESSION_FILE = Path(__file__).parent.parent.parent / "pje_session.json"


async def _login_pdpj(page: Page, cpf: str, senha: str) -> bool:
    """
    Autentica no PJe via PDPJ SSO (sso.cloud.pje.jus.br).
    Fluxo: PJe login page → clica "Entrar com PDPJ" → PDPJ SSO → preenche CPF + senha → redirect de volta ao PJe.
    """
    try:
        logger.info("Iniciando login no PDPJ...")
        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)

        # Clicar no botão de login PDPJ (tenta múltiplos seletores)
        pdpj_btn = page.locator(
            "a:has-text('PDPJ'), button:has-text('PDPJ'), "
            "[class*='pdpj'], [id*='pdpj'], "
            "a:has-text('Entrar com PDPJ'), button:has-text('Entrar com PDPJ')"
        ).first
        await pdpj_btn.wait_for(state="visible", timeout=20000)
        await pdpj_btn.click()

        # Aguardar redirect para PDPJ SSO
        await page.wait_for_url("**/sso.cloud.pje.jus.br/**", timeout=15000)
        logger.info("Redirecionado para PDPJ SSO")

        # Preencher CPF/CNPJ
        cpf_input = page.locator("input[placeholder*='000'], input#username, input[name='username']").first
        await cpf_input.wait_for(timeout=8000)
        await cpf_input.fill(cpf)

        # Preencher senha
        senha_input = page.locator("input[type='password']").first
        await senha_input.fill(senha)

        # Clicar em ENTRAR — tenta múltiplos seletores
        entrar_btn = page.locator(
            "button[type='submit'], input[type='submit'], "
            "button:has-text('Entrar'), button:has-text('ENTRAR'), "
            "button:has-text('Login'), button:has-text('Acessar'), "
            "button:has-text('Continuar'), button:has-text('Prosseguir')"
        ).first
        await entrar_btn.wait_for(state="visible", timeout=15000)
        await entrar_btn.click()

        # Aguardar redirect de volta ao PJe
        await page.wait_for_url("**/trt7.jus.br/**", timeout=20000)
        logger.info("Login no PDPJ realizado com sucesso — sessão autenticada")
        return True

    except Exception as e:
        logger.error(f"Erro no login PDPJ: {e}")
        return False


async def _is_session_valid(context) -> bool:
    """Verifica se a sessão salva ainda está autenticada no PJe."""
    try:
        page = await context.new_page()
        await page.goto(f"{BASE_URL}/pautas", wait_until="domcontentloaded", timeout=15000)
        # Se redirecionar para login, a sessão expirou
        is_valid = "login" not in page.url and "sso.cloud.pje" not in page.url
        await page.close()
        return is_valid
    except Exception:
        return False


async def scrape_pauta(vara_nome: str, data_audiencia: date, cpf: str = "", senha: str = "") -> List[dict]:
    """
    Pipeline completo: login PDPJ + etapa 1 (lista) + etapa 2 (detalhe com CAPTCHA).
    Tenta reutilizar sessão salva em pje_session.json antes de fazer novo login.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        base_context_args = dict(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            timezone_id="America/Fortaleza",
        )

        # Tentar carregar sessão salva
        context = None
        if SESSION_FILE.exists():
            try:
                context = await browser.new_context(
                    storage_state=str(SESSION_FILE),
                    **base_context_args,
                )
                if await _is_session_valid(context):
                    logger.info("Sessão PJe salva reutilizada com sucesso.")
                else:
                    logger.info("Sessão PJe expirada — será feito novo login.")
                    await context.close()
                    SESSION_FILE.unlink(missing_ok=True)
                    context = None
            except Exception as e:
                logger.warning(f"Erro ao carregar sessão salva: {e}")
                context = None

        if context is None:
            context = await browser.new_context(**base_context_args)

        try:
            page = await context.new_page()

            # ETAPA 0: Login via PDPJ SSO (apenas se não há sessão válida)
            if SESSION_FILE.exists():
                logger.info("Usando sessão autenticada existente.")
            elif cpf and senha:
                login_ok = await _login_pdpj(page, cpf, senha)
                if login_ok:
                    try:
                        await context.storage_state(path=str(SESSION_FILE))
                        logger.info("Sessão PJe salva em disco após login bem-sucedido")
                    except Exception as se:
                        logger.warning(f"Não foi possível salvar sessão: {se}")
                else:
                    logger.warning("Login falhou — tentando acessar pautas sem autenticação")
            else:
                logger.info("Sem credenciais e sem sessão — acessando pautas como consulta pública")

            # ETAPA 1: extrair lista de audiências
            audiencias = await _scrape_lista_pautas(page, vara_nome, data_audiencia)
            logger.info(f"Etapa 1: {len(audiencias)} audiências encontradas em {vara_nome}")

            # ETAPA 2: detalhe de cada processo
            # Se token da Infosimples estiver configurado, usa a API (sem CAPTCHA).
            # Caso contrário, usa o scraper local com ddddocr.
            use_infosimples = bool(settings.infosimples_token)
            if use_infosimples:
                logger.info("ETAPA 2: usando API Infosimples (sem CAPTCHA)")
            else:
                logger.info("ETAPA 2: usando scraper local com CAPTCHA (token Infosimples não configurado)")

            processos = []
            for aud in audiencias:
                numero = aud.get("numero_processo", "")
                if not numero:
                    continue
                try:
                    if use_infosimples:
                        detalhe = await fetch_processo_infosimples(numero, token=settings.infosimples_token)
                        # Infosimples não fornece PDF — pdf_bytes fica None
                        if detalhe:
                            detalhe["pdf_bytes"] = None
                        await asyncio.sleep(0.5)
                    else:
                        detail_page = await context.new_page()
                        detalhe = await _scrape_detalhe_processo(
                            detail_page, numero,
                            url_override=aud.get("detalhe_href", ""),
                        )
                        await detail_page.close()
                        await asyncio.sleep(1.5)

                    if detalhe:
                        processos.append({**aud, **detalhe})
                    else:
                        processos.append(aud)

                except Exception as e:
                    logger.error(f"Erro no detalhe de {numero}: {e}")
                    processos.append(aud)

        except Exception as e:
            logger.error(f"Erro no scraping de {vara_nome}/{data_audiencia}: {e}")
            processos = []
        finally:
            await browser.close()

    return processos


async def _scrape_lista_pautas(page: Page, vara_nome: str, data_audiencia: date) -> List[dict]:
    """
    ETAPA 1: Acessa a lista pública de pautas e extrai os processos.
    Estratégia primária: interceptar resposta XHR do Angular.
    Fallback: ler tabela HTML.
    Diagnóstico: screenshots + HTML dump em cada etapa.
    """
    # Registrar listener XHR antes de qualquer navegação
    api_responses: List[dict] = []

    async def _on_response(response):
        # Capturar qualquer resposta JSON do domínio TRT-7
        if "trt7.jus.br" in response.url and response.status == 200:
            ct = response.headers.get("content-type", "")
            if "json" in ct:
                try:
                    body = await response.json()
                    api_responses.append({"url": response.url, "body": body})
                    logger.info(f"XHR capturado: {response.url}")
                except Exception:
                    pass

    page.on("response", _on_response)

    await page.goto(f"{BASE_URL}/pautas", wait_until="networkidle", timeout=30000)
    await _screenshot(page, "debug_01_pagina_carregada.png")

    # Selecionar vara — Angular Material mat-select (não é <select> nativo)
    try:
        orgao_locator = page.locator("mat-select, [role='combobox'], .mat-select").first
        await orgao_locator.wait_for(state="visible", timeout=8000)
        await orgao_locator.click()
        await asyncio.sleep(0.5)  # aguardar animação do painel

        # Aguardar opções no painel overlay
        await page.wait_for_selector("mat-option, .mat-option", timeout=8000)
        options = page.locator("mat-option, .mat-option")
        count = await options.count()
        logger.info(f"Dropdown: {count} opções disponíveis")

        found = False
        for i in range(count):
            txt = (await options.nth(i).inner_text()).strip()
            if vara_nome.lower() in txt.lower() or txt.lower() in vara_nome.lower():
                await options.nth(i).click()
                found = True
                logger.info(f"Vara selecionada: '{txt}'")
                break

        if not found:
            primeiras = [((await options.nth(i).inner_text()).strip()) for i in range(min(count, 5))]
            logger.warning(f"Vara '{vara_nome}' não encontrada. Primeiras opções: {primeiras}")
            await _screenshot(page, "debug_02_vara_erro.png")
            return []

        await _screenshot(page, "debug_02_vara_selecionada.png")
    except Exception as e:
        logger.warning(f"Erro ao selecionar vara '{vara_nome}': {e}")
        await _screenshot(page, "debug_02_vara_erro.png")
        return []

    # Preencher data — input[type="date"] com formato ISO (Angular Material datepicker)
    try:
        date_input = page.locator("input[type='date'], input[matdatepickerinput]").first
        await date_input.wait_for(state="visible", timeout=5000)
        await date_input.fill(data_audiencia.strftime("%Y-%m-%d"))
        await page.keyboard.press("Tab")
        logger.info(f"Data preenchida: {data_audiencia.strftime('%Y-%m-%d')}")
        await _screenshot(page, "debug_03_data_preenchida.png")
    except Exception as e:
        logger.warning(f"Erro ao preencher data: {e}")
        await _screenshot(page, "debug_03_data_erro.png")

    # Clicar em PESQUISAR
    try:
        btn = page.locator(SELECTORS["btn_pesquisar"]).first
        await btn.wait_for(state="visible", timeout=5000)
        await btn.click()
        await page.wait_for_load_state("networkidle", timeout=15000)
        try:
            await page.wait_for_selector("table tbody tr", timeout=8000)
        except Exception:
            pass  # Pode não ter resultados
        await asyncio.sleep(1.5)
        await _screenshot(page, "debug_04_apos_pesquisar.png")
    except Exception as e:
        logger.warning(f"Erro ao clicar em pesquisar: {e}")
        await _screenshot(page, "debug_04_pesquisar_erro.png")
        return []

    # Tentar usar dados XHR capturados primeiro (mais confiável que HTML)
    if api_responses:
        logger.info(f"Tentando parsear {len(api_responses)} resposta(s) XHR...")
        audiencias = _parse_xhr_responses(api_responses, vara_nome, data_audiencia)
        if audiencias:
            logger.info(f"XHR: {len(audiencias)} audiências extraídas")
            return audiencias

    # Fallback: ler tabela HTML
    audiencias = await _parse_tabela_pautas(page, vara_nome, data_audiencia)

    # Se ainda 0, dumpar HTML + logs para diagnóstico
    if not audiencias:
        logger.warning(f"0 audiências encontradas para {vara_nome} / {data_audiencia}")
        logger.warning(f"URLs XHR capturadas: {[r['url'] for r in api_responses]}")
        try:
            html = await page.content()
            with open("debug_html_sem_resultados.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.warning("HTML da página salvo: debug_html_sem_resultados.html")
        except Exception:
            pass

    return audiencias


async def _screenshot(page: Page, path: str) -> None:
    """Salva screenshot silenciosamente (falha não interrompe o fluxo)."""
    try:
        await page.screenshot(path=path, full_page=False)
    except Exception:
        pass


def _parse_xhr_responses(responses: List[dict], vara_nome: str, data_audiencia: date) -> List[dict]:
    """
    Tenta extrair audiências de respostas XHR capturadas.
    Loga o JSON para diagnóstico e tenta campos comuns de paginação Angular.
    """
    for r in responses:
        body = r["body"]
        logger.warning(f"XHR [{r['url']}] amostra: {str(body)[:400]}")

        items = None
        if isinstance(body, list):
            items = body
        elif isinstance(body, dict):
            for key in ("data", "items", "audiencias", "content", "list", "result", "rows", "pautas"):
                if isinstance(body.get(key), list):
                    items = body[key]
                    logger.info(f"XHR: lista encontrada em body['{key}'] com {len(items)} items")
                    break

        if items:
            return _map_xhr_items(items, vara_nome, data_audiencia)

    return []


def _map_xhr_items(items: list, vara_nome: str, data_audiencia: date) -> List[dict]:
    """
    Mapeia items do JSON XHR para o formato interno de audiência.
    Tenta campos comuns que o PJe costuma usar.
    """
    audiencias = []
    for item in items:
        if not isinstance(item, dict):
            continue

        # Número do processo — vários nomes possíveis
        numero = (
            item.get("numeroProcesso")
            or item.get("numero_processo")
            or item.get("processo")
            or item.get("numProcesso")
            or ""
        )
        numero = parse_numero_processo(str(numero)) if numero else ""
        if not numero:
            continue

        horario = str(item.get("horario") or item.get("hora") or item.get("horaAudiencia") or "")
        tipo_raw = str(item.get("tipo") or item.get("tipoAudiencia") or item.get("tipo_audiencia") or "")
        sala = str(item.get("sala") or item.get("local") or "")
        situacao = str(item.get("situacao") or item.get("status") or "")

        data_hora_str = f"{data_audiencia.strftime('%d/%m/%Y')} {horario}"
        data_hora = parse_data_audiencia(data_hora_str)

        audiencias.append({
            "numero_processo": numero,
            "orgao_julgador": vara_nome,
            "data_audiencia": data_hora or data_audiencia,
            "tipo_audiencia": normalize_tipo_audiencia(tipo_raw),
            "sala": sala,
            "situacao": situacao,
            "horario": horario,
            "reclamante_nome": str(item.get("reclamante") or item.get("reclamanteNome") or ""),
            "empresa_nome": str(item.get("reclamado") or item.get("reclamadoNome") or ""),
            "empresa_cnpj": None,
            "valor_causa": None,
            "resumo_caso": "",
            "raw_data": item,
        })

    return audiencias


async def _parse_tabela_pautas(page: Page, vara_nome: str, data_audiencia: date) -> List[dict]:
    """Lê a tabela de audiências e extrai os dados de cada linha."""
    audiencias = []

    try:
        rows = page.locator("table tbody tr")
        count = await rows.count()
        logger.info(f"Linhas na tabela: {count}")

        for i in range(count):
            row = rows.nth(i)
            cells = row.locator("td")
            cell_count = await cells.count()

            if cell_count < 4:
                continue

            try:
                horario = (await cells.nth(TABLE_COLUMNS["horario"]).inner_text()).strip()
                tipo_raw = (await cells.nth(TABLE_COLUMNS["tipo"]).inner_text()).strip()
                processo_cell = cells.nth(TABLE_COLUMNS["processo"])
                processo_text = (await processo_cell.inner_text()).strip()

                # Extrair número do processo + capturar href real do link
                numero = parse_numero_processo(processo_text)
                link = processo_cell.locator("a").first
                detalhe_href = ""
                if await link.count() > 0:
                    href_raw = await link.get_attribute("href") or ""
                    if not numero:
                        numero = parse_numero_processo(href_raw)
                    if href_raw.startswith("http"):
                        detalhe_href = href_raw
                    elif href_raw.startswith("/"):
                        detalhe_href = f"https://pje.trt7.jus.br{href_raw}"
                    logger.warning(f"Linha {i}: processo='{processo_text}' href='{href_raw}'")

                if not numero:
                    logger.debug(f"Linha {i}: número de processo não encontrado em '{processo_text}'")
                    continue

                sala = (await cells.nth(TABLE_COLUMNS["sala"]).inner_text()).strip() if cell_count > TABLE_COLUMNS["sala"] else ""
                situacao = (await cells.nth(TABLE_COLUMNS["situacao"]).inner_text()).strip() if cell_count > TABLE_COLUMNS["situacao"] else ""

                # Montar data+hora da audiência
                data_hora_str = f"{data_audiencia.strftime('%d/%m/%Y')} {horario}"
                data_hora = parse_data_audiencia(data_hora_str)

                audiencias.append({
                    "numero_processo": numero,
                    "orgao_julgador": vara_nome,
                    "data_audiencia": data_hora or data_audiencia,
                    "tipo_audiencia": normalize_tipo_audiencia(tipo_raw),
                    "sala": sala,
                    "situacao": situacao,
                    "horario": horario,
                    "detalhe_href": detalhe_href,
                    # Campos a preencher na etapa 2
                    "reclamante_nome": "",
                    "empresa_nome": "",
                    "empresa_cnpj": None,
                    "valor_causa": None,
                    "resumo_caso": "",
                    "raw_data": {
                        "tipo_raw": tipo_raw,
                        "processo_text": processo_text,
                        "situacao": situacao,
                    },
                })

            except Exception as e:
                logger.debug(f"Erro ao processar linha {i}: {e}")

    except Exception as e:
        logger.error(f"Erro ao parsear tabela: {e}")

    return audiencias


async def _scrape_detalhe_processo(page: Page, numero: str, url_override: str = "") -> Optional[dict]:
    """
    ETAPA 2: Acessa a página de detalhe do processo.
    Resolve o CAPTCHA automaticamente com ddddocr e extrai partes.
    url_override: se fornecido, usa este URL em vez de construir a partir do número.
    """
    url = url_override if url_override else f"{BASE_URL}/captcha/detalhe-processo/{numero}/1"
    logger.warning(f"Detalhe {numero}: acessando URL={url}")

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception as e:
        logger.warning(f"Erro ao acessar detalhe de {numero}: {e}")
        return None

    await _screenshot(page, "debug_05_detalhe_carregado.png")
    page_title = await page.title()
    logger.warning(f"Detalhe {numero}: URL_atual={page.url} | título='{page_title}'")

    # Verificar se tem CAPTCHA
    captcha_img = page.locator(SELECTORS["captcha_img"])
    captcha_count = await captcha_img.count()
    todas_imgs = await page.locator("img").count()
    logger.info(f"Detalhe {numero}: captcha_img encontrado={captcha_count > 0} | total <img>={todas_imgs}")

    if captcha_count == 0:
        # Sem CAPTCHA — página carregou direto
        await _screenshot(page, "debug_06_detalhe_sem_captcha.png")
        try:
            suffix = numero[-10:].replace(".", "").replace("-", "")
            html_content = await page.content()
            with open(f"debug_detalhe_{suffix}.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.warning(f"Detalhe {numero}: HTML salvo em debug_detalhe_{suffix}.html ({len(html_content)} chars)")
        except Exception:
            pass
        html_data = await _extract_partes(page)
        pdf_bytes = await _download_processo_pdf(page, numero)
        html_data["pdf_bytes"] = pdf_bytes
        if pdf_bytes:
            pdf_data = parse_pdf_text(pdf_bytes)
            for key in ("reclamante_nome", "empresa_nome", "empresa_cnpj", "valor_causa", "resumo_caso", "tem_advogado"):
                if pdf_data.get(key) is not None and pdf_data.get(key) != "":
                    html_data[key] = pdf_data[key]
        if not html_data.get("empresa_nome") and not html_data.get("reclamante_nome"):
            try:
                suffix = numero[-10:].replace(".", "").replace("-", "")
                html_content = await page.content()
                with open(f"debug_detalhe_{suffix}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.warning(f"Detalhe {numero}: campos vazios (sem captcha) — HTML salvo em debug_detalhe_{suffix}.html")
            except Exception:
                pass
        return html_data

    # Resolver CAPTCHA (até 5 tentativas)
    for tentativa in range(1, 6):
        try:
            # Preferir download direto via src (imagem original, sem artefatos de render)
            img_bytes: Optional[bytes] = None
            try:
                captcha_src = await captcha_img.first.get_attribute("src") or ""
                if captcha_src:
                    if captcha_src.startswith("/"):
                        captcha_src = f"https://pje.trt7.jus.br{captcha_src}"
                    resp = await page.request.get(captcha_src)
                    if resp.ok:
                        img_bytes = await resp.body()
                        logger.warning(f"CAPTCHA src={captcha_src} ({len(img_bytes)} bytes)")
            except Exception as src_err:
                logger.warning(f"CAPTCHA download via src falhou: {src_err}")

            if not img_bytes:
                img_bytes = await captcha_img.screenshot()

            # Salvar imagem do CAPTCHA para diagnóstico
            try:
                suffix = numero[-10:].replace(".", "").replace("-", "")
                with open(f"debug_captcha_{suffix}.png", "wb") as f:
                    f.write(img_bytes)
            except Exception:
                pass

            resposta = solve_captcha_bytes(img_bytes)
            logger.warning(f"CAPTCHA tentativa {tentativa}: resposta='{resposta}'")

            if not resposta:
                logger.warning(f"CAPTCHA não resolvido (tentativa {tentativa})")
                continue

            # Preencher resposta
            captcha_input = page.locator(SELECTORS["captcha_input"])
            await captcha_input.fill(resposta)

            # Enviar
            await page.get_by_text("ENVIAR").click()
            await page.wait_for_load_state("domcontentloaded", timeout=10000)
            await asyncio.sleep(1)

            # Verificar se CAPTCHA foi aceito (página mudou)
            if await captcha_img.count() > 0:
                logger.warning(f"CAPTCHA incorreto (tentativa {tentativa}), tentando novamente...")
                # Recarregar para novo CAPTCHA
                await page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(1)
                captcha_img = page.locator(SELECTORS["captcha_img"])
                continue

            # CAPTCHA aceito — extrair dados do HTML e do PDF
            logger.info(f"CAPTCHA resolvido com sucesso (tentativa {tentativa})")
            html_data = await _extract_partes(page)

            # Tentar baixar o PDF completo e enriquecer com dados dele
            pdf_bytes = await _download_processo_pdf(page, numero)
            html_data["pdf_bytes"] = pdf_bytes  # armazenar para upload posterior
            if pdf_bytes:
                pdf_data = parse_pdf_text(pdf_bytes)
                for key in ("reclamante_nome", "empresa_nome", "empresa_cnpj", "valor_causa", "resumo_caso", "tem_advogado"):
                    if pdf_data.get(key) is not None and pdf_data.get(key) != "":
                        html_data[key] = pdf_data[key]

            return html_data

        except Exception as e:
            logger.warning(f"Erro na tentativa {tentativa} do CAPTCHA de {numero}: {e}")

    logger.warning(f"Não foi possível resolver CAPTCHA de {numero} após 5 tentativas")
    return None


async def _download_processo_pdf(page: Page, numero: str) -> Optional[bytes]:
    """
    Clica no botão 'Baixar processo na íntegra' e retorna os bytes do PDF baixado.
    O download é interceptado pelo Playwright antes de tocar o disco.
    """
    try:
        # O botão aparece como ícone PDF ou link com esse texto
        download_btn = page.locator(
            "a[title*='ntegra'], a[href*='baixar'], a[href*='inteira'], "
            "button:has-text('ntegra'), a:has-text('ntegra')"
        ).first

        if await download_btn.count() == 0:
            # Fallback: qualquer link que pareça download de processo
            download_btn = page.locator("a[href*='.pdf'], a[href*='download']").first

        if await download_btn.count() == 0:
            logger.warning(f"Botão de download não encontrado para {numero}")
            return None

        async with page.expect_download(timeout=60000) as download_info:
            await download_btn.click()

        download = await download_info.value
        pdf_bytes = await (await download.path()).read_bytes() if await download.path() else None

        # Alternativa: ler do stream
        if pdf_bytes is None:
            stream = await download.open_read_stream()
            chunks = []
            while True:
                chunk = await stream.read(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            pdf_bytes = b"".join(chunks)

        logger.info(f"PDF baixado para {numero}: {len(pdf_bytes or b'')} bytes")
        return pdf_bytes

    except Exception as e:
        logger.warning(f"Erro ao baixar PDF de {numero}: {e}")
        return None


async def _extract_partes(page: Page) -> dict:
    """
    Extrai reclamante e empresa reclamada da página de detalhe.
    Baseado no layout visto nas imagens: 'RECLAMANTE: ...' e 'RECLAMADO: ...'
    """
    result = {
        "reclamante_nome": "",
        "empresa_nome": "",
        "empresa_cnpj": None,
        "valor_causa": None,
        "resumo_caso": "",
    }

    try:
        content = await page.content()

        # Extrair RECLAMANTE
        reclamante_match = re.search(
            r"RECLAMANTE[:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇa-záàâãéêíóôõúüç\s]+?)(?=RECLAMADO|$)",
            content,
            re.IGNORECASE,
        )
        if reclamante_match:
            result["reclamante_nome"] = reclamante_match.group(1).strip()

        # Extrair RECLAMADO (empresa)
        reclamado_match = re.search(
            r"RECLAMADO[:\s]+([A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇa-záàâãéêíóôõúüç\s\-\.\/]+?)(?=\n|<|CNPJ|CPF|$)",
            content,
            re.IGNORECASE,
        )
        if reclamado_match:
            result["empresa_nome"] = reclamado_match.group(1).strip()

        # Tentar extrair CNPJ se presente
        cnpj_match = re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", content)
        if cnpj_match:
            result["empresa_cnpj"] = re.sub(r"\D", "", cnpj_match.group())

        # Tentar extrair valor da causa
        valor_match = re.search(r"[Vv]alor[:\s]+R?\$?\s*([\d.,]+)", content)
        if valor_match:
            try:
                v = valor_match.group(1).replace(".", "").replace(",", ".")
                result["valor_causa"] = float(v)
            except ValueError:
                pass

    except Exception as e:
        logger.warning(f"Erro ao extrair partes: {e}")

    return result
