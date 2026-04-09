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

# Seletores para detectar campo de TOTP no PDPJ SSO
OTP_SELECTORS = [
    "input[placeholder*='digo']",        # "código"
    "input[name*='otp']",
    "input[name*='token']",
    "input[name*='totp']",
    "input[name*='code']",
    "input[id*='otp']",
    "input[id*='token']",
    "input[id*='totp']",
    "input[autocomplete='one-time-code']",
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

                # 2. Clicar em "Entrar com PDPJ"
                session.mensagem = "Clicando em 'Entrar com PDPJ'..."
                pdpj_btn = page.get_by_text("Entrar com PDPJ")
                await pdpj_btn.wait_for(timeout=10000)
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

                # 6. Clicar em ENTRAR
                session.mensagem = "Enviando credenciais..."
                await page.click("button:has-text('ENTRAR')")

                # 7. Aguardar: redirect para PJe (sucesso sem 2FA) ou campo TOTP
                for _ in range(30):  # aguarda até 15s
                    await asyncio.sleep(0.5)

                    # Sucesso direto (sem 2FA)
                    if "trt7.jus.br" in page.url and "sso.cloud.pje.jus.br" not in page.url:
                        await _save_session(context)
                        session.status = "sucesso"
                        session.mensagem = "Conectado ao PJe com sucesso!"
                        logger.info("Login PDPJ concluído sem 2FA.")
                        return

                    # Verificar se apareceu campo de TOTP
                    for sel in OTP_SELECTORS:
                        otp_field = page.locator(sel)
                        if await otp_field.count() > 0:
                            session.status = "aguardando_otp"
                            session.mensagem = "Digite o código do seu app autenticador."
                            logger.info("PDPJ solicitou código TOTP.")

                            # Aguardar o usuário fornecer o código (timeout de 3 min)
                            try:
                                await asyncio.wait_for(session.otp_event.wait(), timeout=180)
                            except asyncio.TimeoutError:
                                session.status = "erro"
                                session.mensagem = "Tempo esgotado aguardando código TOTP."
                                return

                            # Preencher código TOTP
                            session.mensagem = "Enviando código TOTP..."
                            await otp_field.fill(session.otp_code)

                            # Submeter (Enter ou botão)
                            submit_btn = page.locator(
                                "button[type='submit'], button:has-text('CONFIRMAR'), "
                                "button:has-text('VERIFICAR'), button:has-text('ENTRAR')"
                            ).first
                            if await submit_btn.count() > 0:
                                await submit_btn.click()
                            else:
                                await otp_field.press("Enter")

                            # Aguardar redirect para PJe
                            try:
                                await page.wait_for_url("**/trt7.jus.br/**", timeout=20000)
                                await _save_session(context)
                                session.status = "sucesso"
                                session.mensagem = "Conectado ao PJe com sucesso!"
                                logger.info("Login PDPJ concluído com 2FA.")
                            except Exception:
                                session.status = "erro"
                                session.mensagem = "Código inválido ou timeout após TOTP."
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


async def _save_session(context) -> None:
    """Salva o estado da sessão Playwright em disco para reutilização."""
    try:
        state = await context.storage_state()
        import json
        SESSION_FILE.write_text(json.dumps(state), encoding="utf-8")
        logger.info(f"Sessão PJe salva em {SESSION_FILE}")
    except Exception as e:
        logger.error(f"Erro ao salvar sessão: {e}")
