"""
微信公众号招聘文章分析模块
==========================
采集 → OCR（可选）+ LLM 视觉提取 → LLM 智能合并 Markdown → LLM 投递判断

用法:
    uv run --package data-collection-platform python -m wx.recruit_analyzer.analyze \
        --url "https://mp.weixin.qq.com/s?__biz=..."

或者作为模块调用:
    from wx.recruit_analyzer import analyze_url
    result = await analyze_url(url)
"""

import os
import logging
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

from .llm_operations import extract_from_vision, analyze_recruit_llm
from .merge_parser import build_markdown

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

logger = logging.getLogger(__name__)


async def analyze_recruit(url: str, enable_ocr: bool = False) -> dict:
    """
    完整分析流程：采集 → OCR（可选）→ LLM 视觉提取 → LLM 智能合并 Markdown → LLM 投递判断。

    步骤:
    1. 用 Playwright 采集页面（HTML + 截图）
    2. 用 rapidocr 对截图进行 OCR 识别（可选）
    3. 用多模态 LLM 从截图提取结构化信息
    4. LLM 智能合并 HTML + 视觉提取 + OCR → 结构化 Markdown
    5. LLM 投递判断

    Args:
        url: 微信文章 URL
        enable_ocr: 是否启用 OCR 识别（默认关闭）

    Returns:
        dict: {
            "url": str,
            "markdown_filename": str,
            "analyzed_filename": str,
            "analysis": dict,
        }
    """
    from browser_playwright.puppeteer import capture_recruit_page

    # 步骤 1: 采集页面
    logger.info("开始采集: %s", url)
    captured = await capture_recruit_page(url)

    # 步骤 2: OCR 识别截图（可选）
    screenshot_path = captured.get("screenshot_path", "")
    ocr_text = ""
    if enable_ocr and screenshot_path and os.path.exists(screenshot_path):
        from common import ocr_tools
        logger.info("开始 OCR 识别...")
        ocr_text = ocr_tools.extract_text(screenshot_path)
        logger.info("OCR 识别完成，字符数: %d", len(ocr_text))
    elif enable_ocr:
        logger.warning("截图文件不存在，跳过 OCR")

    # 步骤 3: LLM 视觉提取
    logger.info("开始 LLM 视觉提取...")
    vision_text = ""
    if screenshot_path and os.path.exists(screenshot_path):
        vision_text = await extract_from_vision(
            screenshot_path=screenshot_path,
            html_text=captured.get("body_html", ""),
        )
    else:
        logger.warning("截图文件不存在，跳过视觉提取")

    # 步骤 4: LLM 智能合并为 Markdown
    markdown_content = await build_markdown(
        title=captured.get("title", ""),
        html_text=captured.get("body_html", ""),
        vision_text=vision_text,
        ocr_text=ocr_text,
        url=url,
    )

    # 保存 Markdown
    raw_filename = captured.get("raw_filename", "")
    if raw_filename:
        _save_markdown(markdown_content, raw_filename)

    # 步骤 5: LLM 投递判断
    logger.info("开始 LLM 投递判断...")
    analysis = await analyze_recruit_llm(markdown_content)

    # 组装结果
    result = {
        "url": url,
        "captured_at": captured.get("captured_at", ""),
        "markdown_filename": f"{Path(raw_filename).stem}_parsed.md" if raw_filename else "",
        "analysis": analysis,
    }

    if raw_filename:
        analyzed_filename = _save_analyzed(result, raw_filename)
        result["analyzed_filename"] = analyzed_filename

    return result


async def analyze_url(url: str, enable_ocr: bool = False) -> dict:
    """对外调用的入口。"""
    return await analyze_recruit(url, enable_ocr=enable_ocr)


def main():
    """命令行入口。"""
    parser = argparse.ArgumentParser(description="微信招聘文章分析")
    parser.add_argument("--url", required=True, help="微信文章 URL")
    parser.add_argument("--ocr", action="store_true", help="启用 OCR 识别")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    import asyncio
    result = asyncio.run(analyze_url(args.url, enable_ocr=args.ocr))

    # 打印结果
    analysis = result.get("analysis", {})
    print("\n" + "=" * 60)
    print("📋 招聘分析结果")
    print("=" * 60)
    print(f"公司：{analysis.get('company', 'N/A')}")
    print(f"岗位数：{len(analysis.get('positions', []))}")
    print(f"投递方式：{analysis.get('application_method', 'N/A')}")
    print(f"截止：{analysis.get('deadline', '未注明')}")
    print(f"是否投递：{'✅ 建议投递' if analysis.get('should_apply') else ' 不建议投递'}")
    print(f"原因：{analysis.get('apply_reason', '')}")

    if analysis.get("positions"):
        print("\n岗位详情:")
        for i, pos in enumerate(analysis["positions"], 1):
            print(f"\n  {i}. {pos.get('title', 'N/A')}")
            if pos.get("salary"):
                print(f"     薪资：{pos['salary']}")
            if pos.get("location"):
                print(f"     地点：{pos['location']}")
            if pos.get("requirements"):
                print(f"     要求：{'；'.join(pos['requirements'][:3])}")

    if analysis.get("key_highlights"):
        print(f"\n亮点：{'；'.join(analysis['key_highlights'])}")

    if result.get("markdown_filename"):
        from common import file_manager
        md_path = file_manager.ANALYZED_DIR / result["markdown_filename"]
        print(f"\n📄 解析内容：{md_path}")

    print("=" * 60)



def _save_markdown(content: str, raw_filename: str) -> str:
    """保存 Markdown 解析结果到 local_data/analyzed/。"""
    from common import file_manager

    stem = Path(raw_filename).stem
    filename = f"{stem}_parsed.md"
    path = file_manager.ANALYZED_DIR / filename
    path.write_text(content, encoding="utf-8")
    logger.info("Markdown 已保存: %s", path)
    return filename


def _save_analyzed(data: dict, raw_filename: str) -> str:
    """保存 LLM 分析结果到 local_data/analyzed/。"""
    from common import file_manager

    stem = Path(raw_filename).stem
    filename = f"{stem}_analyzed.json"
    file_manager.write_json(data, filename, data_type="analyzed")
    return filename


if __name__ == "__main__":
    main()

