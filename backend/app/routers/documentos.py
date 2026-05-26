import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from ..models.documento import DocumentoProcessado
from ..services.document_service import process_document
from ..database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documentos", tags=["documentos"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB por arquivo


@router.post("/upload", response_model=List[DocumentoProcessado])
async def upload_documentos(
    files: List[UploadFile] = File(...),
    responsavel: Optional[str] = Form(None),
):
    """
    Recebe um ou mais PDFs de processos judiciais, extrai os dados e cria leads.
    Processa cada arquivo em sequência e retorna o resultado de cada um.
    """
    if not files:
        raise HTTPException(status_code=422, detail="Nenhum arquivo enviado.")

    resultados = []
    for upload in files:
        filename = upload.filename or "documento.pdf"

        pdf_bytes = await upload.read()
        if len(pdf_bytes) == 0:
            resultados.append(DocumentoProcessado(
                filename=filename,
                status="erro",
                erro_msg="Arquivo vazio.",
            ))
            continue

        if len(pdf_bytes) > MAX_FILE_SIZE:
            resultados.append(DocumentoProcessado(
                filename=filename,
                status="erro",
                erro_msg="Arquivo excede o limite de 50 MB.",
            ))
            continue

        try:
            resultado = await process_document(pdf_bytes, filename, responsavel=responsavel)
            resultados.append(DocumentoProcessado(**resultado))
        except Exception as e:
            logger.exception(f"Erro inesperado ao processar {filename}: {e}")
            resultados.append(DocumentoProcessado(
                filename=filename,
                status="erro",
                erro_msg=str(e),
            ))

    # Salva o batch no histórico de uploads
    try:
        sb = get_supabase()
        arquivos_json = [
            {
                "filename": r.filename,
                "status": r.status,
                "lead_id": r.lead_id,
                "empresa_nome": r.empresa_nome,
                "numero_processo": r.numero_processo,
                "erro_msg": r.erro_msg,
            }
            for r in resultados
        ]
        sb.table("upload_batches").insert({
            "total_arquivos": len(resultados),
            "criados": sum(1 for r in resultados if r.status == "criado"),
            "ja_existentes": sum(1 for r in resultados if r.status == "ja_existe"),
            "com_advogado": sum(1 for r in resultados if r.status == "tem_advogado"),
            "erros": sum(1 for r in resultados if r.status == "erro"),
            "arquivos": arquivos_json,
            "responsavel": responsavel,
        }).execute()
    except Exception as e:
        logger.warning(f"Falha ao salvar histórico do batch: {e}")

    return resultados


@router.get("/uploads")
def listar_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
):
    """Retorna o histórico de batches de upload com data, hora e resumo dos arquivos."""
    sb = get_supabase()
    offset = (page - 1) * page_size
    result = (
        sb.table("upload_batches")
        .select("*")
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    count_result = sb.table("upload_batches").select("id", count="exact").execute()
    return {
        "items": result.data or [],
        "total": count_result.count or 0,
        "page": page,
        "page_size": page_size,
    }
