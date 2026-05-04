"""
LLM 操作模块
负责视觉提取和投递判断。
复用 ai_agent.agent_config 中的 create_llm 方法。
"""

import os
import json
import base64
import logging
import re
import io
from pathlib import Path
from datetime import datetime
from PIL import Image

from ai_agent.agent_config import create_llm

logger = logging.getLogger(__name__)

VISION_MODEL = os.getenv("RECRUIT_VISION_MODEL", "qwen-vl-max")


async def extract_from_vision(
    screenshot_path: str,
    html_text: str = "",
) -> str:
    """
    用多模态 LLM 从截图提取招聘信息。

    Args:
        screenshot_path: 截图路径
        html_text: HTML 提取的正文（辅助上下文）

    Returns:
        LLM 提取的结构化文本（Markdown 格式）
    """
    api_key = os.getenv("ALIBABA_API_KEY")
    if not api_key or "your_" in api_key:
        return ""

    llm = create_llm(model=VISION_MODEL, temperature=0.3)
    image_data_url = _encode_image_to_base64(screenshot_path)

    system_prompt = """你是一个专业的招聘数据分析助手。请仔细分析截图中的所有内容，提取所有招聘信息。

请按以下格式输出（纯文本 Markdown）：

## 公司/组织
公司名称全称

## 招聘岗位
按表格格式列出所有岗位：

| 岗位名称 | 部门 | 招聘人数 | 专业要求 | 学历要求 | 薪资待遇 | 工作地点 |
|---------|------|---------|---------|---------|---------|---------|
| ... | ... | ... | ... | ... | ... | ... |

## 招聘条件
- 通用要求列表
- 特殊要求说明

## 福利待遇
- 各项福利列表

## 投递方式
- 邮箱/链接/二维码说明
- 截止时间

## 其他信息
- 宣传标语
- 重要提示

注意：
1. 只提取截图中实际存在的信息，不要编造
2. 如果某项信息在截图中不存在，填写"未注明"
3. 保持原始数据的准确性，特别是数字、日期、邮箱等"""

    user_text = f"请分析以下微信招聘文章截图。\n\nHTML 提取的文字（辅助参考）：\n{html_text[:2000] if html_text else '无'}"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_url},
                },
            ],
        },
    ]

    try:
        response = llm.invoke(messages)
        content = response.content
        if not isinstance(content, str):
            content = str(content)
        logger.info("视觉提取完成，字符数: %d", len(content))
        return content
    except Exception as exc:
        logger.error("视觉提取失败: %s", exc)
        return ""


async def analyze_recruit_llm(markdown_content: str) -> dict:
    """
    对招聘 Markdown 内容进行 LLM 投递判断分析。

    Args:
        markdown_content: 合并后的 Markdown 格式内容

    Returns:
        结构化分析结果
    """
    api_key = os.getenv("ALIBABA_API_KEY")
    if not api_key or "your_" in api_key:
        return {
            "error": "未配置 ALIBABA_API_KEY",
            "should_apply": None,
        }

    llm = create_llm(model=VISION_MODEL, temperature=0.3)

    system_prompt = """你是一个专业的招聘顾问助手。请分析招聘文章内容，判断是否应该投递简历。

你必须以严格的 JSON 格式返回，不要有任何 Markdown 包装或多余文字。

返回格式:
{
  "company": "公司名称",
  "positions": [
    {
      "title": "岗位名称",
      "requirements": ["要求1", "要求2"],
      "responsibilities": ["职责1"],
      "salary": "薪资范围（如有）",
      "location": "工作地点（如有）"
    }
  ],
  "application_method": "投递方式（邮箱/链接/二维码说明）",
  "deadline": "截止日期（如有）",
  "should_apply": true,
  "apply_reason": "简要说明为什么建议或不建议投递（2-3句话）",
  "key_highlights": ["亮点1", "亮点2"]
}"""

    user_prompt = f"""请分析以下招聘文章：

{markdown_content}

请综合文章内容，给出完整的分析结果。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        response = llm.invoke(messages)
        content = response.content
        if not isinstance(content, str):
            content = str(content)
        result = _parse_llm_json_response(content)
        result["analyzed_at"] = datetime.now().isoformat()
        return result
    except Exception as exc:
        logger.error("LLM 分析失败: %s", exc)
        return {
            "error": str(exc),
            "should_apply": None,
        }


def _encode_image_to_base64(image_path: str, max_width: int = 1200) -> str:
    """将图片文件编码为 base64 data URL。"""
    img = Image.open(image_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        logger.info("图片已压缩: %dx%d → %dx%d", img.width, img.height, max_width, new_height)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def _parse_llm_json_response(content: str) -> dict:
    """解析 LLM 返回的 JSON 响应，处理 Markdown 代码块。"""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法解析 LLM 响应为 JSON: {content[:500]}")

