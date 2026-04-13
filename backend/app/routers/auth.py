"""
Login interativo no PJe via PDPJ SSO com suporte a 2FA (TOTP).

Fluxo:
1. POST /api/auth/pdpj/iniciar  → inicia sessão Playwright em background
2. GET  /api/auth/pdpj/status/{session_id} → polling do status
3. POST /api/auth/pdpj/submit-otp → envia código TOTP quando solicitado
4. GET  /api/auth/pdpj/connection-status → verifica se sessão salva existe

Após login bem-sucedido, salva pje_session.json para reutilização no scraper.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/pdpj", tags=["auth"])

LOGIN_URL = "https://pje.trt7.jus.br/primeirograu/login.seam"
SESSION_FILE = Path(__file__).parent.parent.parent / "pje_session.json"

# Seletores para detectar campo de código de verificação no PDPJ SSO
# Cobre: app autenticador (TOTP), SMS, e-mail, e variações do PDPJ
OTP_SELECTORS = [
    "input[autocomplete='one-time-code']",
    "input[name*='otp']",
    "input[name*='totp']",
    "input[name*='token']",
    "input[name*='code']",
    "input[name*='codigo']",
    "input[name*='verification']",
    "input[id*='otp']",
    "input[id*='totp']",
    "input[id*='token']",
    "input[id*='code']",
    "input[id*='codigo']",
    "input[placeholder*='digo']",       # "código" / "Código"
    "input[placeholder*='verificacao']",
    "input[placeholder*='verificação']",
    "input[placeholder*='autenticad']",  # "autenticador"
    "input[aria-label*='digo']",
    "input[aria-label*='OTP']",
    "input[aria-label*='token']",
    "input[type='tel'][maxlength]",      # campo numérico com limite (típico de OTP)
]


@dataclass
class LoginSession:
    session_id: str
    status: str = "iniciando"   # iniciando | aguardando_otp | sucesso | erro
    mensagem: str = "Iniciando login..."
    otp_event: asyncio.Event = field(default_factory=asyncio.Event)
    otp_code: str = ""
    task: Optional[asyncio.Task] = None


_sessions: dict[str, LoginSession] = {}


# ─── Modelos Pydantic ──────────────────────────────────────────────────────────

class IniciarRequest(BaseModel):
    cpf: Optional[str] = None
    senha: Optional[str] = None


class IniciarResponse(BaseModel):
    session_id: str


class StatusResponse(BaseModel):
    status: str
    mensagem: str


class SubmitOtpRequest(BaseModel):
    session_id: str
    codigo: str


class ConnectionStatusResponse(BaseModel):
    conectado: bool
    salvo_em: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/iniciar", response_model=IniciarResponse)
async def iniciar_login(body: IniciarRequest, background_tasks: BackgroundTasks):
    """Inicia o processo de login no PDPJ em background."""
    cpf = body.cpf or settings.pje_cpf
    senha = body.senha or settings.pje_senha

    session_id = str(uuid.uuid4())
    session = LoginSession(session_id=session_id)
    _sessions[session_id] = session

    background_tasks.add_task(_login_task, session, cpf, senha)
    return IniciarResponse(session_id=session_id)


@router.get("/status/{session_id}", response_model=StatusResponse)
def get_status(session_id: str):
    """Retorna o status atual da sessão de login."""
    session = _sessions.get(session_id)
    if not session:
        return StatusResponse(status="erro", mensagem="Sessão não encontrada.")
    return StatusResponse(status=session.status, mensagem=session.mensagem)


@router.post("/submit-otp")
async def submit_otp(body: SubmitOtpRequest):
    """Envia o código TOTP para a sessão aguardando 2FA."""
    session = _sessions.get(body.session_id)
    if not session:
        return {"ok": False, "erro": "Sessão não encontrada."}
    if session.status != "aguardando_otp":
        return {"ok": False, "erro": f"Sessão não está aguardando OTP (status: {session.status})."}

    session.otp_code = body.codigo.strip()
    session.otp_event.set()
    return {"ok": True}


@router.get("/connection-status", response_model=ConnectionStatusResponse)
def connection_status():
    """Verifica se há uma sessão PJe salva."""
    if SESSION_FILE.exists():
        mtime = SESSION_FILE.stat().st_mtime
        salvo_em = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
        return ConnectionStatusResponse(conectado=True, salvo_em=salvo_em)
    return ConnectionStatusResponse(conectado=False)


# ─── Tarefa de login em background ────────────────────────────────────────────

async def _login_task(session: LoginSession, cpf: str, senha: str) -> None:
    """Coroutine que executa o login no PDPJ com suporte a 2FA."""
    try:
        from playwright.async_api import async_playwright

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

            try:
                # 1. Navegar para o PJe
                session.mensagem = "Acessando portal PJe..."
                await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)

                # 2. Clicar no botão de login PDPJ
                # Tenta múltiplos seletores para cobrir variações de texto/estrutura
                session.mensagem = "Clicando em 'Entrar com PDPJ'..."
                pdpj_btn = page.locator(
                    "a:has-text('PDPJ'), button:has-text('PDPJ'), "
                    "[class*='pdpj'], [id*='pdpj'], "
                    "a:has-text('Entrar com PDPJ'), button:has-text('Entrar com PDPJ')"
                ).first
                try:
                    await pdpj_btn.wait_for(state="visible", timeout=20000)
                except Exception:
                    # Salvar screenshot para diagnóstico e mostrar URL atual
                    screenshot_path = Path(__file__).parent.parent.parent / "debug_login.png"
                    await page.screenshot(path=str(screenshot_path))
                    logger.error(
                        f"Botão PDPJ não encontrado. URL atual: {page.url} | "
                        f"Screenshot salvo em {screenshot_path}"
                    )
                    raise
                await pdpj_btn.click()

                # 3. Aguardar redirect para PDPJ SSO
                await page.wait_for_url("**/sso.cloud.pje.jus.br/**", timeout=15000)
                session.mensagem = "Preenchendo CPF e senha..."

                # 4. Preencher CPF
                cpf_input = page.locator(
                    "input[placeholder*='000'], input#username, input[name='username']"
                ).first
                await cpf_input.wait_for(timeout=8000)
                await cpf_input.fill(cpf)

                # 5. Preencher senha
                senha_input = page.locator("input[type='password']").first
                await senha_input.fill(senha)

                # 6. Clicar em ENTRAR — tenta múltiplos seletores
                session.mensagem = "Enviando credenciais..."
                # Screenshot para diagnóstico (mostra a página do SSO antes de clicar)
                debug_path = Path(__file__).parent.parent.parent / "debug_sso.png"
                await page.screenshot(path=str(debug_path))
                logger.info(f"Screenshot do SSO salvo em {debug_path} | URL: {page.url}")

                entrar_btn = page.locator(
                    "button[type='submit'], input[type='submit'], "
                    "button:has-text('Entrar'), button:has-text('ENTRAR'), "
                    "button:has-text('Login'), button:has-text('Acessar'), "
                    "button:has-text('Continuar'), button:has-text('Prosseguir')"
                ).first
                await entrar_btn.wait_for(state="visible", timeout=15000)
                await entrar_btn.click()

                # 7. Aguardar: redirect para PJe (sucesso sem 2FA) ou campo de código
                for _ in range(60):  # aguarda até 30s
                    await asyncio.sleep(0.5)

                    # Sucesso direto (sem 2FA)
                    if "trt7.jus.br" in page.url and "sso.cloud.pje.jus.br" not in page.url:
                        await _save_session(context)
                        session.status = "sucesso"
                        session.mensagem = "Conectado ao PJe com sucesso!"
                        logger.info("Login PDPJ concluído sem 2FA.")
                        return

                    # Verificar se apareceu campo de código de verificação
                    otp_selector_found = None
                    for sel in OTP_SELECTORS:
                        if await page.locator(sel).count() > 0:
                            otp_selector_found = sel
                            break

                    if otp_selector_found:
                        logger.info("PDPJ solicitou código de verificação.")
                        sucesso_otp = await _handle_otp(page, session, otp_selector_found)
                        if sucesso_otp:
                            await _save_session(context)
                            session.status = "sucesso"
                            session.mensagem = "Conectado ao PJe com sucesso!"
                            logger.info("Login PDPJ concluído com 2FA.")
                        return

                # Se chegou aqui sem sucesso
                if session.status == "iniciando":
                    session.status = "erro"
                    session.mensagem = "Login expirou ou ocorreu erro desconhecido."

            except Exception as e:
                logger.error(f"Erro no login PDPJ: {e}")
                session.status = "erro"
                session.mensagem = f"Erro: {str(e)[:200]}"
            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"Erro ao inicializar Playwright: {e}")
        session.status = "erro"
        session.mensagem = f"Erro interno: {str(e)[:200]}"


async def _handle_otp(page, session: LoginSession, otp_selector: str) -> bool:
    """
    Gerencia o fluxo de código de verificação (TOTP/SMS/e-mail) com até 3 tentativas.
    Se pje_totp_secret estiver configurado, gera o código automaticamente via pyotp.
    Retorna True se o login foi concluído com sucesso, False caso contrário.
    """
    # Auto-TOTP: se a chave está configurada, gerar e submeter automaticamente
    if settings.pje_totp_secret:
        try:
            import pyotp
            for tentativa_auto in range(1, 3):  # 2 tentativas (cobre troca de intervalo de 30s)
                totp_code = pyotp.TOTP(settings.pje_totp_secret).now()
                session.mensagem = f"Enviando código TOTP automático... (tentativa {tentativa_auto})"
                logger.info(f"TOTP automático gerado, tentativa {tentativa_auto}")

                otp_field = page.locator(otp_selector)
                await otp_field.fill(totp_code)

                submit_btn = page.locator(
                    "button[type='submit'], input[type='submit'], "
                    "button:has-text('CONFIRMAR'), button:has-text('Confirmar'), "
                    "button:has-text('VERIFICAR'), button:has-text('Verificar'), "
                    "button:has-text('CONTINUAR'), button:has-text('Continuar'), "
                    "button:has-text('ENVIAR'), button:has-text('Enviar'), "
                    "button:has-text('ENTRAR'), button:has-text('Entrar')"
                ).first
                if await submit_btn.count() > 0:
                    await submit_btn.click()
                else:
                    await otp_field.press("Enter")

                # Polling 30s: sucesso ou código rejeitado
                for _ in range(60):
                    await asyncio.sleep(0.5)
                    if "trt7.jus.br" in page.url and "sso.cloud.pje.jus.br" not in page.url:
                        return True
                    if await page.locator(otp_selector).count() > 0:
                        logger.info(f"TOTP rejeitado (tentativa {tentativa_auto}), aguardando próximo intervalo")
                        await asyncio.sleep(15)  # ~meio ciclo TOTP para tentar código diferente
                        break
                else:
                    session.status = "erro"
                    session.mensagem = "TOTP automático: timeout aguardando redirecionamento."
                    return False

            logger.warning("TOTP automático falhou 2x, iniciando fluxo manual")
        except Exception as e:
            logger.warning(f"Erro no TOTP automático: {e}, iniciando fluxo manual")

    # Fluxo manual — fallback ou quando pje_totp_secret não está configurado
    for tentativa in range(1, 4):
        # Sinalizar ao frontend que está aguardando o código
        session.status = "aguardando_otp"
        if tentativa == 1:
            session.mensagem = "Digite o código de verificação (app autenticador, SMS ou e-mail)."
        else:
            session.mensagem = f"Código incorreto ou expirado. Tente novamente ({tentativa}/3)."

        # Resetar evento para nova espera
        session.otp_event.clear()

        # Aguardar o usuário fornecer o código (timeout de 3 min)
        try:
            await asyncio.wait_for(session.otp_event.wait(), timeout=180)
        except asyncio.TimeoutError:
            session.status = "erro"
            session.mensagem = "Tempo esgotado aguardando código de verificação."
            return False

        # Re-localizar o campo OTP (evita locator stale)
        otp_field = page.locator(otp_selector)
        if await otp_field.count() == 0:
            # Tentar todos os seletores novamente (campo pode ter mudado)
            for sel in OTP_SELECTORS:
                if await page.locator(sel).count() > 0:
                    otp_field = page.locator(sel)
                    break

        # Preencher e submeter o código
        session.mensagem = "Enviando código de verificação..."
        try:
            await otp_field.fill(session.otp_code)
        except Exception as e:
            logger.warning(f"Erro ao preencher campo OTP (tentativa {tentativa}): {e}")

        submit_btn = page.locator(
            "button[type='submit'], input[type='submit'], "
            "button:has-text('CONFIRMAR'), button:has-text('Confirmar'), "
            "button:has-text('VERIFICAR'), button:has-text('Verificar'), "
            "button:has-text('CONTINUAR'), button:has-text('Continuar'), "
            "button:has-text('ENVIAR'), button:has-text('Enviar'), "
            "button:has-text('ENTRAR'), button:has-text('Entrar')"
        ).first
        if await submit_btn.count() > 0:
            await submit_btn.click()
        else:
            await otp_field.press("Enter")

        # Screenshot de diagnóstico após o submit
        debug_path = Path(__file__).parent.parent.parent / f"debug_otp_{tentativa}.png"
        await page.screenshot(path=str(debug_path))
        logger.info(f"Screenshot pós-OTP (tentativa {tentativa}) salvo em {debug_path} | URL: {page.url}")

        # Polling por 30s: sucesso (redirect para trt7) ou código inválido (campo ainda visível)
        for _ in range(60):
            await asyncio.sleep(0.5)

            # Sucesso: saiu do SSO e chegou ao PJe
            if "trt7.jus.br" in page.url and "sso.cloud.pje.jus.br" not in page.url:
                return True

            # Código inválido: campo OTP ainda visível → tentar novamente
            if await page.locator(otp_selector).count() > 0:
                logger.info(f"Código OTP rejeitado (tentativa {tentativa}), pedindo novo.")
                break
        else:
            # 30s sem sucesso nem campo OTP visível
            session.status = "erro"
            session.mensagem = "Tempo esgotado aguardando redirecionamento após o código."
            return False

    session.status = "erro"
    session.mensagem = "Número máximo de tentativas de código atingido (3/3)."
    return False


async def _save_session(context) -> None:
    """Salva o estado da sessão Playwright em disco para reutilização."""
    try:
        state = await context.storage_state()
        import json
        SESSION_FILE.write_text(json.dumps(state), encoding="utf-8")
        logger.info(f"Sessão PJe salva em {SESSION_FILE}")
    except Exception as e:
        logger.error(f"Erro ao salvar sessão: {e}")
