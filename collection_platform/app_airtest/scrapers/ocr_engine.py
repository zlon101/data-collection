# scrapers/ocr_engine.py
"""PaddleOCR 封装：截图 → 文字块列表。"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    text: str
    conf: float
    x: int    # bounding box 水平中心
    y: int    # bounding box 垂直中心
    width: int
    height: int


def _get_ocr():
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        raise ImportError("请先安装: uv add paddlepaddle paddleocr")
    return PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)


_ocr_instance = None


def get_ocr_instance():
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = _get_ocr()
    return _ocr_instance


def recognize(image_path: str, confidence_threshold: float = 0.5) -> list[TextBlock]:
    """对图片执行 OCR，返回 TextBlock 列表（按 y 坐标排序）。"""
    ocr = get_ocr_instance()
    result = ocr.ocr(image_path, cls=True)
    blocks = []
    for page in (result or []):
        if not page:
            continue
        for line in page:
            box, (text, conf) = line
            if conf < confidence_threshold or not text.strip():
                continue
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            blocks.append(TextBlock(
                text=text.strip(),
                conf=round(float(conf), 4),
                x=int(sum(xs) / 4),
                y=int(sum(ys) / 4),
                width=int(max(xs) - min(xs)),
                height=int(max(ys) - min(ys)),
            ))
    blocks.sort(key=lambda b: b.y)
    logger.debug("OCR 识别 %d 个文字块（图片: %s）", len(blocks), Path(image_path).name)
    return blocks