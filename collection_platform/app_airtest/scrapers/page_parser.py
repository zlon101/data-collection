# scrapers/page_parser.py
"""将 OCR TextBlock 列表解析为结构化文章数据。"""

import re
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

from .ocr_engine import TextBlock

logger = logging.getLogger(__name__)

# 时间标记正则
_TIME_PATTERNS = [
    r"\d+\s*分钟前", r"\d+\s*小时前", r"\d+\s*天前",
    r"昨天", r"前天",
    r"\d{4}[-年]\d{1,2}[-月]\d{1,2}",
]
_TIME_RE = re.compile("|".join(_TIME_PATTERNS))

# 日期正则（详情页精确日期）
_DATE_RE = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{2}-\d{2}")

# 阅读量正则
_READ_RE = re.compile(r"阅读[：:\s]*(\d+)|(\d+)\s*次阅读|(\d+)\s*阅读")

# 微信详情页底部标识符
_ARTICLE_BOTTOM_KEYWORDS = {"写留言", "在看", "分享", "喜欢作者"}


@dataclass
class ArticleItem:
    index: int
    title: str = ""
    account_name: str = ""
    publish_time: str = ""
    click_x: int = 0
    click_y: int = 0
    status: str = "pending"
    error_msg: str = ""
    detail: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def is_time_marker(block: TextBlock, screen_width: int) -> bool:
    """判断一个文字块是否为时间标记。"""
    return bool(_TIME_RE.search(block.text)) and block.x > screen_width * 0.5


def parse_list_page(
    blocks: list[TextBlock],
    screen_width: int,
    content_start_y: int,
    existing_titles: set[str],
) -> list[ArticleItem]:
    """
    将列表页 OCR 结果解析为 ArticleItem 列表。

    Args:
        blocks: OCR 文字块（已按 y 排序）。
        screen_width: 屏幕宽度（像素）。
        content_start_y: 有效内容区域的起始 y（过滤头部 UI）。
        existing_titles: 已采集的标题集合（去重用）。

    Returns:
        新发现的文章列表。
    """
    # 过滤头部 UI
    valid = [b for b in blocks if b.y >= content_start_y]

    # 找出时间标记，作为卡片分隔锚点
    time_markers = [b for b in valid if is_time_marker(b, screen_width)]
    if not time_markers:
        return []

    articles = []
    for i, tm in enumerate(time_markers):
        card_y_start = time_markers[i - 1].y if i > 0 else content_start_y
        card_y_end = time_markers[i + 1].y if i < len(time_markers) - 1 else float("inf")

        # 该卡片范围内的所有文字块
        card_blocks = [b for b in valid if card_y_start <= b.y <= card_y_end]

        # 字号最大 = 标题
        non_time = [b for b in card_blocks if not is_time_marker(b, screen_width)]
        if not non_time:
            continue
        title_block = max(non_time, key=lambda b: b.height)
        title = title_block.text.strip()

        if not title or title in existing_titles:
            continue

        # 账号名：在 title_block 下方 80px 内、字号较小、靠左的文字
        account_candidates = [
            b for b in non_time
            if b != title_block
            and abs(b.y - title_block.y) < 80
            and b.x < screen_width * 0.5
            and b.height < title_block.height
        ]
        account_name = account_candidates[0].text.strip() if account_candidates else ""

        articles.append(ArticleItem(
            index=0,  # 由调用方重新编号
            title=title,
            account_name=account_name,
            publish_time=tm.text.strip(),
            click_x=title_block.x,
            click_y=title_block.y,
        ))

    return articles


def parse_detail_page(all_blocks: list[TextBlock], first_screen_blocks: list[TextBlock]) -> dict:
    """
    从详情页多屏 OCR 结果中提取结构化字段。

    Args:
        all_blocks: 所有屏拼接的去重后文字块。
        first_screen_blocks: 仅第一屏的文字块（用于提取元数据）。

    Returns:
        detail 字典。
    """
    from datetime import datetime

    if not all_blocks:
        return {}

    # 首屏字号最大的文字 = 标题
    title_block = max(first_screen_blocks, key=lambda b: b.height) if first_screen_blocks else None
    title = title_block.text if title_block else ""

    # 从首屏提取元数据
    publish_date = ""
    read_count = ""
    author = ""

    for b in first_screen_blocks:
        if not publish_date:
            m = _DATE_RE.search(b.text)
            if m:
                publish_date = m.group()
        if not read_count:
            m = _READ_RE.search(b.text)
            if m:
                read_count = m.group(1) or m.group(2) or m.group(3) or ""

    # 账号名（标题块下方 100px 内，字号最大的非时间/日期文字）
    if title_block:
        below_title = [
            b for b in first_screen_blocks
            if b.y > title_block.y and b.y < title_block.y + 100
            and not _DATE_RE.search(b.text)
        ]
        if below_title:
            author = min(below_title, key=lambda b: b.y).text

    # 正文 = 排除元数据字段后的全部文字，按 y 顺序拼接
    meta_texts = {title, publish_date, read_count, author}
    content_blocks = [
        b for b in all_blocks
        if b.text not in meta_texts and not _ARTICLE_BOTTOM_KEYWORDS.intersection(b.text.split())
    ]
    content_text = "\n".join(b.text for b in content_blocks)

    return {
        "title": title,
        "author": author,
        "publish_date": publish_date,
        "read_count": read_count,
        "content_text": content_text,
        "collected_at": datetime.now().isoformat(),
    }


def is_article_bottom(blocks: list[TextBlock]) -> bool:
    """检测当前屏是否包含微信文章底部元素（用于停止滚动）。"""
    texts = {b.text for b in blocks}
    return bool(texts & _ARTICLE_BOTTOM_KEYWORDS)