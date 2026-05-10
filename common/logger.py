"""
通用日志函数：打印到终端 + 推送 SSE 给已连接的前端客户端。
"""

import asyncio
import json
from datetime import datetime

# task_id → list[asyncio.Queue]，一个任务可有多个 SSE 连接
_subscribers: dict[str, list[asyncio.Queue]] = {}


def _make_entry(message: str, level: str) -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    return f"[{ts}] [{level}] {message}"


def register_queue(task_id: str) -> asyncio.Queue:
    """注册一个队列到指定任务，返回该队列供 SSE 端消费。"""
    q: asyncio.Queue[str] = asyncio.Queue()
    _subscribers.setdefault(task_id, []).append(q)
    return q


def unregister_queue(task_id: str, q: asyncio.Queue) -> None:
    """SSE 断开时清理。"""
    queues = _subscribers.get(task_id, [])
    if q in queues:
        queues.remove(q)
    if not queues:
        _subscribers.pop(task_id, None)


def log(message: str, level: str = "INFO", task_id: str | None = None) -> None:
    """通用日志：打印到终端 + 推送 SSE。

    Args:
        message: 日志内容
        level: 日志级别 (INFO/WARNING/ERROR)
        task_id: 关联的任务 ID，为 None 时不推送 SSE
    """
    entry = _make_entry(message, level)
    # 1. 打印到终端
    print(entry, flush=True)
    # 2. 推送给该 task_id 的所有 SSE 队列
    if task_id and task_id in _subscribers:
        payload = json.dumps({
            "timestamp": entry[:8],
            "level": level,
            "message": message,
        })
        sse_event = f"event: log\ndata: {payload}\n\n"
        for q in list(_subscribers[task_id]):
            q.put_nowait(sse_event)
