import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, BackgroundTasks
from ..models.pauta import ExtrairRequest, ExtrairResponse, ExtrairJobStatus
from ..services.extraction_service import run_extraction
from ..database import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/extrair", tags=["extrair"])

# Estado em memória: key → job info (ordered insertion, Python 3.7+)
_jobs: dict[str, dict] = {}
_MAX_JOBS = 100  # manter só os últimos 100


@router.post("", response_model=ExtrairResponse, status_code=202)
async def extrair_pauta(req: ExtrairRequest, background_tasks: BackgroundTasks):
    """
    Dispara extração de pauta em background para cada combinação (vara, data).
    Retorna 202 imediatamente.
    """
    keys: List[str] = []

    sb = get_supabase()

    for vara_id in req.vara_ids:
        for data in req.datas:
            key = f"{vara_id}_{data.isoformat()}"

            # Resolver nome da vara para exibição no dashboard
            try:
                vara_result = sb.table("varas").select("nome").eq("id", vara_id).single().execute()
                vara_nome = vara_result.data["nome"] if vara_result.data else vara_id
            except Exception:
                vara_nome = vara_id

            _jobs[key] = {
                "key": key,
                "vara_id": vara_id,
                "vara_nome": vara_nome,
                "data": data.isoformat(),
                "status": "running",
                "processos_encontrados": 0,
                "leads_criados": 0,
                "processos_com_advogado": 0,
                "errors": [],
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            keys.append(key)

            # Captura de variáveis no closure
            _vara_id = vara_id
            _data = data
            _key = key

            async def _run(vara_id=_vara_id, data=_data, key=_key):
                try:
                    result = await run_extraction(vara_id, data)
                    _jobs[key] = {
                        **_jobs[key],
                        "status": "done",
                        "processos_encontrados": result.get("processos_encontrados", 0),
                        "leads_criados": result.get("leads_criados", 0),
                        "processos_com_advogado": result.get("processos_com_advogado", 0),
                        "errors": result.get("errors", []),
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                    }
                except Exception as e:
                    logger.error(f"Job {key} falhou: {e}")
                    _jobs[key] = {
                        **_jobs[key],
                        "status": "error",
                        "errors": [str(e)],
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                    }

            background_tasks.add_task(_run)

    # Limitar tamanho do histórico
    if len(_jobs) > _MAX_JOBS:
        oldest_keys = list(_jobs.keys())[: len(_jobs) - _MAX_JOBS]
        for k in oldest_keys:
            del _jobs[k]

    return ExtrairResponse(jobs_iniciados=len(keys), keys=keys)


@router.get("/status", response_model=List[ExtrairJobStatus])
def get_status():
    """Retorna os últimos jobs de extração (mais recente primeiro)."""
    jobs = list(_jobs.values())
    jobs.reverse()
    return [
        ExtrairJobStatus(
            key=j["key"],
            vara_id=j["vara_id"],
            vara_nome=j.get("vara_nome", j["vara_id"]),
            data=j["data"],
            status=j["status"],
            processos_encontrados=j.get("processos_encontrados", 0),
            leads_criados=j.get("leads_criados", 0),
            processos_com_advogado=j.get("processos_com_advogado", 0),
            errors=j.get("errors", []),
        )
        for j in jobs[:20]
    ]
