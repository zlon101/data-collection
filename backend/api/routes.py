"""
FastAPI 路由：提供给前端调用的 REST 接口。

接口列表：
  GET  /api/files              列举所有数据文件
  GET  /api/data/{filename}    读取指定文件内容
  POST /api/analyze            触发 AI 分析（异步后台任务）
  GET  /api/analyze/status/{filename}  查询分析任务状态
  GET  /api/summary            返回最新 analyzed 文件的数据摘要
  GET  /api/jobs               获取招聘数据（支持筛选）
  GET  /api/job/files          列出 local_data/job/ 中的文件
  DELETE /api/job/files/{filename}     删除 job 文件
  POST /api/job/merge          合并 job 目录所有文件
  POST /api/collector          触发爬虫采集任务
  GET  /api/collector/logs/{task_id}  读取采集任务日志
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from common.file_manager import (
    analyzed_filename_for,
    list_files,
    list_json_files,
    parse_salary,
    read_job_data,
    read_json,
    read_json_path,
    write_json,
    write_json_path,
)
from common.path_utils import get_project_root
from common.logger import log, set_log_file

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

    return {"total": len(filtered), "items": filtered}


# ── Job 文件管理 ─────────────────────────────────────────
_job_dir = get_project_root() / "local_data" / "job"


@router.get("/job/files")
async def list_job_files():
    """列出 local_data/job/ 中的所有 .json 文件。"""
    if not _job_dir.exists():
        return {"files": []}

    files = []
    for f in sorted(_job_dir.iterdir()):
        if f.suffix == ".json" and f.is_file():
            stat = f.stat()
            files.append({
                "filename": f.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })

    return {"files": files}


@router.get("/job/files/{filename}")
async def get_job_file_content(filename: str):
    """读取 local_data/job/ 中指定文件的内容。"""
    file_path = _job_dir / filename
    if not file_path.resolve().is_relative_to(_job_dir.resolve()):
        raise HTTPException(status_code=400, detail="非法文件名")
    data = read_json_path(file_path)
    if data is None or not isinstance(data, list):
        raise HTTPException(status_code=404, detail=f"文件不存在或格式错误: {filename}")
    return {"filename": filename, "total": len(data), "items": data}


@router.delete("/job/files/{filename}")
async def delete_job_file(filename: str):
    """删除 local_data/job/ 中的指定文件。"""
    file_path = _job_dir / filename
    # 安全检查：防止路径遍历
    if not file_path.resolve().is_relative_to(_job_dir.resolve()):
        raise HTTPException(status_code=400, detail="非法文件名")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    file_path.unlink()
    return {"message": f"文件已删除: {filename}"}


@router.post("/job/merge")
async def merge_job_files():
    """合并 local_data/job/ 中的所有文件并去重。"""
    if not _job_dir.exists():
        raise HTTPException(status_code=404, detail="job 目录不存在")

    try:
        from collection_platform.app_uiautomator2.tools.merge_job_data import (
            merge_and_deduplicate_data,
            output_path,
        )
        merge_and_deduplicate_data()
        return {
            "message": "合并完成",
            "output_file": str(output_path.name),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合并失败: {e}")


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


@router.post("/collector/{task_id}/cancel")
async def cancel_collector(task_id: str):
    """取消正在运行的采集任务。"""
    task = _collector_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    if task["status"] not in ("running", "pending"):
        raise HTTPException(status_code=400, detail=f"任务已结束，状态: {task['status']}")

    task["status"] = "cancelling"
    return {"status": "cancelling", "message": "已发送停止信号"}


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


@router.get("/collector/logs/{task_id}")
async def get_collector_logs(task_id: str):
    """读取采集任务日志。"""
    log_dir = get_project_root() / "backend" / "log"
    if not log_dir.exists():
        return ""
    log_files = list(log_dir.glob(f"*_{task_id}.log"))
    if not log_files:
        return ""
    return log_files[0].read_text(encoding="utf-8")


@router.post("/collector/config")
async def save_collector_config(config_name: str, req: dict[str, Any]):
    """保存爬虫配置到 backend/database/crawler/。"""
    config_dir = get_project_root() / "backend" / "database" / "crawler"
    config_dir.mkdir(parents=True, exist_ok=True)
    path = write_json_path(req, config_dir / f"config_{config_name}.json")
    return {"path": str(path)}


@router.get("/collector/configs")
async def list_collector_configs():
    """列出所有已保存的爬虫配置。"""
    config_dir = get_project_root() / "backend" / "database" / "crawler"
    if not config_dir.exists():
        return {"configs": []}

    files = list_json_files(config_dir)
    # 从 config_xxx.json 提取配置名 xxx
    names = []
    for f in files:
        if f.name.startswith("config_") and f.name.endswith(".json"):
            names.append(f.name[len("config_") : -len(".json")])
    return {"configs": names}


@router.get("/collector/config/{config_name}")
async def get_collector_config(config_name: str):
    """加载指定配置。"""
    config_dir = get_project_root() / "backend" / "database" / "crawler"
    path = config_dir / f"config_{config_name}.json"
    data = read_json_path(path)
    if data is None:
        raise HTTPException(status_code=404, detail=f"配置不存在: {config_name}")
    return {"name": config_name, "params": data}


@router.delete("/collector/config/{config_name}")
async def delete_collector_config(config_name: str):
    """删除指定配置。"""
    config_dir = get_project_root() / "backend" / "database" / "crawler"
    path = config_dir / f"config_{config_name}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"配置不存在: {config_name}")
    path.unlink()
    return {"message": f"配置已删除: {config_name}"}


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

    def is_cancelled() -> bool:
        return _collector_tasks.get(task_id, {}).get("status") == "cancelling"

    date_str = datetime.now().strftime("%Y-%m-%d")
    app_type = params.get("app_type", "boss")
    log_dir = get_project_root() / "backend" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{date_str}_{app_type}_{task_id}.log"
    set_log_file(str(log_file))

    log("开始执行 app_uiautomator2 采集...", task_id=task_id)

    try:
        loop = asyncio.get_event_loop()
        was_cancelled = await loop.run_in_executor(
            None,
            lambda: _sync_run_app_scraper(task_id, params, is_cancelled),
        )
        if was_cancelled:
            _collector_tasks[task_id]["status"] = "cancelled"
            _collector_tasks[task_id]["error"] = "用户主动取消"
            log("采集任务已取消", level="INFO", task_id=task_id)
        else:
            _collector_tasks[task_id]["status"] = "done"
            _collector_tasks[task_id]["output"] = "采集完成"
            log("采集任务完成", level="INFO", task_id=task_id)
    except Exception as exc:
        _collector_tasks[task_id]["status"] = "error"
        _collector_tasks[task_id]["error"] = str(exc)
        log(f"采集失败: {exc}", level="ERROR", task_id=task_id)


def _sync_run_app_scraper(task_id: str, params: dict, is_cancelled) -> bool:
    """同步执行 app_uiautomator2 采集（在线程池中调用）。"""
    from collection_platform.app_uiautomator2.launcher import run_app_scraper

    return run_app_scraper(
        app_type=params.get("app_type", "boss"),
        max_items=params.get("max_items", 20),
        is_search=params.get("is_search", True),
        is_new_job_list=params.get("is_new_job_list", False),
        job_keys=params.get("job_keys"),
        black_company=params.get("black_company"),
        money_min=params.get("money_min"),
        max_distance=params.get("max_distance"),
        task_id=task_id,
        is_cancelled=is_cancelled,
    )


async def _run_browser_scraper(task_id: str, params: dict) -> None:
    """后台运行 browser_playwright 采集器（本身就是 async）。"""
    _collector_tasks[task_id]["status"] = "running"

    def is_cancelled() -> bool:
        return _collector_tasks.get(task_id, {}).get("status") == "cancelling"

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_dir = get_project_root() / "backend" / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{date_str}_browser_playwright_{task_id}.log"
    set_log_file(str(log_file))

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
            is_cancelled=is_cancelled,
            detail_fields=params.get("detail_fields"),
            detail_container_selector=params.get("detail_container_selector"),
            detail_url_field=params.get("detail_url_field"),
            detail_url_attribute=params.get("detail_url_attribute", "href"),
            navigation_mode=params.get("navigation_mode", "go_back"),
            back_wait_time=params.get("back_wait_time", 2.0),
            detail_page_wait_time=params.get("detail_page_wait_time", 2.0),
            max_detail_retries=params.get("max_detail_retries", 2),
            continue_on_error=params.get("continue_on_error", True),
        )
        if output is None and is_cancelled():
            _collector_tasks[task_id]["status"] = "cancelled"
            _collector_tasks[task_id]["error"] = "用户主动取消"
            log("采集任务已取消", level="INFO", task_id=task_id)
        elif output is None:
            _collector_tasks[task_id]["status"] = "done"
            _collector_tasks[task_id]["output"] = "未抓取到数据"
            log("采集完成（无数据）", level="INFO", task_id=task_id)
        else:
            _collector_tasks[task_id]["status"] = "done"
            _collector_tasks[task_id]["output"] = output
            log("采集任务完成", level="INFO", task_id=task_id)
    except Exception as exc:
        _collector_tasks[task_id]["status"] = "error"
        _collector_tasks[task_id]["error"] = str(exc)
        log(f"采集失败: {exc}", level="ERROR", task_id=task_id)
