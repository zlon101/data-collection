"""
API 响应采集器

通过监听网络响应 + 点击分页按钮，
将分页表格的 API 响应数据收集到同一个数组中。
"""

import json
import re
from typing import Optional
from playwright.async_api import Page, Response

from .config import ApiCollectorConfig


class ApiCollector:
    """采集指定 API 接口的分页响应数据。

    流程：
        1. 启动监听，等待用户手动操作触发 API 请求（如打开弹窗）
        2. 捕获首次 API 响应后，自动点击下一页继续采集
        3. 达到 max_pages 或没有下一页时停止

    使用方式:
        config = ApiCollectorConfig(
            url_pattern=r".*/api/articles.*",
            json_path="data.items",
            next_button_selector=".next-btn",
            max_pages=5,
        )
        collector = ApiCollector(page, config)
        all_data = await collector.collect_all_pages()
    """

    def __init__(self, page: Page, config: ApiCollectorConfig):
        self._page = page
        self._config = config
        self._all_data: list[dict] = []
        self._responses: list[dict] = []

    @property
    def all_data(self) -> list[dict]:
        """采集到的数据列表（已扁平化到同一数组）。"""
        return self._all_data

    @property
    def responses(self) -> list[dict]:
        """所有 API 原始响应体列表（含分页元信息）。"""
        return self._responses

    # ── 公共方法 ────────────────────────────────────────────

    async def collect_all_pages(self) -> list[dict]:
        """采集所有分页数据（受 max_pages 限制）。

        流程：
            1. 等待用户手动操作，捕获首次 API 响应（不刷新页面）
            2. 自动点击下一页，捕获后续页数据
        """
        # 第一步：等待用户操作触发首次 API 响应
        print("⏳ 等待用户手动操作（如打开弹窗、触发列表加载）...")
        first_collected = await self._wait_first_response()

        if not first_collected:
            print("❌ 超时未捕获到目标 API 响应")
            return self._all_data

        # 第二步：自动点击下一页
        page_count = 1
        while await self._has_next_page():
            if self._config.max_pages and page_count >= self._config.max_pages:
                print(f"📊 已达页数上限 ({self._config.max_pages} 页)")
                break
            await self._click_next_and_collect()
            page_count += 1

        return self._all_data

    def get_stats(self) -> dict:
        """返回采集统计信息。"""
        return {
            "total_items": len(self._all_data),
            "total_pages": len(self._responses),
        }

    def save_to_json(self, filepath: str):
        """保存采集数据到 JSON 文件。"""
        data = self._all_data
        if self._config.data_format:
            data = self._config.data_format(data)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 已保存 {len(data)} 条数据到 {filepath}")

    # ── 内部方法 ────────────────────────────────────────────

    def _match_response(self, response: Response) -> bool:
        """判断响应是否来自目标 API。"""
        return bool(re.search(self._config.url_pattern, response.url))

    def _extract_data(self, resp_json: dict) -> list:
        """从响应 JSON 中按 json_path 提取数据列表。"""
        path_keys = self._config._extract_json_path()
        if not path_keys:
            return [resp_json] if resp_json else []

        current = resp_json
        for key in path_keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return []

        return current if isinstance(current, list) else [current] if current else []

    async def _wait_first_response(self) -> bool:
        """等待用户操作触发目标 API 响应。不刷新页面。"""
        try:
            async with self._page.expect_response(
                self._match_response, timeout=60_000  # 等待用户操作，给 60 秒
            ) as response_info:
                pass
            response = await response_info.value
            await self._process_response(response)
            return True
        except Exception:
            return False

    async def _has_next_page(self) -> bool:
        """判断是否还有下一页。"""
        selector = self._config.next_button_selector
        if not selector:
            return False
        try:
            locator = self._page.locator(selector)
            return await locator.count() > 0 and await locator.is_visible()
        except Exception:
            return False

    async def _click_next_and_collect(self):
        """点击下一页并捕获 API 响应。"""
        async with self._page.expect_response(
            self._match_response, timeout=self._config.timeout
        ) as response_info:
            await self._page.locator(self._config.next_button_selector).click()
            if self._config.next_page_delay > 0:
                await self._page.wait_for_timeout(self._config.next_page_delay)
            await self._page.wait_for_load_state("networkidle")

        try:
            response = await response_info.value
            await self._process_response(response)
        except Exception as e:
            print(f"⚠️ 等待下一页响应超时: {e}")

    async def _process_response(self, response: Response):
        """处理单个 API 响应，提取数据并追加到数组。"""
        try:
            resp_json = await response.json()
        except Exception:
            print(f"⚠️ 响应无法解析为 JSON: {response.url}")
            return

        data = self._extract_data(resp_json)
        self._responses.append(resp_json)
        self._all_data.extend(data)
        print(f"✅ 采集到 {len(data)} 条，累计 {len(self._all_data)} 条")
