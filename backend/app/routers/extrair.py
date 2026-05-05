import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter
from ..models.pauta import ExtrairRequest, ExtrairResponse, ExtrairJobStatus
from ..services.extraction_service import run_extraction
from ..database import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/extrair", tags=["extrair"])

# Estado em memória: key → job info (ordered insertion, Python 3.7+)
_jobs: dict[str, dict] = {}
_MAX_JOBS = 100

# Semáforo: limita a 1 extração simultânea para não estourar RAM no servidor
# (cada Chromium usa ~300MB; o Render free tier tem 512MB total)
_extraction_semaphore = asyncio.Semaphore(1)
_semaphore_acquired_at: Optional[float] = None  # monotonic timestamp

_EXTRACTION_TIMEOUT = 20 * 60   # 20 minutos — mata extração travada
_WATCHDOG_INTERVAL = 2 * 60     # verifica a cada 2 min
_WATCHDOG_TIMEOUT = 22 * 60     # força reset se travado há mais de 22 min


async def _watchdog():
    """Detecta semáforo permanentemente travado e força reset após 22 min."""
    while True:
        await asyncio.sleep(_WATCHDOG_INTERVAL)
        global _semaphore_acquired_at
        if _semaphore_acquired_at is not None:
            elapsed = time.monotonic() - _semaphore_acquired_at
            if elapsed > _WATCHDOG_TIMEOUT:
                logger.error(
                    f"Watchdog: semáforo travado há {elapsed / 60:.1f} min — forçando reset"
                )
                _semaphore_acquired_at = None
                if _extraction_semaphore.locked():
                    _extraction_semaphore.release()
                for key, job in list(_jobs.items()):
                    if job.get("status") == "running":
                        _jobs[key].update({
                            "status": "error",
                            "mensagem": "Timeout watchdog: extração travada por mais de 22 min",
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                        })


def start_watchdog():
    asyncio.create_task(_watchdog())


