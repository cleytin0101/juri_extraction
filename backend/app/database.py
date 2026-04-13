import logging
from supabase import create_client, Client
from .config import settings

logger = logging.getLogger(__name__)

VARAS_TRT7 = [
    ("UVT-ARA",  "Única Vara do Trabalho de Aracati"),
    ("UVT-BAT",  "Única Vara do Trabalho de Baturité"),
    ("1VT-CAU",  "1ª Vara do Trabalho de Caucaia"),
    ("2VT-CAU",  "2ª Vara do Trabalho de Caucaia"),
    ("UVT-CRA",  "Única Vara do Trabalho de Crateús"),
    ("UVT-EUS",  "Única Vara do Trabalho de Eusébio"),
    ("1VT-FOR",  "1ª Vara do Trabalho de Fortaleza"),
    ("2VT-FOR",  "2ª Vara do Trabalho de Fortaleza"),
    ("3VT-FOR",  "3ª Vara do Trabalho de Fortaleza"),
    ("4VT-FOR",  "4ª Vara do Trabalho de Fortaleza"),
    ("5VT-FOR",  "5ª Vara do Trabalho de Fortaleza"),
    ("6VT-FOR",  "6ª Vara do Trabalho de Fortaleza"),
    ("7VT-FOR",  "7ª Vara do Trabalho de Fortaleza"),
    ("8VT-FOR",  "8ª Vara do Trabalho de Fortaleza"),
    ("9VT-FOR",  "9ª Vara do Trabalho de Fortaleza"),
    ("10VT-FOR", "10ª Vara do Trabalho de Fortaleza"),
    ("11VT-FOR", "11ª Vara do Trabalho de Fortaleza"),
    ("12VT-FOR", "12ª Vara do Trabalho de Fortaleza"),
    ("13VT-FOR", "13ª Vara do Trabalho de Fortaleza"),
    ("14VT-FOR", "14ª Vara do Trabalho de Fortaleza"),
    ("15VT-FOR", "15ª Vara do Trabalho de Fortaleza"),
    ("16VT-FOR", "16ª Vara do Trabalho de Fortaleza"),
    ("17VT-FOR", "17ª Vara do Trabalho de Fortaleza"),
    ("18VT-FOR", "18ª Vara do Trabalho de Fortaleza"),
    ("VP-FOR",   "Vara Plantonista"),
    ("PA-CLE",   "Posto Avançado CLE - Secretaria Judiciária"),
    ("PA-PREC",  "Posto Avançado Divisão de Precatórios"),
    ("CEJUSC",   "CEJUSC-JT de 1º grau"),
    ("CA-FAN",   "Central de Atendimento Fórum Autran Nunes"),
    ("CORR",     "Corregedoria-Geral"),
    ("SEU",      "Secretaria de Execuções Unificadas, Pesquisas Patrimoniais e Expropriações"),
    ("GETEC",    "Posto Avançado de Execuções Coletivas - GETEC"),
    ("UVT-IGU",  "Única Vara do Trabalho de Iguatu"),
    ("1VT-CAR",  "1ª Vara do Trabalho da Região do Cariri"),
    ("2VT-CAR",  "2ª Vara do Trabalho da Região do Cariri"),
    ("3VT-CAR",  "3ª Vara do Trabalho da Região do Cariri"),
    ("CA-CAR",   "Central de Atendimento Cariri"),
    ("UVT-LIM",  "Única Vara do Trabalho de Limoeiro do Norte"),
    ("1VT-MAR",  "1ª Vara do Trabalho de Maracanaú"),
    ("2VT-MAR",  "2ª Vara do Trabalho de Maracanaú"),
    ("PA-MAG-1", "Posto Avançado do Fórum Trabalhista de Maracanaú em Maranguape - 1ª VT"),
    ("PA-MAG-2", "Posto Avançado do Fórum Trabalhista de Maracanaú em Maranguape - 2ª VT"),
    ("UVT-PAC",  "Única Vara do Trabalho de Pacajus"),
    ("UVT-QUI",  "Única Vara do Trabalho de Quixadá"),
    ("UVT-SGA",  "Única Vara do Trabalho de São Gonçalo do Amarante"),
    ("1VT-SOB",  "1ª Vara do Trabalho de Sobral"),
    ("2VT-SOB",  "2ª Vara do Trabalho de Sobral"),
    ("UVT-TIA",  "Única Vara do Trabalho de Tianguá"),
]


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_KEY precisam estar configuradas. "
            "Verifique as Environment Variables no Render (aba Environment do serviço)."
        )
    return create_client(settings.supabase_url, settings.supabase_key)


def seed_varas_if_empty(sb: Client) -> None:
    """Insere as varas do TRT-7 se a tabela estiver vazia."""
    try:
        result = sb.table("varas").select("id").limit(1).execute()
        if result.data:
            return  # já tem dados
        rows = [{"codigo": codigo, "nome": nome} for codigo, nome in VARAS_TRT7]
        sb.table("varas").upsert(rows, on_conflict="codigo").execute()
        logger.info(f"Seed: {len(rows)} varas do TRT-7 inseridas.")
    except Exception as e:
        logger.error(f"Erro ao fazer seed das varas: {e}")
