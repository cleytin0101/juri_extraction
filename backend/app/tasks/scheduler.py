import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..database import get_supabase
from ..services.extraction_service import run_extraction

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/Fortaleza")


@scheduler.scheduled_job("cron", day_of_week="mon-fri", hour=7, minute=0)
async def daily_scrape():
    """Job automático: extrai pautas de todas as varas cadastradas às 7h."""
    logger.info("Iniciando scrape diário automático...")
    sb = get_supabase()
    varas = sb.table("varas").select("id, codigo").execute().data or []
    today = date.today()

    for vara in varas:
        try:
            result = await run_extraction(vara["id"], today)
            logger.info(
                f"Vara {vara['codigo']}: "
                f"{result['processos_encontrados']} processos, "
                f"{result['leads_criados']} leads"
            )
        except Exception as e:
            logger.error(f"Erro na vara {vara['codigo']}: {e}")
