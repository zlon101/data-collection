#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用页面解析器 - 自动分屏策略
"""

import uiautomator2 as u2
import time
import re
from typing import Dict, Optional, List, Any, Callable
from rich.console import Console
from rich.table import Table
from .exceptions import (
    MultipleElementsError,
    ParseTimeoutError,
    BottomReachedError,
    ScrollFailedError
)

console = Console()


class UniversalPageParser:
    """
    通用页面解析器
    
    特性：
    1. 自动滚动查找未解析字段
    2. 智能检测页面底部
    3. 多元素匹配时报错
    4. 第一次找到即保存
    """
    
    def __init__(
        self,
        device: u2.Device,
        selectors: Dict[str, Dict[str, Any]],
        bottom_indicator_resourceId: str,
        max_scroll_times: int = 10,
        scroll_from: float = 0.7,
        scroll_to: float = 0.3,
        scroll_duration: float = 0.3,
        scroll_wait: float = 0.5,
        custom_stop: Optional[Callable[[Dict[str, Any]], bool]] = None,
        verbose: bool = False
    ):
        """
        Args:
            device: uiautomator2 设备
            selectors: 字段选择器配置
                格式: {
                    "字段名": {
                        "resourceId": "xxx",  # 必填
                        "textPattern": "regex",  # 可选
                        "optional": True/False,  # 可选，默认 False
                    }
                }
            bottom_indicator_resourceId: 底部标识元素的 resourceId
            max_scroll_times: 最大滚动次数，默认10次
            scroll_from: 滚动起点Y坐标比例，默认0.7
            scroll_to: 滚动终点Y坐标比例，默认0.3
            scroll_duration: 滚动持续时间，默认0.3秒
            scroll_wait: 滚动后等待时间，默认0.5秒
            verbose: 是否输出详细日志
        """
        self.device = device
        self.selectors = selectors
        self.bottom_indicator_resourceId = bottom_indicator_resourceId
        self.max_scroll_times = max_scroll_times
        self.scroll_from = scroll_from
        self.scroll_to = scroll_to
        self.scroll_duration = scroll_duration
        self.scroll_wait = scroll_wait
        self.custom_stop = custom_stop
        self.verbose = verbose
        
        # 内部状态
        self.parsed_data: Dict[str, str] = {}
        self.pending_fields: List[str] = []
        self.scroll_count: int = 0
    
    def parse(self) -> Dict[str, str]:
        """
        执行解析
        
        Returns:
            字段数据字典 {"字段名": "字段值"}
            
        Raises:
            MultipleElementsError: 字段匹配到多个元素
            ParseTimeoutError: 达到最大滚动次数仍有字段未解析
            BottomReachedError: 检测到底部但必填字段未找全
            ScrollFailedError: 滚动操作失败
        """
        # 1. 初始化
        self._initialize()
        
        # 2. 主循环
        while True:
            # 2.1 遍历待解析字段
            self._parse_pending_fields()
            
            # 自定义终止判断
            if self.custom_stop and self.custom_stop(self.parsed_data):
                # console.print(f"\n详情页 {self.parsed_data.get('公司')} 提前终止")
                self.parsed_data["stop_reason"] = "数据不符合用户要求"
                return self.parsed_data
            
            # 2.2 检查终止条件 1: 所有字段都找到了？
            if not self.pending_fields:
                if self.verbose:
                    self._log_completion()
                return self.parsed_data
            
            # 2.3 检查终止条件 2: 检测到底部标识？
            if self._check_bottom_indicator():
                return self._handle_bottom_reached()
            
            # 2.4 检查终止条件 3: 达到最大滚动次数？
            if self.scroll_count >= self.max_scroll_times:
                self._raise_parse_timeout_error()
            
            # 2.5 执行滚动
            self._scroll_down()
    
    def _initialize(self):
        """初始化解析状态"""
        self.parsed_data = {}
        self.pending_fields = list(self.selectors.keys())
        self.scroll_count = 0
        
        if self.verbose:
            required_count = sum(
                1 for config in self.selectors.values() 
                if not config.get("optional", False)
            )
            optional_count = len(self.selectors) - required_count
            
            required_fields = [
                name for name, config in self.selectors.items()
                if not config.get("optional", False)
            ]
            optional_fields = [
                name for name, config in self.selectors.items()
                if config.get("optional", False)
            ]
            
            
    def _parse_pending_fields(self):
        """遍历并解析待解析字段"""
        screen_label = f"第 {self.scroll_count + 1} 屏"
        
        if self.verbose and self.pending_fields:
            console.print(f"[cyan][{screen_label}][/cyan]\n")
        
        for field_name in self.pending_fields[:]:  # 拷贝列表，因为会动态删除
            config = self.selectors[field_name]
            
            if self.verbose:
                console.print(f"[cyan]🔍 查找字段: {field_name}[/cyan]")
                console.print(f"  └─ resourceId: {config['resourceId']}")
                if "textPattern" in config:
                    console.print(f"  └─ textPattern: {config['textPattern']}")
            
            # 查找元素
            element = self._find_element_by_config(field_name, config)
            
            if element and element.exists:
                # 找到元素，获取文本
                text = element.get_text() or ""
                self.parsed_data[field_name] = text.strip()
                self.pending_fields.remove(field_name)
                
                if self.verbose:
                    display_text = text.strip() if text.strip() else "(空)"
                    if len(display_text) > 50:
                        display_text = display_text[:47] + "..."
                    console.print(f"  └─ 文本内容: {display_text}")
                    console.print(f"[green]✅ 字段 '{field_name}' 解析成功[/green]\n")
            else:
                # 未找到元素
                self.parsed_data[field_name] = ""
                if self.verbose:
                    console.print(f"  └─ 未找到匹配元素")
                    console.print(f"[yellow]⏩ 字段 '{field_name}' 暂未找到，继续滚动[/yellow]\n")
    
    def _find_element_by_config(
        self,
        field_name: str,
        config: Dict[str, Any]
    ) -> Optional[u2.UiObject]:
        """
        根据配置查找单个字段的元素
        
        Returns:
            单个元素或 None
            
        Raises:
            MultipleElementsError: 匹配到多个元素
        """
        resource_id = config["resourceId"]
        
        # 1. 根据 resourceId 查找所有匹配元素
        elements = self.device(resourceId=resource_id)
        count = elements.count
        
        if self.verbose:
            console.print(f"  └─ 找到 {count} 个元素")
        
        if count == 0:
            return None
        
        text_pattern = config.get("textPattern")
        
        if not text_pattern:
            # 多个元素
            if count > 1:
                # 将 UiObject 转换为 List[UiObject]
                elements_list = [elements[i] for i in range(count)]
                self._raise_multiple_elements_error(field_name, elements_list, config)
            else:
                return elements[0]
            
        # 配置了 textPattern，进行过滤
        filtered = self._filter_by_text_pattern(elements, text_pattern)
            
        if self.verbose:
            console.print(f"  └─ 找到 {count} 个元素，使用正则过滤")
            console.print(f"  └─ 过滤后: {len(filtered)} 个元素")
        
        if len(filtered) == 0:
            return None
        
        if len(filtered) == 1:
            return filtered[0]
        
        # 过滤后仍有多个元素，报错
        self._raise_multiple_elements_error(
            field_name, 
            filtered, 
            config,
            filtered=True
        )
    
    def _filter_by_text_pattern(
        self,
        elements: u2.UiObject,
        pattern: str
    ) -> List[u2.UiObject]:
        """
        使用正则表达式过滤元素
        
        Args:
            elements: 元素集合
            pattern: 正则表达式字符串
            
        Returns:
            过滤后的元素列表
        """
        filtered = []
        
        for i in range(elements.count):
            element = elements[i]
            text = element.get_text() or ""
            
            # 使用 re.search 进行包含匹配
            if re.search(pattern, text):
                filtered.append(element)
        
        return filtered
    
    def _check_bottom_indicator(self) -> bool:
        """
        检测是否到达底部
        
        Returns:
            True/False
        """
        if not self.bottom_indicator_resourceId:
            return False
        
        element = self.device(resourceId=self.bottom_indicator_resourceId)
        
        if element.exists:
            if self.verbose:
                console.print("\n" + "━" * 60 + "\n")
                console.print("[yellow]⚠️ 检测到底部标识[/yellow]")
                console.print(f"  └─ resourceId: {self.bottom_indicator_resourceId}\n")
            return True
        
        return False
    
    def _handle_bottom_reached(self) -> Dict[str, str]:
        """
        处理检测到底部标识的情况
        
        Returns:
            解析数据（可能是部分结果）
            
        Raises:
            BottomReachedError: 必填字段未找全
        """
        # 检查是否还有必填字段未找到
        required_pending = [
            name for name in self.pending_fields
            if not self.selectors[name].get("optional", False)
        ]
        
        optional_pending = [
            name for name in self.pending_fields
            if self.selectors[name].get("optional", False)
        ]
        
        if required_pending:
            # 有必填字段未找到，报错
            self._raise_bottom_reached_error(required_pending, optional_pending)
        else:
            # 只剩可选字段，返回部分结果
            if self.verbose:
                if optional_pending:
                    console.print(f"[yellow]⚠️ 可选字段未找到 ({len(optional_pending)}个): {', '.join(optional_pending)}[/yellow]\n")
                console.print("━" * 60 + "\n")
                self._log_completion()
            
            return self.parsed_data
    
    def _scroll_down(self):
        """
        执行滚动操作
        
        Raises:
            ScrollFailedError: 滚动失败
        """
        if self.verbose:
            console.print("\n" + "━" * 60 + "\n")
            remaining = self.max_scroll_times - self.scroll_count - 1
            console.print(f"[cyan]↓ 滚动到下一屏 (第 {self.scroll_count + 1} 次，剩余可滚动次数: {remaining})[/cyan]\n")
            console.print("━" * 60 + "\n")
        
        try:
            self.device.swipe(
                0.5, self.scroll_from, 
                0.5, self.scroll_to, 
                duration=self.scroll_duration
            )
            time.sleep(self.scroll_wait)
            self.scroll_count += 1
        except Exception as e:
            raise ScrollFailedError(f"滚动操作失败: {e}")
    
    def _raise_multiple_elements_error(
        self,
        field_name: str,
        elements: List[u2.UiObject],
        config: Dict[str, Any],
        filtered: bool = False
    ):
        """
        抛出多元素匹配错误
        
        Args:
            field_name: 字段名
            elements: 匹配到的多个元素列表（或 UiObject）
            config: 字段配置
            filtered: 是否是过滤后的结果
        """
        console.print(f"\n[red]❌ 字段 '{field_name}' 匹配到多个元素 (共 {len(elements)} 个)[/red]\n")
        
        # 创建表格
        table = Table(title="匹配的元素详情")
        table.add_column("索引", style="cyan", width=6)
        table.add_column("文本内容", style="yellow")
        table.add_column("坐标 (bounds)", style="green")
        
        for idx, elem in enumerate(elements):
            text = elem.get_text() or "(空)"
            bounds = elem.info.get("bounds", {})
            bounds_str = f"[{bounds.get('left', 0)},{bounds.get('top', 0)}]"
            bounds_str += f"[{bounds.get('right', 0)},{bounds.get('bottom', 0)}]"
            
            table.add_row(str(idx), text, bounds_str)
        
        console.print(table)
        
        # 给出解决建议
        console.print("\n[yellow]💡 解决方案:[/yellow]")
        if not filtered:
            console.print("  添加 textPattern 过滤，例如:")
            console.print(f"    \"textPattern\": r\"\\d+\\.?\\d*\\s*(km|m)\"")
        else:
            console.print("  优化 textPattern 正则表达式，使其更精确")
        
        console.print(f"\n当前配置: {config}\n")
        
        raise MultipleElementsError(
            f"字段 '{field_name}' 匹配到 {len(elements)} 个元素，请添加或优化 textPattern 过滤"
        )
    
    def _raise_parse_timeout_error(self):
        """抛出解析超时错误"""
        console.print(f"\n[red]❌ 解析超时[/red]\n")
        console.print(f"滚动次数: {self.scroll_count} (已达上限)")
        console.print(f"底部标识配置: resourceId={self.bottom_indicator_resourceId}")
        console.print(f"检测结果: 未检测到底部标识元素\n")
        
        # 未找到的字段
        console.print(f"未找到的字段 ({len(self.pending_fields)}个):")
        for field_name in self.pending_fields:
            config = self.selectors[field_name]
            console.print(f"  - {field_name}:")
            console.print(f"      resourceId: {config['resourceId']}")
            if "textPattern" in config:
                console.print(f"      textPattern: {config['textPattern']}")
            console.print(f"      optional: {config.get('optional', False)}")
            console.print()
        
        # 建议
        console.print("[yellow]💡 可能原因:[/yellow]")
        console.print("  1. 底部标识配置错误（检查 resourceId 是否正确）")
        console.print("  2. 页面过长（增大 max_scroll_times）")
        console.print("  3. 字段配置错误（检查上述字段的 resourceId 和 textPattern）\n")
        
        console.print("[yellow]💡 建议:[/yellow]")
        console.print(f"  1. 增加 max_scroll_times (当前为 {self.max_scroll_times})")
        console.print("  2. 使用 verbose=True 查看详细日志")
        console.print("  3. 手动验证底部标识元素是否存在\n")
        
        raise ParseTimeoutError(
            f"滚动{self.scroll_count}次后，未检测到底部标识，"
            f"可能底部标识配置错误。未找到字段: {self.pending_fields}"
        )
    
    def _raise_bottom_reached_error(
        self,
        required_pending: List[str],
        optional_pending: List[str]
    ):
        """抛出到达底部但字段未找全错误"""
        console.print(f"\n[red]❌ 已到达页面底部，但必填字段未找全[/red]\n")
        console.print(f"底部标识: 已检测到 (resourceId={self.bottom_indicator_resourceId})\n")
        
        # 已找到的字段
        if self.parsed_data:
            console.print(f"已找到的字段 ({len(self.parsed_data)}个):")
            for name, value in self.parsed_data.items():
                display_value = value if len(value) <= 30 else value[:27] + "..."
                console.print(f"  ✅ {name}: {display_value}")
            console.print()
        
        # 未找到的必填字段
        console.print(f"未找到的必填字段 ({len(required_pending)}个):")
        for field_name in required_pending:
            config = self.selectors[field_name]
            console.print(f"  ❌ {field_name}:")
            console.print(f"      resourceId: {config['resourceId']}")
            if "textPattern" in config:
                console.print(f"      textPattern: {config['textPattern']}")
            console.print(f"      optional: False")
            console.print()
        
        # 未找到的可选字段
        if optional_pending:
            console.print(f"未找到的可选字段 ({len(optional_pending)}个):")
            for field_name in optional_pending:
                config = self.selectors[field_name]
                console.print(f"  ⚠️ {field_name}:")
                console.print(f"      resourceId: {config['resourceId']}")
                if "textPattern" in config:
                    console.print(f"      textPattern: {config['textPattern']}")
                console.print(f"      optional: True")
                console.print()
        
        # 建议
        console.print("[yellow]💡 可能原因:[/yellow]")
        console.print("  1. 必填字段的 resourceId 配置错误")
        console.print("  2. 页面确实没有该字段内容")
        console.print("  3. textPattern 过滤条件过于严格\n")
        
        console.print("[yellow]💡 建议:[/yellow]")
        console.print("  1. 检查字段配置是否正确")
        console.print("  2. 使用 verbose=True 查看详细解析过程")
        console.print("  3. 考虑将字段改为 optional=True（如果该字段不是必需的）\n")
        
        raise BottomReachedError(
            f"到达底部但必填字段未找全: {required_pending}"
        )
    
    def _log_completion(self):
        """输出解析完成日志"""
        required_count = sum(
            1 for name, config in self.selectors.items()
            if not config.get("optional", False)
        )
        optional_count = len(self.selectors) - required_count
        
        found_required = sum(
            1 for name in self.parsed_data.keys()
            if not self.selectors[name].get("optional", False)
        )
        found_optional = len(self.parsed_data) - found_required
        
        console.print("[green]✅ 所有字段解析完成[/green]")
        console.print(f"  成功字段: {len(self.parsed_data)}/{len(self.selectors)}")
        console.print(f"  必填字段: {found_required}/{required_count} ✅")
        console.print(f"  可选字段: {found_optional}/{optional_count} {'✅' if found_optional == optional_count else '⚠️'}")
        console.print(f"  滚动次数: {self.scroll_count}\n")
