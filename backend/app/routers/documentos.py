import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException

from ..models.documento import DocumentoProcessado
from ..services.document_service import process_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documentos", tags=["documentos"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB por arquivo
ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


@router.post("/upload", response_model=List[DocumentoProcessado])
async def upload_documentos(files: List[UploadFile] = File(...)):
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
                erro_msg=f"Arquivo excede o limite de 50 MB.",
            ))
            continue

        try:
            resultado = await process_document(pdf_bytes, filename)
            resultados.append(DocumentoProcessado(**resultado))
        except Exception as e:
            logger.exception(f"Erro inesperado ao processar {filename}: {e}")
            resultados.append(DocumentoProcessado(
                filename=filename,
                status="erro",
                erro_msg=str(e),
            ))

    return resultados
