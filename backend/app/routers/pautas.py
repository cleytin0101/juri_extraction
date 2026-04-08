from fastapi import APIRouter
from ..database import get_supabase
from ..models.pauta import PautasResponse, Vara

router = APIRouter(prefix="/api/pautas", tags=["pautas"])


@router.get("", response_model=PautasResponse)
def list_pautas():
    sb = get_supabase()
    varas_result = sb.table("varas").select("*").order("nome").execute()
    varas = [Vara(**v) for v in (varas_result.data or [])]

    pautas_result = (
        sb.table("pautas")
        .select("data_pauta")
        .order("data_pauta", desc=True)
        .limit(30)
        .execute()
    )
    datas = sorted(
        {p["data_pauta"] for p in (pautas_result.data or [])},
        reverse=True,
    )

    return PautasResponse(varas=varas, datas_disponiveis=datas)
