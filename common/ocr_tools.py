"""
OCR 文字识别工具
基于 rapidocr_onnxruntime 实现，支持中文识别。
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text(image_path: str | Path) -> str:
    """
    对图片进行 OCR 文字识别。

    Args:
        image_path: 图片文件路径

    Returns:
        识别出的纯文本内容
    """
    try:
        from rapidocr_onnxruntime import RapidOCR

        engine = RapidOCR()
        result, _ = engine(str(image_path))

        if not result:
            logger.warning("OCR 未识别到文字: %s", image_path)
            return ""

        # 按从上到下排序（box 的 y 坐标）
        sorted_result = sorted(result, key=lambda x: x[0][0][1])

        # 提取文字并拼接
        texts = [item[1] for item in sorted_result]
        return "\n".join(texts)

    except ImportError:
        logger.error("rapidocr_onnxruntime 未安装，请运行: uv add rapidocr_onnxruntime")
        return ""
    except Exception as exc:
        logger.error("OCR 识别失败 [%s]: %s", image_path, exc)
        return ""
