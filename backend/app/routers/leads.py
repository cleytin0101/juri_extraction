from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from ..models.lead import LeadListResponse, LeadStatusUpdate
from ..services import lead_service
from ..database import get_supabase

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/varas")
def list_varas():
    return lead_service.get_varas_disponiveis()


@router.get("", response_model=LeadListResponse)
def list_leads(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    valor_min: Optional[float] = Query(None),
    valor_max: Optional[float] = Query(None),
    data_audiencia_de: Optional[str] = Query(None),
    data_audiencia_ate: Optional[str] = Query(None),
    orgao_julgador: Optional[str] = Query(None),
):
    data = lead_service.get_leads(
        status=status,
        page=page,
        page_size=page_size,
        valor_min=valor_min,
        valor_max=valor_max,
        data_audiencia_de=data_audiencia_de,
        data_audiencia_ate=data_audiencia_ate,
        orgao_julgador=orgao_julgador,
    )
    return LeadListResponse(**data)


@router.patch("/{lead_id}/status")
def update_status(lead_id: str, body: LeadStatusUpdate):
    updated = lead_service.update_lead_status(lead_id, body.status.value)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return {"ok": True, "lead_id": lead_id, "status": body.status}


@router.delete("/{lead_id}")
def delete_lead(lead_id: str):
    sb = get_supabase()
    sb.table("leads").delete().eq("id", lead_id).execute()
    return {"ok": True, "lead_id": lead_id}
