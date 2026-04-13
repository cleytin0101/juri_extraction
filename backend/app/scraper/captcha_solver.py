"""
Resolução automática de CAPTCHA usando ddddocr.
Gratuito, roda 100% local, sem API externa.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        import ddddocr
        _ocr = ddddocr.DdddOcr(show_ad=False)
        logger.warning("ddddocr carregado com sucesso")
    return _ocr


def _preprocess(image_bytes: bytes) -> bytes:
    """Grayscale + autocontrast + 2x scale + binarização."""
    import io
    from PIL import Image, ImageOps
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    img = ImageOps.autocontrast(img)
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    img = img.point(lambda x: 0 if x < 127 else 255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def solve_captcha_bytes(image_bytes: bytes) -> Optional[str]:
    """
    Resolve CAPTCHA com ddddocr + pré-processamento de imagem.
    Filtra apenas caracteres ASCII alfanuméricos (evita chinês/símbolos).
    """
    try:
        processed = _preprocess(image_bytes)
        ocr = _get_ocr()

        # Tentar modelo com preprocessamento
        result = ocr.classification(processed)
        # Filtro estrito: apenas ASCII alfanumérico (evita caracteres chineses)
        cleaned = "".join(c for c in result if c.isascii() and c.isalnum())
        logger.warning(f"CAPTCHA OCR: '{result}' → '{cleaned}'")

        if cleaned:
            return cleaned

        # Fallback: imagem original sem preprocessamento
        result2 = ocr.classification(image_bytes)
        cleaned2 = "".join(c for c in result2 if c.isascii() and c.isalnum())
        logger.warning(f"CAPTCHA OCR (fallback): '{result2}' → '{cleaned2}'")
        return cleaned2 if cleaned2 else None

    except Exception as e:
        logger.error(f"Erro ao resolver CAPTCHA: {e}")
        return None
