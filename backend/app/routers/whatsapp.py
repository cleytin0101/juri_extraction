import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Query, HTTPException, Request

from ..config import settings
from ..database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


@router.get("/webhook")
def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Verificação do webhook pelo Meta Developers.
    O Meta faz um GET nesse endpoint quando você cadastra a URL do webhook.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        logger.info("[Webhook Meta] Verificação concluída com sucesso.")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificação inválido.")


@router.post("/webhook")
async def receber_webhook(request: Request):
    """
    Recebe eventos do Meta Cloud API:
    - Confirmação de entrega (DELIVERED)
    - Leitura (READ)
    - Resposta do cliente (mensagem recebida)

    Quando o cliente responde, busca o lead pelo número e marca como 'respondido'.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Payload inválido.")

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            # Mensagem recebida do cliente (resposta ao disparo)
            for message in value.get("messages", []):
                telefone_remetente = message.get("from")
                if not telefone_remetente:
                    continue

                logger.info(f"[Webhook Meta] Mensagem recebida de {telefone_remetente}")
                _marcar_lead_respondido(telefone_remetente)

            # Atualizações de status de entrega/leitura
            for status_update in value.get("statuses", []):
                provider_ref = status_update.get("id")
                status = status_update.get("status")
                logger.info(f"[Webhook Meta] Status atualizado: ref={provider_ref} status={status}")

    return {"status": "ok"}


def _marcar_lead_respondido(telefone: str) -> None:
    """
    Busca o lead mais recente com aquele número de telefone e atualiza para 'respondido'.
    Normaliza o número removendo '+' para comparação.
    """
    try:
        sb = get_supabase()
        numero = telefone.lstrip("+")
        numero_com_plus = f"+{numero}"

        # Busca empresa com esse telefone
        result = (
            sb.table("empresas")
            .select("id")
            .or_(f"telefones.cs.{{\"{numero}\"}},telefones.cs.{{\"{numero_com_plus}\"}}")
            .execute()
        )

        if not result.data:
            logger.warning(f"[Webhook Meta] Nenhuma empresa encontrada para {telefone}")
            return

        empresa_ids = [r["id"] for r in result.data]

        # Busca o lead mais recente com status 'enviado' para essa empresa
        lead_result = (
            sb.table("leads")
            .select("id")
            .in_("empresa_id", empresa_ids)
            .eq("status", "enviado")
            .order("enviado_em", desc=True)
            .limit(1)
            .execute()
        )

        if not lead_result.data:
            logger.info(f"[Webhook Meta] Nenhum lead 'enviado' encontrado para {telefone}")
            return

        lead_id = lead_result.data[0]["id"]
        now = datetime.now(timezone.utc).isoformat()

        sb.table("leads").update({
            "status": "respondido",
            "respondido_em": now,
            "updated_at": now,
        }).eq("id", lead_id).execute()

        logger.info(f"[Webhook Meta] Lead {lead_id} marcado como 'respondido' (tel: {telefone})")

    except Exception as exc:
        logger.error(f"[Webhook Meta] Erro ao marcar respondido para {telefone}: {exc}")
