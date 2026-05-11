#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列表页面爬虫 (流式处理版)
支持 "边抓边点" 模式，在抓取列表项时直接处理详情页
"""

import uiautomator2 as u2
import time
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from common.file_manager import write_json_path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


@dataclass
class ListPageSpiderParam:
    """
    列表页爬虫的配置参数对象
    device: uiautomator2 设备对象
    item_selector: 列表项的 resourceId
    container_selector: 列表容器的 resourceId
    selectors: 字段选择器映射
    max_items: 最大数据条数
    scroll_sleep: 滚动后等待时间（秒）
    max_empty_scrolls: 连续多少次无新数据时停止
    click_wait: 点击列表项后等待详情页加载的时间（秒）
    generate_unique_key: 生成唯一key
    item_processing_callback: 单项处理回调函数（用于解析详情页并返回）
                            点击由 ListPageSpider 内部完成，回调只负责解析和返回
                            返回: 详情页数据字典
    is_cancelled: 取消检查回调，返回 True 表示需要停止
    """

    # 必填参数 (无默认值)
    device: u2.Device
    container_selector: str
    item_selector: str
    selectors: dict[str, str | dict[str, Any]]
    generate_unique_key: Callable[[dict[str, str]], str]

    # 选填参数 (带默认值)
    max_items: int = 10
    scroll_sleep: float = 1.0
    max_empty_scrolls: int = 8
    click_wait: float = 1.0
    item_processing_callback: Callable[[], dict[str, Any]] | None = None
    item_filter: Callable[[dict[str, str]], bool] | None = None
    format_data: Callable[[list[dict[str, str]]], None] | None = None
    is_cancelled: Callable[[], bool] | None = None


class ListPageSpider:
    """
    列表页面爬虫

    功能：
    - 基于容器解析方案
    - 支持流式处理（列表+详情同步抓取）
    - 自动滚动翻页、智能去重、智能停止
    """

    def __init__(self, config: ListPageSpiderParam):
        self.config = config
        self.data_list: list[dict[str, Any]] = []
        self.seen_items: set[str] = set()

    def crawl(self) -> list[dict[str, Any]]:
        """开始抓取列表数据"""
        console.print(
            f"\n[cyan]开始流式抓取，目标: {self.config.max_items} 条[/cyan]\n"
        )

        empty_scroll_count = 0
        scroll_count = 0
        self.cancelled = False

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:

                task = progress.add_task(
                    f"[cyan]抓取中... (0/{self.config.max_items})",
                    total=self.config.max_items,
                )

                while len(self.data_list) < self.config.max_items:
                    if self.config.is_cancelled and self.config.is_cancelled():
                        self.cancelled = True
                        console.print("\n[yellow]⚠ 用户停止采集[/yellow]")
                        break

                    scroll_count += 1

                    # 解析当前页面（包含详情页交互逻辑）
                    new_items_count = self._parse_current_page_stream()

                    if new_items_count > 0:
                        empty_scroll_count = 0
                        current_count = len(self.data_list)

                        progress.update(
                            task,
                            completed=min(current_count, self.config.max_items),
                            description=f"[cyan]抓取中... ({current_count}/{self.config.max_items})",
                        )

                        console.print(
                            f"[green]第 {scroll_count} 次滚动: 新增 {new_items_count} 条，"
                            f"累计 {current_count} 条[/green]"
                        )

                        if current_count >= self.config.max_items:
                            break
                    else:
                        empty_scroll_count += 1
                        console.print(
                            f"[yellow]第 {scroll_count} 次滚动: 无新数据 "
                            f"({empty_scroll_count}/{self.config.max_empty_scrolls})[/yellow]"
                        )

                        if empty_scroll_count >= self.config.max_empty_scrolls:
                            console.print("\n[yellow]⚠ 已到达列表底部[/yellow]")
                            break

                    self._scroll_page()

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ 用户中断抓取[/yellow]")

        console.print(f"\n[green]✓ 抓取完成: 共 {len(self.data_list)} 条[/green]")
        return self.data_list

    def _parse_current_page_stream(self) -> int:
        """
        解析当前页面，分两个阶段处理：
        - 阶段一（快照）：批量收集列表数据，零跳转。
        - 阶段二（导航）：逐项重新定位容器，点击进入详情，调用回调解析后返回。
        Returns: 本页新增的数据条数
        """
        new_items_count = 0

        # ── 阶段一：解析列表项，零跳转 ──────────────────────────────────
        pending_items = self._snapshot_current_page()
        if not pending_items:
            return 0

        # ── 阶段二：点击列表项，解析详情页 ──────────────────────
        item = None
        detail_data = None
        pending_item_keys = [u["unique_item_key"] for u in pending_items]

        while len(self.data_list) < self.config.max_items:
            containers = self.config.device(resourceId=self.config.item_selector)
            for matched_container in containers:
                if len(self.data_list) >= self.config.max_items:
                    break

                if not self._is_element_fully_visible_in_container(matched_container):
                    continue

                if self.config.item_processing_callback:
                    now_container_field, has_valid_data = self._parse_container_item(matched_container)
                    now_item_key = now_container_field["unique_item_key"]
                    first_attr_value = now_container_field.get(next(iter(now_container_field)))
                    if now_item_key not in pending_item_keys or now_item_key in self.seen_items:
                        continue

                    # 点击进入详情页
                    console.print(f"\n🔥 点击 {now_item_key}  {first_attr_value}")
                    self._click_container(matched_container)

                    # 解析详情页数据，回调只负责解析详情页并返回列表页
                    try:
                        detail_data = self.config.item_processing_callback()
                    except Exception as e:
                        self.save_to_json()
                        raise e
                    else:
                        # 详情页数据不满足筛选条件
                        if detail_data.get("stop_reason"):
                            self.seen_items.add(now_item_key)
                            break
                        item = next((u for u in pending_items if u["unique_item_key"] == detail_data["unique_key"]), None)
                        if item is not None:
                            item.update(detail_data)
                            self.data_list.append(item)
                            self.seen_items.add(item["unique_item_key"])
                            new_items_count += 1
                        else:
                            # 跳过当前列表item
                            self.seen_items.add(now_item_key)
                            console.print(f"[red]{detail_data['unique_key']} 没有匹配的列表项[/red]")
                        break
            else:
                break
        return new_items_count

    def _snapshot_current_page(self) -> list[dict[str, Any]]:
        """
        阶段一：纯快照，零跳转。
        遍历当前屏所有可见容器，收集列表字段数据，返回待处理项列表。
        整个过程不做任何页面跳转，最大程度避免 race condition。
        """
        pending_items: list[dict[str, Any]] = []
        containers = self.config.device(resourceId=self.config.item_selector)
        container_count = containers.count
        has_visible_item = False
        for i in range(container_count):
            if len(self.data_list) + len(pending_items) >= self.config.max_items:
                break
            try:
                container = containers[i]
                # 跳过不完整的元素
                if not self._is_element_fully_visible_in_container(container):
                    continue
                has_visible_item = True
                # 读取所有字段
                item, has_valid_data = self._parse_container_item(container)
                if not has_valid_data or (
                    self.config.item_filter and not self.config.item_filter(item)
                ):
                    continue

                # 排除已入库的和本轮快照中已收集的
                item_key_val = item["unique_item_key"]
                already_pending_keys = {p["unique_item_key"] for p in pending_items}
                if item_key_val and item_key_val not in self.seen_items and item_key_val not in already_pending_keys:
                    pending_items.append(item)
            except Exception as e:
                console.print(f"[dim]快照容器 {i} 跳过: {e}[/dim]")
                continue

        if not has_visible_item:
            raise ValueError("容器定位错误，请检查配置项")
        return pending_items

    def _parse_container_item(self, container_item: u2.UiObject) -> tuple[dict[str, str], bool]:
        field_value: dict[str, Any] = {}
        has_valid_data = False
        for field_name, selector_config in self.config.selectors.items():
            try:
                resource_id = selector_config if isinstance(selector_config, str) else selector_config.get("value", "")
                element = container_item.child(resourceId=resource_id)
                if element.exists:
                    field_value[field_name] = element.get_text().strip()
                    has_valid_data = True
                else:
                    field_value[field_name] = ""
            except Exception:
                field_value[field_name] = ""

        if has_valid_data:
            item_key_val = self.config.generate_unique_key(field_value)
            field_value["unique_item_key"] = item_key_val

        return field_value, has_valid_data

    def _click_container(self, container) -> None:
        """
        点击容器中心点，并等待详情页加载。
        """
        bounds = container.info.get('bounds', {})
        if bounds:
            center_x = (bounds['left'] + bounds['right']) // 2
            center_y = (bounds['top'] + bounds['bottom']) // 2
            self.config.device.click(center_x, center_y)
        else:
            container.click()
        time.sleep(self.config.click_wait)

    def _scroll_page(self) -> None:
        try:
            screen_width, screen_height = self.config.device.window_size()
            x = int(screen_width / 2)

            # 修改策略：从 80% 位置滑到 40% 位置
            # 移动距离 = 40% 屏幕高度
            # 这样每次滚动保留了一半的旧数据在屏幕上方，确保底部那个"半残"的 C
            # 在下一次循环时会出现在屏幕中间，被完整解析。
            start_y = int(screen_height * 0.8)
            end_y = int(screen_height * 0.35)

            self.config.device.swipe(
                x, start_y, x, end_y, duration=0.5
            )  # duration 稍慢一点更稳
            time.sleep(self.config.scroll_sleep)
        except Exception as e:
            console.print(f"[red]滚动失败: {e}[/red]")
            pass

    def _is_element_fully_visible_in_container(self, element: u2.UiObject) -> bool:
        """
        判断子元素是否完全显示在其父容器（如列表）内部，没有被滚动切断
        
        :param element: 待判断的列表项元素对象 (Item)
        :return: bool 完全包含返回 True，部分遮挡或不存在返回 False
        """
        list_container = self.config.device(resourceId=self.config.container_selector)
        try:
            if not element.exists or not list_container.exists:
                return False

            # 获取容器的边界
            c_bounds = list_container.info['bounds']
            c_top = c_bounds['top']
            c_bottom = c_bounds['bottom']

            # 获取元素的边界
            e_bounds = element.info['bounds']
            e_top = e_bounds['top']
            e_bottom = e_bounds['bottom']

            # 核心判断：元素的 top 不能超出容器的 top，元素的 bottom 不能超出容器的 bottom
            # (加 2 像素的容错率，防止 UI 渲染时的像素级误差)
            if e_top > c_top and e_top >= (c_top - 2) and e_bottom <= (c_bottom + 2) and e_bottom < c_bottom:
                return True
            return False

        except Exception:
            return False

    def save_to_json(self, filename: str | None = None) -> None:
        if not self.data_list or len(self.data_list) == 0:
            console.print(f"[green]数据为空，不保存 {filename}[/green]")
            return
        if not filename:
            filename = f"test_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if self.config.format_data:
            self.config.format_data(self.data_list)

        path = Path(filename)
        write_json_path(self.data_list, path)
        console.print(f"[green]已保存到 {path}[/green]")
