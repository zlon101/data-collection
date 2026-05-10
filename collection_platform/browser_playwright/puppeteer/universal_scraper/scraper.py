"""
通用网页数据抓取器
支持自定义字段、分页抓取、灵活配置
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from playwright.async_api import Page

from common.file_manager import write_json_path


@dataclass
class FieldConfig:
    """字段配置"""
    name: str  # 字段名
    selector: str  # CSS选择器
    attribute: Optional[str] = None  # 提取属性（默认提取text）
    multiple: bool = False  # 是否提取多个值


@dataclass
class ScraperConfig:
    """抓取器配置"""
    url: str  # 目标网址
    fields: List[FieldConfig]  # 字段配置列表
    container_selector: str  # 容器选择器（每个数据项的容器）
    next_button_selector: Optional[str] = None  # 下一页按钮选择器
    page_range: Optional[tuple] = None  # 页码范围 (start, end)
    delay: float = 3.0  # 页面延迟时间（秒）
    max_pages: int = 0  # 最大页数（0表示无限制）


class UniversalScraper:
    """通用网页数据抓取器"""
    
    def __init__(self, page: Page, config: ScraperConfig):
        """
        初始化抓取器
        
        Args:
            page: Playwright页面对象
            config: 抓取器配置
        """
        self.page = page
        self.config = config
        self.all_data: List[Dict[str, Any]] = []
    
    async def scrape_current_page(self) -> List[Dict[str, Any]]:
        """
        抓取当前页面数据
        
        Returns:
            当前页的数据列表
        """
        page_data = []
        
        # 等待容器加载
        try:
            await self.page.wait_for_selector(
                self.config.container_selector,
                timeout=10000
            )
        except Exception as e:
            print(f"⚠️ 容器未找到: {self.config.container_selector}")
            return page_data
        
        # 获取所有容器
        containers = await self.page.locator(self.config.container_selector).all()
        print(f"   找到 {len(containers)} 个数据项")
        
        # 遍历每个容器
        for container in containers:
            item_data = {}
            
            # 提取每个字段
            for field in self.config.fields:
                try:
                    value = await self._extract_field(container, field)
                    item_data[field.name] = value
                except Exception as e:
                    print(f"   ⚠️ 提取字段失败 [{field.name}]: {e}")
                    item_data[field.name] = None
            
            page_data.append(item_data)
        
        return page_data
    
    async def _extract_field(self, container, field: FieldConfig) -> Any:
        """
        提取单个字段的值
        
        Args:
            container: 容器元素
            field: 字段配置
            
        Returns:
            字段值
        """
        locator = container.locator(field.selector)
        
        # 检查元素是否存在
        count = await locator.count()
        if count == 0:
            return None
        
        # 提取多个值
        if field.multiple:
            elements = await locator.all()
            values = []
            for elem in elements:
                if field.attribute:
                    val = await elem.get_attribute(field.attribute)
                else:
                    val = await elem.text_content()
                values.append(val.strip() if val else None)
            return values
        
        # 提取单个值
        if field.attribute:
            value = await locator.first.get_attribute(field.attribute)
        else:
            value = await locator.first.text_content()
        
        return value.strip() if value else None
    
    async def scrape_with_pagination(self) -> List[Dict[str, Any]]:
        """
        抓取分页数据
        
        Returns:
            所有页面的数据
        """
        current_page = 1
        
        while True:
            # 检查是否达到最大页数
            if self.config.max_pages > 0 and current_page > self.config.max_pages:
                print(f"✅ 达到最大页数: {self.config.max_pages}")
                break
            
            # 检查页码范围
            if self.config.page_range:
                start, end = self.config.page_range
                if current_page < start:
                    current_page += 1
                    continue
                if current_page > end:
                    print(f"✅ 达到页码范围上限: {end}")
                    break
            
            # 抓取当前页
            print(f"\n📄 抓取第 {current_page} 页...")
            page_data = await self.scrape_current_page()
            
            if page_data:
                self.all_data.extend(page_data)
                print(f"   ✓ 成功提取 {len(page_data)} 条数据")
            else:
                print(f"   ⚠️ 当前页无数据")
            
            # 检查是否有下一页
            if not self.config.next_button_selector:
                print("✅ 无分页配置，抓取完成")
                break
            
            # 查找下一页按钮
            next_button = self.page.locator(self.config.next_button_selector)
            
            try:
                # 检查按钮是否存在
                count = await next_button.count()
                if count == 0:
                    print("✅ 未找到下一页按钮")
                    break
                
                # 检查按钮是否可点击
                is_visible = await next_button.first.is_visible()
                is_enabled = await next_button.first.is_enabled()
                
                if not is_visible or not is_enabled:
                    print("✅ 下一页按钮不可用")
                    break
                
                # 点击下一页
                print(f"   🔄 点击下一页，等待 {self.config.delay} 秒...")
                await next_button.first.click()
                
                # 等待页面加载
                await asyncio.sleep(self.config.delay)
                await self.page.wait_for_load_state("networkidle", timeout=15000)
                
                current_page += 1
                
            except Exception as e:
                print(f"✅ 分页结束: {str(e)}")
                break
        
        return self.all_data
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        执行抓取（自动判断是否分页）
        
        Returns:
            抓取的所有数据
        """
        # 导航到目标页面
        print(f"🌐 访问: {self.config.url}")
        await self.page.goto(self.config.url)
        await asyncio.sleep(self.config.delay)
        
        # 判断是否需要分页
        if self.config.next_button_selector or self.config.page_range:
            return await self.scrape_with_pagination()
        else:
            data = await self.scrape_current_page()
            self.all_data = data
            return data
    
    async def scrape_from_current_page(self, skip_navigation: bool = True) -> List[Dict[str, Any]]:
        """
        从当前页面开始抓取（不导航）
        适用于已经打开的页面
        
        Args:
            skip_navigation: 是否跳过导航，默认True
        
        Returns:
            抓取的所有数据
        """
        print(f"📍 从当前页面开始抓取: {self.page.url}")
        
        # 等待页面稳定
        await asyncio.sleep(self.config.delay)
        
        # 判断是否需要分页
        if self.config.next_button_selector or self.config.page_range:
            return await self.scrape_with_pagination()
        else:
            data = await self.scrape_current_page()
            self.all_data = data
            return data
    
    def save_to_json(self, filename: str = "scraped_data.json") -> str:
        """
        保存数据到JSON文件
        
        Args:
            filename: 文件名
            
        Returns:
            保存结果信息
        """
        if not self.all_data:
            return "❌ 无数据可保存"
        
        output = {
            "metadata": {
                "total_items": len(self.all_data),
                "url": self.config.url,
                "fields": [field.name for field in self.config.fields]
            },
            "data": self.all_data
        }
        
        path = Path(filename)
        write_json_path(output, path)

        print(f"\n💾 数据已保存到: {path}")
        print(f"   总条目: {len(self.all_data)}")

        return str(path)
    
    def get_data(self) -> List[Dict[str, Any]]:
        """获取抓取的数据"""
        return self.all_data


def create_scraper_config(
    url: str,
    fields: Dict[str, str],
    container_selector: str,
    next_button_selector: Optional[str] = None,
    page_range: Optional[tuple] = None,
    delay: float = 3.0,
    max_pages: int = 0
) -> ScraperConfig:
    """
    创建抓取器配置（便捷函数）

    Args:
        url: 目标网址
        fields: 字段配置字典 {"字段名": "CSS选择器"}
        container_selector: 容器选择器
        next_button_selector: 下一页按钮选择器
        page_range: 页码范围
        delay: 延迟时间
        max_pages: 最大页数

    Returns:
        ScraperConfig对象
    """
    field_configs = [
        FieldConfig(name=name, selector=selector)
        for name, selector in fields.items()
    ]

    return ScraperConfig(
        url=url,
        fields=field_configs,
        container_selector=container_selector,
        next_button_selector=next_button_selector,
        page_range=page_range,
        delay=delay,
        max_pages=max_pages
    )
