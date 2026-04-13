"""
Resolução automática de CAPTCHA usando ddddocr.
Gratuito, roda 100% local, sem API externa.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_ocr = None
_ocr_old = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        import ddddocr
        _ocr = ddddocr.DdddOcr(show_ad=False)
        logger.warning("ddddocr (novo modelo) carregado")
    return _ocr


def _get_ocr_old():
    global _ocr_old
    if _ocr_old is None:
        import ddddocr
        _ocr_old = ddddocr.DdddOcr(old_model=True, show_ad=False)
        logger.warning("ddddocr (modelo antigo) carregado")
    return _ocr_old


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
    Tenta dois modelos do ddddocr (novo + antigo) com pré-processamento.
    Retorna o resultado com mais caracteres alfanuméricos, ou None.
    """
    results = []

    # Modelo novo com pré-processamento
    try:
        processed = _preprocess(image_bytes)
        r1 = _get_ocr().classification(processed)
        c1 = "".join(c for c in r1 if c.isalnum())
        logger.warning(f"CAPTCHA OCR novo='{r1}' → '{c1}'")
        if c1:
            results.append(c1)
    except Exception as e:
        logger.error(f"CAPTCHA OCR (novo modelo) erro: {e}")

    # Modelo antigo com imagem original (sem pré-processamento)
    try:
        r2 = _get_ocr_old().classification(image_bytes)
        c2 = "".join(c for c in r2 if c.isalnum())
        logger.warning(f"CAPTCHA OCR antigo='{r2}' → '{c2}'")
        if c2:
            results.append(c2)
    except Exception as e:
        logger.error(f"CAPTCHA OCR (modelo antigo) erro: {e}")

    if not results:
        return None

    # Preferir o resultado mais longo (geralmente mais correto)
    best = max(results, key=len)
    logger.warning(f"CAPTCHA escolhido: '{best}'")
    return best
