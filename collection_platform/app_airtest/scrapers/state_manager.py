# scrapers/state_manager.py
"""状态文件管理：读取/写入/断点续传。"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # data-collection/
LOCAL_DATA_RAW = _PROJECT_ROOT / "local_data" / "raw"
LOCAL_DATA_RAW.mkdir(parents=True, exist_ok=True)


def make_filename(account_name: str) -> str:
    today = datetime.now().strftime("%Y%m%d")
    return f"wechat_{account_name}_{today}.json"


def load_state(filename: str) -> dict:
    path = LOCAL_DATA_RAW / filename
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            logger.info("加载已有状态: %s (%d 篇)", filename, len(data.get("articles", [])))
            return data
        except Exception:
            pass
    return {"filename": filename, "list_collected": False, "articles": []}


def save_state(state: dict) -> None:
    path = LOCAL_DATA_RAW / state["filename"]
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def pending_articles(state: dict) -> list[dict]:
    return [a for a in state["articles"] if a.get("status") == "pending"]


def mark_detail_done(state: dict, index: int, detail: dict) -> None:
    for a in state["articles"]:
        if a["index"] == index:
            a["detail"] = detail
            a["status"] = "detail_collected"
            break
    save_state(state)


def mark_error(state: dict, index: int, error: str) -> None:
    for a in state["articles"]:
        if a["index"] == index:
            a["status"] = "error"
            a["error_msg"] = error
            break
    save_state(state)