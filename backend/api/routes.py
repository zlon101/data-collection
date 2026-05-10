"""
FastAPI 路由：提供给前端调用的 REST 接口。

接口列表：
  GET  /api/files              列举所有数据文件
  GET  /api/data/{filename}    读取指定文件内容
  POST /api/analyze            触发 AI 分析（异步后台任务）
  GET  /api/analyze/status/{filename}  查询分析任务状态
  GET  /api/summary            返回最新 analyzed 文件的数据摘要
  GET  /api/jobs               获取招聘数据（支持筛选）
  POST /api/collector          触发爬虫采集任务
  GET  /api/collector/sse/{task_id}   SSE 实时推送采集日志
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from common.file_manager import (
    analyzed_filename_for,
    list_files,
    parse_salary,
    read_job_data,
    read_json,
    write_json,
)
from common.logger import _subscribers, log, register_queue, unregister_queue

logger = logging.getLogger(__name__)
router = APIRouter()

# 跟踪正在进行的分析任务（filename → status）
_analysis_tasks: dict[str, str] = {}

# 跟踪采集任务（task_id → status dict）
_collector_tasks: dict[str, dict] = {}


# ── 请求/响应模型 ──────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    filename: str
    source: Literal["wechat", "web", "app"] = "wechat"


class CollectorRequest(BaseModel):
    type: Literal["app_uiautomator2", "browser_playwright"]
    params: dict[str, Any]


# ── 已有接口 ──────────────────────────────────────────────
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
    """触发 AI 分析任务（后台异步执行）。"""
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
    """返回最新 analyzed 文件的数据摘要。"""
    from common.file_manager import latest_file

    filename = latest_file(source=source, data_type="analyzed")
    if not filename:
        return {"articles": [], "sentiment_stats": {}, "entities": []}

    data = read_json(filename, data_type="analyzed")
    if not data or not isinstance(data, list):
        return {"articles": [], "sentiment_stats": {}, "entities": []}

    sentiment_count: dict[str, int] = {}
    entity_count: dict[str, int] = {}
    timeline = []

    for article in data:
        analysis = article.get("analysis", {})
        sentiment = analysis.get("sentiment", "未知")
        sentiment_count[sentiment] = sentiment_count.get(sentiment, 0) + 1

        for entity in analysis.get("core_entities", []):
            entity_count[entity] = entity_count.get(entity, 0) + 1

        timeline.append({
            "title": article.get("title", ""),
            "publish_time": article.get("publish_time", ""),
            "publish_date": article.get("detail", {}).get("publish_date", ""),
            "sentiment": sentiment,
            "summary": analysis.get("summary", ""),
        })

    top_entities = sorted(entity_count.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "source_file": filename,
        "total": len(data),
        "sentiment_stats": sentiment_count,
        "top_entities": [{"name": k, "value": v} for k, v in top_entities],
        "timeline": timeline,
    }


# ── 新增接口 ──────────────────────────────────────────────
@router.get("/jobs")
async def get_jobs(
    activity: str = "",
    min_salary: float = 0,
    max_distance: float = 0,
):
    """获取招聘数据，支持活跃度、最低薪资、最大距离过滤。"""
    all_data = read_job_data()

    filtered = all_data
    if activity:
        filtered = [item for item in filtered if activity in item.get("活跃度", "")]

    if min_salary > 0:
        filtered = [
            item for item in filtered
            if (salary := parse_salary(item.get("薪资", ""))) and salary[0] >= min_salary
        ]

    if max_distance > 0:
        filtered = [
            item for item in filtered
            if (dist_str := item.get("距离", "").strip())
            and float(dist_str) <= max_distance
        ]

    return {"total": len(filtered), "items": filtered}


@router.post("/collector")
async def trigger_collector(
    req: CollectorRequest,
    background_tasks: BackgroundTasks,
):
    """触发爬虫采集任务。"""
    task_id = uuid.uuid4().hex[:12]
    _collector_tasks[task_id] = {
        "status": "pending",
        "type": req.type,
        "output": None,
        "error": None,
    }

    if req.type == "app_uiautomator2":
        background_tasks.add_task(_run_app_scraper, task_id, req.params)
    elif req.type == "browser_playwright":
        background_tasks.add_task(_run_browser_scraper, task_id, req.params)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的采集类型: {req.type}")

    return {"status": "accepted", "task_id": task_id}


@router.get("/collector/tasks")
async def list_collector_tasks():
    """列出所有采集任务。"""
    return [{"task_id": k, **v} for k, v in _collector_tasks.items()]


@router.get("/collector/status/{task_id}")
async def get_collector_status(task_id: str):
    """查询采集任务状态。"""
    task = _collector_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    return task


@router.get("/collector/sse/{task_id}")
async def collector_sse(task_id: str):
    """SSE 实时推送采集日志。"""
    queue = register_queue(task_id)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                yield event
                if "event: complete" in event or "event: error" in event:
                    break
        finally:
            unregister_queue(task_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _send_complete(task_id: str) -> None:
    """向 SSE 队列发送完成事件。"""
    payload = json.dumps({"status": "done", "task_id": task_id})
    complete_event = f"event: complete\ndata: {payload}\n\n"
    for q in list(_subscribers.get(task_id, [])):
        q.put_nowait(complete_event)


def _send_error(task_id: str, error: str) -> None:
    """向 SSE 队列发送错误事件。"""
    payload = json.dumps({"error": error})
    error_event = f"event: error\ndata: {payload}\n\n"
    for q in list(_subscribers.get(task_id, [])):
        q.put_nowait(error_event)


# ── 后台任务 ──────────────────────────────────────────────
async def _run_analysis(filename: str, source: str) -> None:
    """后台运行 LangChain 分析。"""
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


async def _run_app_scraper(task_id: str, params: dict) -> None:
    """后台运行 app_uiautomator2 采集器（同步，需在线程池中执行）。"""
    _collector_tasks[task_id]["status"] = "running"
    log("开始执行 app_uiautomator2 采集...", task_id=task_id)

    try:
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            _sync_run_app_scraper,
            task_id,
            params,
        )
        _collector_tasks[task_id]["status"] = "done"
        _collector_tasks[task_id]["output"] = output
        log("采集任务完成", level="INFO", task_id=task_id)
        _send_complete(task_id)
    except Exception as exc:
        _collector_tasks[task_id]["status"] = "error"
        _collector_tasks[task_id]["error"] = str(exc)
        log(f"采集失败: {exc}", level="ERROR", task_id=task_id)
        _send_error(task_id, str(exc))


def _sync_run_app_scraper(task_id: str, params: dict) -> str:
    """同步执行 app_uiautomator2 采集（在线程池中调用）。"""
    from collection_platform.app_uiautomator2.launcher import run_app_scraper

    return run_app_scraper(
        max_items=params.get("max_items", 20),
        is_search=params.get("is_search", True),
        is_new_job_list=params.get("is_new_job_list", False),
        job_keys=params.get("job_keys"),
        black_company=params.get("black_company"),
        money_min=params.get("money_min"),
        max_distance=params.get("max_distance"),
        task_id=task_id,
    )


async def _run_browser_scraper(task_id: str, params: dict) -> None:
    """后台运行 browser_playwright 采集器（本身就是 async）。"""
    _collector_tasks[task_id]["status"] = "running"
    log("开始执行 browser_playwright 采集...", task_id=task_id)

    try:
        from collection_platform.browser_playwright.launcher import run_browser_scraper

        output = await run_browser_scraper(
            url=params["url"],
            fields=params.get("fields", {}),
            container_selector=params.get("container_selector", ""),
            next_button_selector=params.get("next_button_selector"),
            max_pages=params.get("max_pages", 0),
            delay=params.get("delay", 3.0),
            output_filename=params.get("output_filename", "scraped_data.json"),
            task_id=task_id,
        )
        _collector_tasks[task_id]["status"] = "done"
        _collector_tasks[task_id]["output"] = output
        log("采集任务完成", level="INFO", task_id=task_id)
        _send_complete(task_id)
    except Exception as exc:
        _collector_tasks[task_id]["status"] = "error"
        _collector_tasks[task_id]["error"] = str(exc)
        log(f"采集失败: {exc}", level="ERROR", task_id=task_id)
        _send_error(task_id, str(exc))
