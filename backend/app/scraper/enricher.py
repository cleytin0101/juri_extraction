import httpx
import asyncio
from typing import Optional
from ..config import settings


async def enrich_empresa(cnpj: str) -> dict:
    """
    Consulta a API pública CNPJ.ws para enriquecer dados da empresa.
    Sem necessidade de chave de API. Rate limit: ~3 req/s.
    """
    if not cnpj:
        return {}

    digits = "".join(c for c in cnpj if c.isdigit())
    if len(digits) != 14:
        return {}

    url = f"{settings.cnpj_api_url}/{digits}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                return {
                    "nome": data.get("razao_social", ""),
                    "telefones": _extract_phones(data),
                    "email": data.get("email", ""),
                    "endereco": _format_endereco(data),
                    "cnpj_data": data,
                }
            elif r.status_code == 429:
                # Rate limit — esperar e tentar uma vez
                await asyncio.sleep(3)
                r2 = await client.get(url)
                if r2.status_code == 200:
                    data = r2.json()
                    return {
                        "nome": data.get("razao_social", ""),
                        "telefones": _extract_phones(data),
                        "email": data.get("email", ""),
                        "endereco": _format_endereco(data),
                        "cnpj_data": data,
                    }
    except Exception:
        pass

    return {}


def _extract_phones(data: dict) -> list[str]:
    phones = []
    # CNPJ.ws retorna ddd_telefone_1, telefone_1, etc.
    for i in ("1", "2"):
        ddd = str(data.get(f"ddd_telefone_{i}", "")).strip()
        tel = str(data.get(f"telefone_{i}", "")).strip()
        if ddd and tel and tel != "None":
            number = f"+55{ddd}{tel}"
            if number not in phones:
                phones.append(number)
    return phones


def _format_endereco(data: dict) -> str:
    parts = [
        data.get("logradouro", ""),
        data.get("numero", ""),
        data.get("complemento", ""),
        data.get("bairro", ""),
        data.get("municipio", {}).get("descricao", "") if isinstance(data.get("municipio"), dict) else data.get("municipio", ""),
        data.get("uf", ""),
        data.get("cep", ""),
    ]
    return ", ".join(p for p in parts if p and str(p).strip())
