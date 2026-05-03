#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详情页爬虫 - 使用 UniversalPageParser
"""

import uiautomator2 as u2
import time
from typing import Dict, Any, List, Callable, Optional
from rich.console import Console
from .universal_page_parser import UniversalPageParser
from .exceptions import (
    MultipleElementsError,
    ParseTimeoutError,
    BottomReachedError,
    ScrollFailedError
)

console = Console()


class DetailPageSpider:
    """
    详情页爬虫 - 使用通用页面解析器
    """

    def __init__(
        self,
        device: u2.Device,
        detail_selectors: Dict[str, Dict[str, Any]],
        bottom_indicator_resourceId: str,
        generate_unique_key: Callable[[Dict[str, Any]], str],
        max_scroll_times: int = 5,
        scroll_from: float = 0.7,
        scroll_to: float = 0.3,
        scroll_duration: float = 0.3,
        scroll_wait: float = 0.5,
        click_wait: float = 1.0,
        back_wait: float = 1.0,
        custom_stop: Callable[[Dict[str, Any]], bool] | None = None,
        verbose: bool = False,
    ):
        """
        Args:
            device: uiautomator2 设备
            detail_selectors: 详情页字段选择器
            bottom_indicator_resourceId: 底部标识元素的 resourceId
            max_scroll_times: 最大滚动次数
            scroll_from: 滚动起点Y坐标比例
            scroll_to: 滚动终点Y坐标比例
            scroll_duration: 滚动持续时间
            scroll_wait: 滚动后等待时间
            click_wait: 点击后等待时间
            back_wait: 返回后等待时间
            custom_stop: 自定义终止判断
            verbose: 是否输出详细日志
        """
        self.device = device
        self.click_wait = click_wait
        self.generate_unique_key = generate_unique_key
        self.back_wait = back_wait

        # 创建通用解析器
        self.parser = UniversalPageParser(
            device=device,
            selectors=detail_selectors,
            bottom_indicator_resourceId=bottom_indicator_resourceId,
            max_scroll_times=max_scroll_times,
            scroll_from=scroll_from,
            scroll_to=scroll_to,
            scroll_duration=scroll_duration,
            scroll_wait=scroll_wait,
            custom_stop=custom_stop,
            verbose=verbose
        )

    def parse_and_return(self) -> Dict[str, str]:
        """
        解析当前详情页并返回列表页。
        供新版 ListPageSpider 使用：点击由 ListPageSpider 负责，
        本方法只负责解析详情页内容并按下返回键。
        Returns:
            详情页解析结果字典

        Raises:
            MultipleElementsError: 字段匹配到多个元素
            ParseTimeoutError: 解析超时
            BottomReachedError: 到达底部但必填字段未找全
            ScrollFailedError: 返回列表页失败
        """

        try:
            detail_data = self.parser.parse()
            detail_data["unique_key"] = self.generate_unique_key(detail_data)
            self._go_back()
            return detail_data

        except (MultipleElementsError, ParseTimeoutError, BottomReachedError) as e:
            console.print(f"[red]⚠️ 详情页解析失败: {e}[/red]")
            try:
                self._go_back()
            except:
                pass
            raise

        except Exception as e:
            console.print(f"[red]⚠️ 详情页异常: {e}[/red]")
            try:
                self._go_back()
            except:
                pass
            raise ScrollFailedError(f"详情页处理异常: {e}")

    def _go_back(self):
        """
        返回列表页
        
        Raises:
            ScrollFailedError: 返回失败
        """
        try:
            self.device.press("back")
            time.sleep(self.back_wait)
        except Exception as e:
            raise ScrollFailedError(f"返回列表页失败: {e}")
