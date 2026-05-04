"""
招聘页面解析合并模块
通过 LLM 智能合并 HTML、视觉提取、OCR 识别结果，生成结构化 Markdown。
"""

import os
import logging
from ai_agent.agent_config import create_llm

logger = logging.getLogger(__name__)

_MERGE_MODEL = "qwen-plus"


async def build_markdown(
    title: str,
    html_text: str,
    vision_text: str,
    ocr_text: str = "",
    url: str = "",
) -> str:
    """
    通过 LLM 智能合并多源内容为结构化 Markdown。

    Args:
        title: 文章标题
        html_text: 页面 <body> HTML
        vision_text: LLM 从截图提取的结构化信息
        ocr_text: OCR 识别出的文字（可选）
        url: 原始 URL

    Returns:
        合并后的 Markdown 格式内容
    """
    api_key = os.getenv("ALIBABA_API_KEY")
    if not api_key or "your_" in api_key:
        return _fallback_merge(title, html_text, vision_text, ocr_text, url)

    llm = create_llm(model=_MERGE_MODEL, temperature=0.1)

    system_prompt = """你是一个招聘数据整理专家。请根据提供的多源信息，去重、整合、补充，生成一份结构化的招聘 Markdown 文档。

输入信息来源：
1. HTML：页面原始 HTML（包含完整结构但文字较少，因为微信文章以图片为主）
2. 视觉提取：LLM 从页面截图识别出的结构化信息（主要数据源）
3. OCR 识别：截图 OCR 识别的纯文字（可能有噪声，仅作参考）

输出要求：
- 以 Markdown 格式输出
- 包含以下章节：
  - 公司名称
  - 招聘岗位（用表格展示：岗位名称、部门、专业要求、学历要求、薪资待遇、工作地点）
  - 招聘条件
  - 福利待遇
  - 投递方式（含链接、二维码说明、截止时间）
  - 其他信息（宣传标语、重要提示等）
- 如果某项信息不存在，填写"未注明"
- 不要编造数据，只使用输入中提供的信息
- 去除重复内容，整合多源信息中的互补部分"""

    ocr_section = f"\n3. OCR 识别文字：\n{ocr_text}" if ocr_text else ""

    user_prompt = f"""请合并以下多源信息，生成结构化的招聘 Markdown 文档：

文章标题：{title}
来源 URL：{url}

1. HTML 内容：
{html_text[:3000]}

2. 视觉提取内容：
{vision_text}
{ocr_section}

请输出完整的 Markdown 文档。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = llm.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        logger.info("LLM 合并完成，字符数: %d", len(content))
        return content
    except Exception as exc:
        logger.error("LLM 合并失败: %s，使用降级方案", exc)
        return _fallback_merge(title, html_text, vision_text, ocr_text, url)


def _fallback_merge(
    title: str,
    html_text: str,
    vision_text: str,
    ocr_text: str,
    url: str,
) -> str:
    """LLM 不可用时的降级方案：简单拼接。"""
    lines = []
    lines.append(f"# {title}")
    lines.append("")
    if url:
        lines.append(f"> 来源：{url}")
        lines.append("")
    lines.append("---")
    lines.append("")

    if vision_text.strip():
        lines.append("## 招聘信息（视觉识别）")
        lines.append("")
        lines.append(vision_text.strip())
        lines.append("")

    if ocr_text.strip():
        lines.append("## 海报文字（OCR 识别）")
        lines.append("")
        lines.append(ocr_text.strip())
        lines.append("")

    return "\n".join(lines)
