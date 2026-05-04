"""
API 响应采集配置
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ApiCollectorConfig:
    """API 响应采集器配置。

    Args:
        url_pattern: 目标 API 的 URL 匹配模式（正则或 glob）。
        json_path: 响应 JSON 中的数据路径，用点号分隔。
            例如: "data.items" → 提取 resp.json()["data"]["items"]
            留空则返回完整响应体。
        next_button_selector: "下一页" 按钮的 CSS 选择器。
        max_pages: 最多采集多少页，0 表示不限制。
        timeout: 单次请求超时时间（毫秒），默认 10 秒。
        next_page_delay: 点击"下一页"后的等待时间（毫秒），默认 500。
        data_format: 数据格式化回调，接收全部采集数据，返回格式化后的列表。
            签名: (list[dict]) -> list[dict]，返回空列表则全部丢弃。
    """

    url_pattern: str
    json_path: str = ""
    next_button_selector: str = ""
    max_pages: int = 0
    timeout: int = 10_000
    next_page_delay: int = 500
    data_format: Callable[[list[dict]], list[dict]] | None = None

    def _extract_json_path(self) -> list[str]:
        """解析 json_path 为键列表。"""
        if not self.json_path:
            return []
        return self.json_path.split(".")
