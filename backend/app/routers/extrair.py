from fastapi import APIRouter, BackgroundTasks
from ..models.pauta import ExtrairRequest, ExtrairResponse
from ..services.extraction_service import run_extraction

router = APIRouter(prefix="/api/extrair", tags=["extrair"])

# Estado simples em memória para acompanhar extração em andamento
_extraction_results: dict = {}


@router.post("", response_model=ExtrairResponse, status_code=202)
async def extrair_pauta(req: ExtrairRequest, background_tasks: BackgroundTasks):
    """
    Dispara extração de pauta em background.
    Retorna 202 imediatamente; polling em GET /api/metrics para ver progresso.
    """
    key = f"{req.vara_id}_{req.data}"
    _extraction_results[key] = {"status": "running"}

    async def _run():
        result = await run_extraction(req.vara_id, req.data)
        _extraction_results[key] = {"status": "done", **result}

    background_tasks.add_task(_run)

    return ExtrairResponse(
        processos_encontrados=0,
        leads_criados=0,
        errors=[],
        vara_id=req.vara_id,
        data=req.data,
    )
