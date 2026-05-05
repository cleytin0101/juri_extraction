import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings, load_runtime_credentials
from .tasks.scheduler import scheduler
from .database import get_supabase, seed_varas_if_empty
from .routers import pautas, extrair, leads, mensagem, metrics, configuracoes
from .routers import auth, debug

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_runtime_credentials()
    sb = get_supabase()
    seed_varas_if_empty(sb)
    # Limpar extrações travadas de antes do restart (OOM crash, etc.)
    try:
        sb.table("extracoes").update({"status": "erro"}).eq("status", "processando").execute()
        logger.warning("Startup: extrações 'processando' marcadas como 'erro' (servidor reiniciado)")
    except Exception as e:
        logger.warning(f"Startup: não foi possível limpar extracoes travadas: {e}")
    from .routers.extrair import start_watchdog
    start_watchdog()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Juri Extraction API",
    description="Sistema de geração de leads jurídicos via PJe TRT-7",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pautas.router)
app.include_router(extrair.router)
app.include_router(leads.router)
app.include_router(mensagem.router)
app.include_router(metrics.router)
app.include_router(configuracoes.router)
app.include_router(auth.router)
app.include_router(debug.router)


@app.get("/health")
def health():
    return {"status": "ok"}
