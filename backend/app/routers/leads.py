from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from ..models.lead import LeadListResponse, LeadStatusUpdate
from ..services import lead_service

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
def list_leads(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    data = lead_service.get_leads(status=status, page=page, page_size=page_size)
    return LeadListResponse(**data)


@router.patch("/{lead_id}/status")
def update_status(lead_id: str, body: LeadStatusUpdate):
    updated = lead_service.update_lead_status(lead_id, body.status.value)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return {"ok": True, "lead_id": lead_id, "status": body.status}
