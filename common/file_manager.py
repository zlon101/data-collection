# common/file_manager.py
"""
统一文件 I/O 入口。
所有文件读写必须通过本模块，禁止直接使用 open() / Path.read_text() / Path.write_text()。
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from common.path_utils import get_project_root

logger = logging.getLogger(__name__)

# local_data 根目录（可通过 LOCAL_DATA_DIR 环境变量配置，默认: 项目根目录下的 local_data/）
_PROJECT_ROOT = get_project_root()
_local_data_env = os.getenv("LOCAL_DATA_DIR")
if _local_data_env:
    LOCAL_DATA = Path(_local_data_env) if Path(_local_data_env).is_absolute() else _PROJECT_ROOT / _local_data_env
else:
    LOCAL_DATA = _PROJECT_ROOT / "local_data"
RAW_DIR = LOCAL_DATA / "raw"
ANALYZED_DIR = LOCAL_DATA / "analyzed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
ANALYZED_DIR.mkdir(parents=True, exist_ok=True)

# ── Job 目录 ──
JOB_DIR = LOCAL_DATA / "job"
JOB_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_dir(path: Path) -> None:
    """确保文件所在目录存在，不存在则创建。"""
    path.parent.mkdir(parents=True, exist_ok=True)


# ── JSON 读写 ──────────────────────────────────────────────

def list_files(source: str = "", data_type: str = "raw") -> list[dict]:
    """
    列举 raw 或 analyzed 目录下的数据文件。

    Args:
        source: 来源前缀过滤，如 "wechat"、"web"，空字符串返回全部。
        data_type: "raw" 或 "analyzed"。

    Returns:
        文件元信息列表，每项含 filename / source / date / size_kb。
    """
    base_dir = RAW_DIR if data_type == "raw" else ANALYZED_DIR
    files = []
    for f in sorted(base_dir.glob("*.json"), reverse=True):
        if source and not f.name.startswith(source):
            continue
        stat = f.stat()
        # 文件名格式约定：{source}_{账号}_{YYYYMMDD}.json
        parts = f.stem.split("_")
        files.append({
            "filename": f.name,
            "source": parts[0] if parts else "unknown",
            "account": parts[1] if len(parts) > 1 else "",
            "date": parts[-1] if len(parts) > 1 else "",
            "size_kb": round(stat.st_size / 1024, 1),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "data_type": data_type,
        })
    return files


def read_json(filename: str, data_type: str = "raw") -> list | dict | None:
    """读取指定文件内容，文件不存在或解析失败返回 None。"""
    base_dir = RAW_DIR if data_type == "raw" else ANALYZED_DIR
    path = base_dir / filename
    if not path.exists():
        logger.warning("文件不存在: %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("JSON 解析失败 %s: %s", filename, exc)
        return None


def write_json(data: Any, filename: str, data_type: str = "raw") -> Path:
    """将数据序列化并写入指定文件，自动创建父目录。返回完整路径。"""
    base_dir = RAW_DIR if data_type == "raw" else ANALYZED_DIR
    path = base_dir / filename
    _ensure_dir(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("数据已写入: %s", path)
    return path


def write_json_path(data: Any, path: Path) -> Path:
    """将数据写入任意路径的 JSON 文件，自动创建父目录。返回完整路径。"""
    _ensure_dir(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("数据已写入: %s", path)
    return path


def read_json_path(path: Path) -> list | dict | None:
    """从任意路径读取 JSON，文件不存在或解析失败返回 None。"""
    if not path.exists():
        logger.warning("文件不存在: %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("JSON 解析失败 %s: %s", path, exc)
        return None


def list_json_files(directory: Path) -> list[Path]:
    """列出目录下所有 .json 文件。"""
    if not directory.exists():
        logger.warning("目录不存在: %s", directory)
        return []
    return sorted(directory.glob("*.json"))


# ── 文本读写 ──────────────────────────────────────────────


def read_text(path: Path, encoding: str = "utf-8") -> str | None:
    """读取文本文件，文件不存在返回 None。"""
    if not path.exists():
        logger.warning("文件不存在: %s", path)
        return None
    return path.read_text(encoding=encoding)


def write_text(content: str, path: Path, encoding: str = "utf-8") -> Path:
    """写入文本文件，自动创建父目录。返回完整路径。"""
    _ensure_dir(path)
    path.write_text(content, encoding=encoding)
    logger.info("文本已写入: %s", path)
    return path


# ── 二进制读写 ─────────────────────────────────────────────


def read_bytes(path: Path) -> bytes | None:
    """读取二进制文件，文件不存在返回 None。"""
    if not path.exists():
        logger.warning("文件不存在: %s", path)
        return None
    return path.read_bytes()


def write_bytes(data: bytes, path: Path) -> Path:
    """写入二进制文件，自动创建父目录。返回完整路径。"""
    _ensure_dir(path)
    path.write_bytes(data)
    logger.info("二进制数据已写入: %s", path)
    return path


# ── 工具方法 ──────────────────────────────────────────────

def latest_file(source: str, data_type: str = "raw") -> str | None:
    """返回指定来源最新文件的文件名，不存在返回 None。"""
    files = list_files(source=source, data_type=data_type)
    return files[0]["filename"] if files else None


def analyzed_filename_for(raw_filename: str) -> str:
    """
    根据原始文件名推导对应的 analyzed 文件名。
    例：wechat_国资小新_20260403.json → wechat_国资小新_20260403_done.json
    """
    stem = Path(raw_filename).stem
    return f"{stem}_done.json"


# ── Job 目录操作 ──────────────────────────────────────────

def list_job_files() -> list[dict]:
    """列举 job 目录下的所有 JSON 文件元信息。"""
    files = []
    for f in sorted(JOB_DIR.glob("*.json"), reverse=True):
        stat = f.stat()
        files.append({
            "filename": f.name,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return files


def read_job_data() -> list[dict]:
    """读取 job 目录下所有 JSON 文件，按 unique_key 合并去重后返回。"""
    all_data: list[dict] = []
    for f in JOB_DIR.glob("*.json"):
        data = read_json_path(f)
        if data and isinstance(data, list):
            all_data.extend(data)

    seen: set[str] = set()
    deduplicated: list[dict] = []
    for item in all_data:
        key = item.get("unique_key")
        if key and key not in seen:
            deduplicated.append(item)
            seen.add(key)
    return deduplicated


def parse_salary(salary_str: str) -> tuple[float, float] | None:
    """解析薪资字符串，如 '1.5-2.0万' → (15.0, 20.0)（千元/月）。

    支持格式:
      - '1.5-2.0万' → (15.0, 20.0)
      - '15-20K' → (15.0, 20.0)
      - '8-12k' → (8.0, 12.0)
      - '8000-12000元' → (8.0, 12.0)
    """
    if not salary_str:
        return None

    numbers = re.findall(r"[\d.]+", salary_str)
    if len(numbers) < 2:
        return None

    low = float(numbers[0])
    high = float(numbers[1])

    lower = salary_str.lower()
    if "万" in salary_str:
        return (low * 10, high * 10)
    elif "k" in lower:
        return (low, high)
    elif "元" in lower:
        return (low / 1000, high / 1000)

    return (low, high)
