# ai_agent/llm_client.py
"""
LangChain + 阿里云 API 分析引擎。
读取原始 JSON，为每篇文章提取：核心实体、情感倾向、摘要。
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv(Path(__file__).parent.parent / ".env")
logger = logging.getLogger(__name__)

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是专业的新闻分析助手。请分析文章内容，必须以严格的 JSON 格式返回，不要有任何 Markdown 包装。"),
    ("user", """请分析以下文章，提取结构化信息：

标题：{title}
正文：{content}

必须以如下 JSON 格式返回（不得包含任何多余文字）：
{{
  "core_entities": ["实体1", "实体2"],
  "sentiment": "正面|负面|中性",
  "summary": "不超过100字的摘要"
}}"""),
])


def _get_llm() -> ChatOpenAI:
    api_key = os.getenv("ALIBABA_API_KEY") or "none"
    return ChatOpenAI(
        model=os.getenv("AGENT_MODEL", "qwen-plus"),
        api_key=SecretStr(api_key),
        base_url=os.getenv("ALIBABA_API_URL"),
        temperature=float(os.getenv("AGENT_TEMPERATURE", "0.1")),
    )


def analyze_single(article: dict) -> dict:
    """分析单篇文章，返回 analysis 字段。"""
    title = article.get("title", "")
    content = article.get("detail", {}).get("content_text", "")
    if not title and not content:
        return {"core_entities": [], "sentiment": "未知", "summary": ""}

    # 如果没有 API key，返回模拟数据
    api_key = os.getenv("ALIBABA_API_KEY")
    if not api_key or "your_" in api_key:
        import random
        return {
            "core_entities": ["AI", "大模型", "芯片", "技术"][:random.randint(2, 4)],
            "sentiment": random.choice(["正面", "中性", "负面"]),
            "summary": f"这是关于 {title[:10]} 的 AI 自动生成的摘要（模拟数据）。",
            "analyzed_at": datetime.now().isoformat()
        }

    llm = _get_llm()
    parser = JsonOutputParser()
    chain = _PROMPT | llm | parser

    try:
        result = chain.invoke({"title": title, "content": content[:2000]})
        result["analyzed_at"] = datetime.now().isoformat()
        return result
    except Exception as exc:
        logger.error("分析失败 [%s]: %s", title[:20], exc)
        return {"core_entities": [], "sentiment": "未知", "summary": "", "error": str(exc)}


def analyze_articles(articles: list[dict], source: str = "wechat") -> list[dict]:
    """批量分析文章列表，将 analysis 字段合并回每篇文章并返回。"""
    results = []
    total = len(articles)
    for i, article in enumerate(articles):
        logger.info("[%s] 分析进度: %d/%d — %s", source, i + 1, total, article.get("title", "")[:20])
        article_copy = dict(article)
        article_copy["analysis"] = analyze_single(article)
        results.append(article_copy)
    return results