"""
Scraper do PJe TRT-7 usando Playwright com interceptação de XHR.

ATENÇÃO: Os seletores em selectors.py precisam ser validados contra a página
real do PJe. Use o comando abaixo para capturar seletores interativamente:

    python -m playwright codegen https://pje.trt7.jus.br/consultaprocessual/pautas

A estratégia preferida é interceptar respostas XHR (mais estável que DOM).
O fallback é parsing de DOM.
"""

import json
import asyncio
import logging
from datetime import date
from typing import List, Optional

from playwright.async_api import async_playwright, Page, Response

from ..config import settings
from .selectors import SELECTORS, API_PATTERNS
from .parser import parse_processo_from_json

logger = logging.getLogger(__name__)


async def scrape_pauta(vara_codigo: str, data_audiencia: date) -> List[dict]:
    """
    Acessa a página de pautas do PJe, filtra por vara e data,
    e retorna lista de processos parseados.
    """
    api_responses: List[dict] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            timezone_id="America/Fortaleza",
        )
        page = await context.new_page()

        # Interceptar respostas de API
        async def on_response(response: Response):
            url = response.url
            if any(pat in url for pat in API_PATTERNS):
                try:
                    ct = response.headers.get("content-type", "")
                    if "json" in ct:
                        body = await response.json()
                        api_responses.append({"url": url, "body": body})
                        logger.info(f"XHR capturado: {url}")
                except Exception as e:
                    logger.debug(f"Erro ao ler XHR {url}: {e}")

        page.on("response", on_response)

        try:
            await page.goto(
                f"{settings.pje_base_url}/pautas",
                wait_until="networkidle",
                timeout=30000,
            )

            # Selecionar vara
            await _select_vara(page, vara_codigo)

            # Preencher data
            data_str = data_audiencia.strftime("%d/%m/%Y")
            await _fill_date(page, data_str)

            # Clicar em pesquisar
            await _click_search(page)

            # Aguardar carregamento dos resultados
            await page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)  # buffer extra para XHR finalizarem

        except Exception as e:
            logger.error(f"Erro durante scraping de {vara_codigo} / {data_audiencia}: {e}")
        finally:
            await browser.close()

    # Tentar extrair dados dos XHR capturados
    processos = _extract_from_xhr(api_responses)

    if not processos:
        logger.warning(
            f"Nenhum dado XHR capturado para {vara_codigo}. "
            "Verifique os seletores e padrões de URL em selectors.py."
        )

    return processos


async def _select_vara(page: Page, vara_codigo: str) -> None:
    try:
        sel = SELECTORS["vara_dropdown"]
        await page.wait_for_selector(sel, timeout=8000)
        await page.select_option(sel, label=vara_codigo)
    except Exception:
        # Tentar abordagem alternativa: clicar no texto da vara
        try:
            await page.locator(f"text={vara_codigo}").first.click(timeout=5000)
        except Exception as e:
            logger.warning(f"Não foi possível selecionar vara '{vara_codigo}': {e}")


async def _fill_date(page: Page, data_str: str) -> None:
    try:
        sel = SELECTORS["data_input"]
        await page.wait_for_selector(sel, timeout=8000)
        await page.fill(sel, data_str)
        await page.keyboard.press("Enter")
    except Exception as e:
        logger.warning(f"Não foi possível preencher data '{data_str}': {e}")


async def _click_search(page: Page) -> None:
    try:
        sel = SELECTORS["btn_pesquisar"]
        await page.wait_for_selector(sel, timeout=5000)
        await page.click(sel)
    except Exception as e:
        logger.warning(f"Não foi possível clicar em pesquisar: {e}")


def _extract_from_xhr(responses: List[dict]) -> List[dict]:
    """
    Tenta extrair processos das respostas XHR capturadas.
    O formato exato depende da versão do PJe — inspecionar network tab
    para confirmar estrutura dos dados.
    """
    processos = []
    for resp in responses:
        body = resp.get("body")
        if isinstance(body, list):
            # Resposta é array de audiências diretamente
            for item in body:
                if isinstance(item, dict):
                    try:
                        processos.append(parse_processo_from_json(item))
                    except Exception as e:
                        logger.debug(f"Erro ao parsear item: {e}")
        elif isinstance(body, dict):
            # Procurar array aninhado: {"data": [...], "content": [...], etc.}
            for key in ("data", "content", "audiencias", "pautas", "processos", "items"):
                if key in body and isinstance(body[key], list):
                    for item in body[key]:
                        if isinstance(item, dict):
                            try:
                                processos.append(parse_processo_from_json(item))
                            except Exception as e:
                                logger.debug(f"Erro ao parsear item: {e}")
                    if processos:
                        break

    # Deduplicar por numero_processo
    seen = set()
    unique = []
    for p in processos:
        num = p.get("numero_processo", "")
        if num and num not in seen:
            seen.add(num)
            unique.append(p)

    return unique
