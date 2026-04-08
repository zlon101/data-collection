# backend/api/routes.py
"""
FastAPI 路由：提供给前端调用的 REST 接口。

接口列表：
  GET  /api/files              列举所有数据文件
  GET  /api/data/{filename}    读取指定文件内容
  POST /api/analyze            触发 AI 分析（异步后台任务）
  GET  /api/analyze/status/{filename}  查询分析任务状态
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from common.file_manager import (
    analyzed_filename_for,
    list_files,
    read_json,
    write_json,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# 跟踪正在进行的分析任务（filename → status）
_analysis_tasks: dict[str, str] = {}


# ── 请求/响应模型 ──────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    filename: str                    # raw 文件名，如 "wechat_国资小新_20260403.json"
    source: Literal["wechat", "web", "app"] = "wechat"


# ── 接口实现 ──────────────────────────────────────────────
@router.get("/files")
async def get_files(
    source: str = "",
    data_type: Literal["raw", "analyzed", "all"] = "all",
):
    """列举数据文件，支持按 source 和 data_type 过滤。"""
    if data_type == "all":
        raw = list_files(source=source, data_type="raw")
        analyzed = list_files(source=source, data_type="analyzed")
        return {"raw": raw, "analyzed": analyzed}
    return list_files(source=source, data_type=data_type)


@router.get("/data/{filename}")
async def get_data(
    filename: str,
    data_type: Literal["raw", "analyzed"] = "analyzed",
):
    """读取指定 JSON 文件内容。"""
    data = read_json(filename, data_type=data_type)
    if data is None:
        raise HTTPException(status_code=404, detail=f"文件不存在或解析失败: {filename}")
    return {"filename": filename, "data_type": data_type, "data": data}


@router.post("/analyze")
async def trigger_analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    触发 AI 分析任务（后台异步执行）。
    立即返回任务接受状态，分析在后台进行。
    """
    if req.filename in _analysis_tasks and _analysis_tasks[req.filename] == "running":
        return {"status": "already_running", "filename": req.filename}

    _analysis_tasks[req.filename] = "running"
    background_tasks.add_task(_run_analysis, req.filename, req.source)
    return {"status": "accepted", "filename": req.filename}


@router.get("/analyze/status/{filename}")
async def get_analyze_status(filename: str):
    """查询分析任务状态。"""
    status = _analysis_tasks.get(filename, "not_started")
    analyzed_fn = analyzed_filename_for(filename)
    analyzed_files = list_files(data_type="analyzed")
    is_done = any(f["filename"] == analyzed_fn for f in analyzed_files)
    return {
        "filename": filename,
        "status": "done" if is_done else status,
        "analyzed_filename": analyzed_fn if is_done else None,
    }


@router.get("/summary")
async def get_summary(source: str = "wechat"):
    """
    返回最新 analyzed 文件的数据摘要，供前端图表使用。
    包含：情感分布统计、核心实体频次、文章时间线。
    """
    from common.file_manager import latest_file

    filename = latest_file(source=source, data_type="analyzed")
    if not filename:
        return {"articles": [], "sentiment_stats": {}, "entities": []}

    data = read_json(filename, data_type="analyzed")
    if not data or not isinstance(data, list):
        return {"articles": [], "sentiment_stats": {}, "entities": []}

    # 情感分布统计
    sentiment_count: dict[str, int] = {}
    entity_count: dict[str, int] = {}
    timeline = []

    for article in data:
        analysis = article.get("analysis", {})

        # 情感
        sentiment = analysis.get("sentiment", "未知")
        sentiment_count[sentiment] = sentiment_count.get(sentiment, 0) + 1

        # 实体
        for entity in analysis.get("core_entities", []):
            entity_count[entity] = entity_count.get(entity, 0) + 1

        # 时间线
        timeline.append({
            "title": article.get("title", ""),
            "publish_time": article.get("publish_time", ""),
            "publish_date": article.get("detail", {}).get("publish_date", ""),
            "sentiment": sentiment,
            "summary": analysis.get("summary", ""),
        })

    # 实体频次排序，取前20
    top_entities = sorted(entity_count.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "source_file": filename,
        "total": len(data),
        "sentiment_stats": sentiment_count,
        "top_entities": [{"name": k, "value": v} for k, v in top_entities],
        "timeline": timeline,
    }


# ── 后台任务 ──────────────────────────────────────────────
async def _run_analysis(filename: str, source: str) -> None:
    """
    后台运行 LangChain 分析，将结果写入 analyzed 目录。
    在独立线程中执行以避免阻塞事件循环。
    """
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_analyze, filename, source)
        _analysis_tasks[filename] = "done"
        logger.info("分析完成: %s", filename)
    except Exception as exc:
        _analysis_tasks[filename] = f"error: {exc}"
        logger.error("分析失败 %s: %s", filename, exc)


def _sync_analyze(filename: str, source: str) -> None:
    """同步执行分析（在线程池中调用）。"""
    from ai_agent.llm_client import analyze_articles

    raw_data = read_json(filename, data_type="raw")
    if not raw_data or not isinstance(raw_data, list):
        raise ValueError(f"无法读取原始数据或格式不正确: {filename}")

    analyzed = analyze_articles(raw_data, source=source)
    out_filename = analyzed_filename_for(filename)
    write_json(analyzed, out_filename, data_type="analyzed")
