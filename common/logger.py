"""
通用日志函数：打印到终端 + 追加写入日志文件。
"""

from contextvars import ContextVar
from datetime import datetime

_log_file: ContextVar[str | None] = ContextVar("log_file", default=None)


def set_log_file(path: str) -> None:
    """设置当前任务的日志文件路径。"""
    _log_file.set(path)


def _make_entry(message: str, level: str) -> str:
    ts = datetime.now().strftime("%H:%M:%S")
    return f"[{ts}] [{level}] {message}"


def log(message: str, level: str = "INFO", task_id: str | None = None) -> None:
    """通用日志：打印到终端 + 追加写入日志文件（如果已设置）。"""
    entry = _make_entry(message, level)
    # 1. 打印到终端
    print(entry, flush=True)
    # 2. 追加写入日志文件
    path = _log_file.get()
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
