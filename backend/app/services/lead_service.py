import logging
from typing import Optional, List
from datetime import datetime, date, timezone

from ..database import get_supabase
from ..models.lead import LeadStatus

logger = logging.getLogger(__name__)


def get_leads(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    sb = get_supabase()
    query = sb.table("leads_completo").select("*")

    if status:
        query = query.eq("status", status)

    # count total
    count_query = sb.table("leads_completo").select("lead_id", count="exact")
    if status:
        count_query = count_query.eq("status", status)
    count_result = count_query.execute()
    total = count_result.count or 0

    offset = (page - 1) * page_size
    result = (
        query
        .order("lead_criado_em", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    return {
        "items": result.data or [],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def update_lead_status(lead_id: str, status: str) -> Optional[dict]:
    sb = get_supabase()
    result = (
        sb.table("leads")
        .update({"status": status, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", lead_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_lead_full(lead_id: str) -> Optional[dict]:
    sb = get_supabase()
    result = (
        sb.table("leads_completo")
        .select("*")
        .eq("lead_id", lead_id)
        .single()
        .execute()
    )
    return result.data


def mark_enviado(lead_id: str, mensagem_texto: str) -> None:
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    sb.table("leads").update({
        "status": "enviado",
        "mensagem_texto": mensagem_texto,
        "enviado_em": now,
        "updated_at": now,
    }).eq("id", lead_id).execute()


def log_mensagem(lead_id: str, telefone: str, mensagem: str, provider: str, provider_ref: Optional[str], status: str, erro: Optional[str]) -> None:
    sb = get_supabase()
    sb.table("mensagens_log").insert({
        "lead_id": lead_id,
        "telefone": telefone,
        "mensagem": mensagem,
        "provider": provider,
        "provider_ref": provider_ref,
        "status": status,
        "erro": erro,
    }).execute()
