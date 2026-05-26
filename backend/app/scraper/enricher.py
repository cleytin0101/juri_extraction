import httpx
import asyncio
from ..config import settings


async def enrich_empresa(cnpj: str, nome: str = "") -> dict:
    """
    Busca telefone/email da empresa em cascata:
    1. CNPJ.ws por CNPJ (gratuito)
    2. cnpja.com por CNPJ se sem telefone (usa créditos)
    3. cnpja.com por nome se ainda sem telefone (usa créditos)
    """
    result = await _enrich_cnpjws(cnpj)

    if not result.get("telefones") and cnpj:
        digits = "".join(c for c in cnpj if c.isdigit())
        if len(digits) == 14:
            fallback = await _enrich_cnpja_by_cnpj(digits)
            if fallback:
                result = {**result, **fallback}

    if not result.get("telefones") and nome:
        name_fallback = await _search_cnpja_by_name(nome)
        if name_fallback.get("telefones"):
            result["telefones"] = name_fallback["telefones"]
            if not result.get("email") and name_fallback.get("email"):
                result["email"] = name_fallback["email"]

    return result


async def _enrich_cnpjws(cnpj: str) -> dict:
    if not cnpj:
        return {}
    digits = "".join(c for c in cnpj if c.isdigit())
    if len(digits) != 14:
        return {}
    url = f"{settings.cnpj_api_url}/{digits}"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                return {
                    "nome": data.get("razao_social", ""),
                    "telefones": _extract_phones_cnpjws(data),
                    "email": data.get("email", ""),
                    "endereco": _format_endereco_cnpjws(data),
                    "cnpj_data": data,
                }
            elif r.status_code == 429:
                await asyncio.sleep(3)
                r2 = await client.get(url)
                if r2.status_code == 200:
                    data = r2.json()
                    return {
                        "nome": data.get("razao_social", ""),
                        "telefones": _extract_phones_cnpjws(data),
                        "email": data.get("email", ""),
                        "endereco": _format_endereco_cnpjws(data),
                        "cnpj_data": data,
                    }
    except Exception:
        pass
    return {}


async def _enrich_cnpja_by_cnpj(cnpj_digits: str) -> dict:
    if not settings.cnpja_api_key:
        return {}
    url = f"{settings.cnpja_api_url}/office/{cnpj_digits}"
    headers = {"Authorization": settings.cnpja_api_key}
    params = {"strategy": "CACHE_IF_FRESH", "maxAge": 45}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code == 200:
                data = r.json()
                return {
                    "nome": data.get("alias") or data.get("company", {}).get("name", ""),
                    "telefones": _extract_phones_cnpja(data),
                    "email": next(
                        (e["address"] for e in data.get("emails", []) if e.get("address")),
                        "",
                    ),
                    "cnpj_data": data,
                }
    except Exception:
        pass
    return {}


async def _search_cnpja_by_name(nome: str) -> dict:
    if not settings.cnpja_api_key or not nome:
        return {}
    url = f"{settings.cnpja_api_url}/office/search"
    headers = {"Authorization": settings.cnpja_api_key}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url, headers=headers, params={"query": nome, "limit": 3})
            if r.status_code == 200:
                offices = r.json().get("offices", [])
                for office in offices:
                    phones = _extract_phones_cnpja(office)
                    if phones:
                        return {
                            "nome": office.get("alias") or office.get("company", {}).get("name", ""),
                            "telefones": phones,
                            "email": next(
                                (e["address"] for e in office.get("emails", []) if e.get("address")),
                                "",
                            ),
                        }
    except Exception:
        pass
    return {}


def _extract_phones_cnpjws(data: dict) -> list[str]:
    phones = []
    for i in ("1", "2"):
        ddd = str(data.get(f"ddd_telefone_{i}", "")).strip()
        tel = str(data.get(f"telefone_{i}", "")).strip()
        if ddd and tel and tel != "None":
            number = f"+55{ddd}{tel}"
            if number not in phones:
                phones.append(number)
    return phones


def _extract_phones_cnpja(data: dict) -> list[str]:
    phones = []
    for p in data.get("phones", []):
        area = str(p.get("area", "")).strip()
        number = str(p.get("number", "")).strip()
        if area and number:
            full = f"+55{area}{number}"
            if full not in phones:
                phones.append(full)
    return phones


def _format_endereco_cnpjws(data: dict) -> str:
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
