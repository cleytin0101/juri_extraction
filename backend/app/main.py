from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .tasks.scheduler import scheduler
from .routers import pautas, extrair, leads, mensagem, metrics, configuracoes


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/health")
def health():
    return {"status": "ok"}
