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


@router.get("/chatwoot")
async def debug_chatwoot():
    """Verifica a integração Chatwoot: credenciais, conta e inboxes disponíveis."""
    import httpx
    from ..config import settings

    resultado = {
        "vars_configuradas": bool(
            settings.chatwoot_url and settings.chatwoot_api_token
            and settings.chatwoot_account_id and settings.chatwoot_inbox_id
        ),
        "chatwoot_url": settings.chatwoot_url or "(não configurado)",
        "account_id": settings.chatwoot_account_id or "(não configurado)",
        "inbox_id_configurado": settings.chatwoot_inbox_id or "(não configurado)",
        "conta_valida": False,
        "inboxes_disponiveis": [],
        "erro": None,
    }

    if not resultado["vars_configuradas"]:
        return resultado

    token = settings.chatwoot_api_token
    base = f"{settings.chatwoot_url.rstrip('/')}/api/v1/accounts/{settings.chatwoot_account_id}"
    profile_url = f"{settings.chatwoot_url.rstrip('/')}/api/v1/profile"

    auth_attempts = [
        {"headers": {"api_access_token": token}, "params": {}, "label": "header:api_access_token"},
        {"headers": {"user_access_token": token}, "params": {}, "label": "header:user_access_token"},
        {"headers": {}, "params": {"api_access_token": token}, "label": "query:api_access_token"},
    ]
    resultado["autenticado_via"] = None
    resultado["tentativas"] = []
    auth_headers = None

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            for attempt in auth_attempts:
                r = await client.get(profile_url, headers=attempt["headers"], params=attempt["params"])
                resultado["tentativas"].append({
                    "formato": attempt["label"],
                    "status": r.status_code,
                    "body": r.text[:300],
                })
                if r.is_success:
                    resultado["autenticado_via"] = attempt["label"]
                    resultado["conta_valida"] = True
                    auth_headers = attempt["headers"]
                    break

            if not resultado["conta_valida"]:
                resultado["erro"] = "Todos os 3 formatos falharam — ver campo 'tentativas'"
                return resultado

            r2 = await client.get(f"{base}/inboxes", headers=auth_headers)
            if r2.is_success:
                inboxes = r2.json().get("payload", [])
                resultado["inboxes_disponiveis"] = [
                    {"id": i.get("id"), "nome": i.get("name"), "tipo": i.get("channel_type")}
                    for i in inboxes
                ]
            else:
                resultado["erro"] = f"GET /inboxes retornou {r2.status_code}: {r2.text[:300]}"
    except Exception as e:
        resultado["erro"] = str(e)

    return resultado


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
