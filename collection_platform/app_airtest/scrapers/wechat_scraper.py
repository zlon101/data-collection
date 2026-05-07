# scrapers/wechat_scraper.py
"""
微信公众号列表 + 详情页数据采集主流程。

运行方式（从项目根目录执行）：
    uv run --directory collection_platform/app_airtest python3 -m scrapers.wechat_scraper --account 国资小新 --max 20

流程：
  1. 手动在手机上打开微信「常看」列表页，按 Enter 触发
  2. 列表采集：多屏 OCR → 解析文章条目
  3. 详情采集：逐条点击 → 多屏 OCR → 解析详情 → 返回
  4. 结果写入 local_data/raw/wechat_{account}_{date}.json
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

from scrapers._path_utils import get_project_root
from config.devices import ADB_PATH
from scrapers.ocr_engine import recognize
from scrapers.page_navigator import (
    go_back,
    init_device,
    scroll_down,
    take_snapshot,
    tap,
    wait,
)
from scrapers.page_parser import (
    ArticleItem,
    is_article_bottom,
    parse_detail_page,
    parse_list_page,
)
from scrapers.state_manager import (
    load_state,
    make_filename,
    mark_detail_done,
    mark_error,
    pending_articles,
    save_state,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("wechat_scraper")

# ── 屏幕参数（根据实际设备截图调整） ──────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 2800
CONTENT_START_Y = 350   # "常看"页有效内容区起始 y（过滤标题栏+账号头像行）


def collect_list(state: dict, account_name: str, max_articles: int) -> None:
    """阶段一：列表页多屏 OCR 采集文章条目。"""
    existing_titles = {a["title"] for a in state["articles"]}
    stable_count = 0   # 连续无新内容帧数