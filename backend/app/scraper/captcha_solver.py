"""
Resolução automática de CAPTCHA usando ddddocr.
Gratuito, roda 100% local, sem API externa.
Taxa de acerto: ~85-95% para CAPTCHAs de texto simples.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy load para não travar o startup se ddddocr não estiver instalado
_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        try:
            import ddddocr
            _ocr = ddddocr.DdddOcr(show_ad=False)
            logger.info("ddddocr carregado com sucesso")
        except ImportError:
            logger.error("ddddocr não instalado. Rode: pip install ddddocr")
            raise
    return _ocr


def solve_captcha_bytes(image_bytes: bytes) -> Optional[str]:
    """
    Resolve CAPTCHA a partir dos bytes da imagem.
    Retorna o texto reconhecido ou None em caso de erro.
    """
    try:
        ocr = _get_ocr()
        result = ocr.classification(image_bytes)
        # Limpar resultado: manter apenas alfanuméricos
        cleaned = "".join(c for c in result if c.isalnum())
        logger.info(f"CAPTCHA resolvido: '{result}' → '{cleaned}'")
        return cleaned
    except Exception as e:
        logger.error(f"Erro ao resolver CAPTCHA: {e}")
        return None
