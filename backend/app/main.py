import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import get_supabase
from .routers import leads, mensagem, metrics, configuracoes, documentos
from .routers import auth, debug, whatsapp

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_supabase()  # valida credenciais na inicialização
    yield


app = FastAPI(
    title="Juri Extraction API",
    description="Sistema de geração de leads jurídicos via upload de documentos",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documentos.router)
app.include_router(leads.router)
app.include_router(mensagem.router)
app.include_router(metrics.router)
app.include_router(configuracoes.router)
app.include_router(auth.router)
app.include_router(debug.router)
app.include_router(whatsapp.router)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
