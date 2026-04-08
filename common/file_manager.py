# common/file_manager.py
"""
JSON 文件的读写、列举、归档等工具。
所有路径均相对于项目根目录的 local_data/ 计算。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# local_data 根目录（此文件在 common/，上二级为项目根）
_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
LOCAL_DATA = _PROJECT_ROOT / "local_data"
RAW_DIR = LOCAL_DATA / "raw"
ANALYZED_DIR = LOCAL_DATA / "analyzed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
ANALYZED_DIR.mkdir(parents=True, exist_ok=True)


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
    """将数据序列化并写入指定文件，返回完整路径。"""
    base_dir = RAW_DIR if data_type == "raw" else ANALYZED_DIR
    path = base_dir / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("数据已写入: %s", path)
    return path


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
