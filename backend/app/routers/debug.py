import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/debug", tags=["debug"])

_ALLOWED_PREFIXES = ("debug_",)


@router.get("/screenshots")
def list_debug_files():
    """Lista screenshots e HTML dumps gerados pelo scraper para diagnóstico."""
    files = sorted(
        list(Path(".").glob("debug_*.png")) + list(Path(".").glob("debug_*.html")),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return [
        {"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
        for f in files
    ]


@router.get("/screenshots/{filename}")
def download_debug_file(filename: str):
    """Baixa um arquivo de diagnóstico pelo nome."""
    if not any(filename.startswith(p) for p in _ALLOWED_PREFIXES):
        raise HTTPException(status_code=403, detail="Acesso negado")
    path = Path(filename)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    media_type = "text/html" if filename.endswith(".html") else "image/png"
    return FileResponse(path, media_type=media_type, filename=filename)