@router.post("", response_model=ExtrairResponse, status_code=202)
async def extrair_pauta(req: ExtrairRequest):
    """
    Dispara extração de pauta em background para cada combinação (vara, data).
    Retorna 202 imediatamente. Usa asyncio.create_task para garantir execução
    independente do ciclo de vida da requisição HTTP.
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
                "mensagem": "Iniciando extração...",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            keys.append(key)

            _vara_id = vara_id
            _data = data
            _key = key

            def _make_progress_cb(k: str):
                def cb(msg: str, processos: int = None, leads: int = None, com_adv: int = None):
                    if k not in _jobs:
                        return
                    update = {"mensagem": msg}
                    if processos is not None:
                        update["processos_encontrados"] = processos
                    if leads is not None:
                        update["leads_criados"] = leads
                    if com_adv is not None:
                        update["processos_com_advogado"] = com_adv
                    _jobs[k].update(update)
                return cb

            async def _run(vara_id=_vara_id, data=_data, key=_key):
                global _semaphore_acquired_at

                if _extraction_semaphore.locked():
                    _jobs[key]["mensagem"] = "Na fila — aguardando extração anterior terminar..."
                    logger.info(f"Job {key}: aguardando semáforo")

                async with _extraction_semaphore:
                    if key not in _jobs or _jobs[key]["status"] != "running":
                        return  # cancelado enquanto aguardava

                    _semaphore_acquired_at = time.monotonic()
                    _jobs[key]["mensagem"] = "Iniciando extração..."
                    logger.warning(f"Job {key}: iniciando extração ({vara_nome} / {data})")
                    try:
                        result = await asyncio.wait_for(
                            run_extraction(vara_id, data, progress_cb=_make_progress_cb(key)),
                            timeout=_EXTRACTION_TIMEOUT,
                        )
                        _jobs[key] = {
                            **_jobs[key],
                            "status": "done",
                            "mensagem": f"Concluído: {result.get('leads_criados', 0)} leads criados",
                            "processos_encontrados": result.get("processos_encontrados", 0),
                            "leads_criados": result.get("leads_criados", 0),
                            "processos_com_advogado": result.get("processos_com_advogado", 0),
                            "errors": result.get("errors", []),
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                        }
                        logger.warning(f"Job {key}: concluído — {result}")
                    except asyncio.TimeoutError:
                        logger.error(f"Job {key}: timeout de {_EXTRACTION_TIMEOUT // 60} min atingido")
                        _jobs[key] = {
                            **_jobs[key],
                            "status": "error",
                            "mensagem": f"Timeout: extração não concluiu em {_EXTRACTION_TIMEOUT // 60} minutos",
                            "errors": ["TimeoutError"],
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                        }
                    except Exception as e:
                        logger.error(f"Job {key} falhou: {e}", exc_info=True)
                        _jobs[key] = {
                            **_jobs[key],
                            "status": "error",
                            "mensagem": f"Erro: {str(e)[:100]}",
                            "errors": [str(e)],
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                        }
                    finally:
                        _semaphore_acquired_at = None

            asyncio.create_task(_run())

    # Limitar tamanho do histórico
    if len(_jobs) > _MAX_JOBS:
        oldest_keys = list(_jobs.keys())[: len(_jobs) - _MAX_JOBS]
        for k in oldest_keys:
            del _jobs[k]

    return ExtrairResponse(jobs_iniciados=len(keys), keys=keys)


@router.post("/cancel")
async def cancel_all():
    """
    Força cancelamento de todos os jobs em execução e reseta o semáforo.
    Use para destravar o sistema após um crash ou travamento.
    """
    global _semaphore_acquired_at

    cancelled = 0
    for key, job in list(_jobs.items()):
        if job.get("status") == "running":
            _jobs[key].update({
                "status": "error",
                "mensagem": "Cancelado manualmente",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            cancelled += 1

    _semaphore_acquired_at = None
    if _extraction_semaphore.locked():
        _extraction_semaphore.release()

    try:
        sb = get_supabase()
        sb.table("extracoes").update({"status": "erro"}).eq("status", "processando").execute()
    except Exception as e:
        logger.warning(f"Cancel: não foi possível atualizar banco: {e}")

    logger.warning(f"Cancel manual: {cancelled} jobs cancelados, semáforo resetado")
    return {"cancelled": cancelled, "semaforo_liberado": True}


@router.get("/status", response_model=List[ExtrairJobStatus])
def get_status():
    """
    Retorna os últimos jobs de extração (mais recente primeiro).
    Mescla jobs em memória (rodando agora) com histórico persistido no banco,
    para sobreviver restarts do servidor.
    """
    result: List[ExtrairJobStatus] = []
    seen_keys: set = set()

    # 1) Jobs em memória (inclui os que estão rodando agora)
    for j in reversed(list(_jobs.values())):
        key = j["key"]
        seen_keys.add(key)
        result.append(ExtrairJobStatus(
            key=key,
            vara_id=j["vara_id"],
            vara_nome=j.get("vara_nome", j["vara_id"]),
            data=j["data"],
            status=j["status"],
            processos_encontrados=j.get("processos_encontrados", 0),
            leads_criados=j.get("leads_criados", 0),
            processos_com_advogado=j.get("processos_com_advogado", 0),
            errors=j.get("errors", []),
            mensagem=j.get("mensagem", ""),
        ))

    # 2) Histórico do banco (sobrevive restarts)
    try:
        sb = get_supabase()
        rows = (
            sb.table("extracoes")
            .select("*, varas(nome)")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        for row in (rows.data or []):
            key = f"{row['vara_id']}_{row['data_pauta']}"
            if key in seen_keys:
                continue  # já está em memória (mais atualizado)
            seen_keys.add(key)
            vara_nome = (row.get("varas") or {}).get("nome") or row["vara_id"]
            status_map = {"processando": "running", "concluido": "done", "erro": "error"}
            status = status_map.get(row.get("status", ""), row.get("status", "error"))
            errors_raw = row.get("errors") or []
            errors = [str(e) for e in errors_raw]
            result.append(ExtrairJobStatus(
                key=key,
                vara_id=row["vara_id"],
                vara_nome=vara_nome,
                data=row["data_pauta"],
                status=status,
                processos_encontrados=row.get("processos_encontrados") or 0,
                leads_criados=row.get("leads_criados") or 0,
                processos_com_advogado=row.get("processos_com_advogado") or 0,
                errors=errors,
            ))
    except Exception as e:
        logger.warning(f"Não foi possível carregar histórico de extracoes do banco: {e}")

    return result[:30]
