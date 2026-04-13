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
    Aplica pré-processamento (grayscale + autocontrast + scale 2x + binarização) para
    melhorar a taxa de acerto do ddddocr em CAPTCHAs com ruído visual.
    Retorna o texto reconhecido ou None em caso de erro.
    """
    try:
        import io
        from PIL import Image, ImageOps

        # Pré-processamento: remover ruído e aumentar contraste
        img = Image.open(io.BytesIO(image_bytes)).convert("L")  # grayscale
        img = ImageOps.autocontrast(img)                         # normalizar contraste
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)  # escalar 2x
        img = img.point(lambda x: 0 if x < 127 else 255)        # binarizar
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        processed_bytes = buf.getvalue()

        ocr = _get_ocr()
        result = ocr.classification(processed_bytes)
        # Limpar resultado: manter apenas alfanuméricos
        cleaned = "".join(c for c in result if c.isalnum())
        logger.warning(f"CAPTCHA OCR: '{result}' → '{cleaned}'")
        return cleaned if cleaned else None
    except Exception as e:
        logger.error(f"Erro ao resolver CAPTCHA: {e}")
        return None
