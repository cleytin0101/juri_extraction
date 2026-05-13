from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/auth/pdpj", tags=["auth"])


class StatusResponse(BaseModel):
    status: str
    mensagem: str


class ConnectionStatusResponse(BaseModel):
    conectado: bool
    salvo_em: Optional[str] = None


@router.get("/connection-status", response_model=ConnectionStatusResponse)
def connection_status():
    return ConnectionStatusResponse(conectado=False)
