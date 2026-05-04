"""
浏览器管理模块
负责浏览器的启动、连接和生命周期管理
"""

import os
from dotenv import load_dotenv
from typing import Literal, TYPE_CHECKING
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

if TYPE_CHECKING:
    from playwright.async_api import Playwright

from .detector import find_chrome_cdp_url

load_dotenv()

class BrowserManager:
    """浏览器管理器"""
    
    def __init__(
        self,
        mode: Literal["launch", "connect"] = "launch",
        headless: bool = False,
        cdp_url: str | None = None,
        cdp_ports: list[int] | None = None
    ):
        """
        初始化浏览器管理器

        Args:
            mode: 浏览器模式
                - "launch": 启动新的 Chromium 实例
                - "connect": 连接到已有的 Chrome（通过 CDP）
            headless: 是否无头模式（仅在 launch 模式下有效）
            cdp_url: CDP 连接地址（connect 模式下使用）
            cdp_ports: 自动检测的 CDP 端口列表
        """
        self.mode = mode
        self.headless = headless
        self.cdp_url = cdp_url = os.getenv("CDP_URL") or cdp_url
        self.cdp_ports = cdp_ports if cdp_ports is not None else [9222, 9223, 9224]
        
        self.browser: Browser | None = None
        self.playwright: "Playwright" | None = None
        self._is_external_browser = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()
    
    async def start(self) -> Browser:
        """启动或连接浏览器"""
        self.playwright = await async_playwright().start()
        
        if self.mode == "launch":
            self.browser = await self._launch_browser()
            self._is_external_browser = False
            print(f"✅ Launched new Chromium instance (headless={self.headless})")
        
        elif self.mode == "connect":
            self.browser = await self._connect_to_chrome()
            self._is_external_browser = True
            print(f"✅ Connected to existing Chrome instance")
        
        else:
            raise ValueError(f"Invalid mode: {self.mode}. Use 'launch' or 'connect'")
        
        return self.browser
    
    async def _launch_browser(self) -> Browser:
        """启动新的 Chromium 实例"""
        assert self.playwright is not None, "Playwright not initialized"
        return await self.playwright.chromium.launch(headless=self.headless)
    
    async def _connect_to_chrome(self) -> Browser:
        """连接到已有的 Chrome 实例"""
        assert self.playwright is not None, "Playwright not initialized"
        
        # 如果未指定 CDP URL，自动检测
        if not self.cdp_url:
            print("🔍 Auto-detecting Chrome CDP endpoint...")
            self.cdp_url = await find_chrome_cdp_url(self.cdp_ports)
            
            if not self.cdp_url:
                raise ConnectionError(
                    "❌ No Chrome instance found with remote debugging enabled.\n"
                    "💡 Start Chrome with: chrome.exe --remote-debugging-port=9222\n"
                    f"   Tried ports: {self.cdp_ports}"
                )
        
        print(f"🔌 Connecting to Chrome at {self.cdp_url}...")
        
        try:
            browser = await self.playwright.chromium.connect_over_cdp(
                self.cdp_url,
                timeout=10000  # 10秒超时
            )
            return browser
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Chrome at {self.cdp_url}: {str(e)}"
            )
    
    async def get_or_create_page(self, target_url: str | None = None) -> Page:
        """
        获取当前页面或创建新页面
        
        Args:
            target_url: 目标URL（可选）
                - 如果提供，会查找匹配此URL的已打开标签页
                - 支持部分匹配（URL包含关系）
                - 如果找不到，按原逻辑返回或创建页面
        
        Returns:
            Page: Playwright 页面对象
        """
        if not self.browser:
            raise RuntimeError("Browser not started. Call start() first.")
        
        # 如果指定了目标URL，尝试查找对应的标签页
        if target_url:
            page = await self.find_page_by_url(target_url)
            if page:
                print(f"✅ Found existing tab: {target_url}")
                return page
            else:
                print(f"⚠️ No tab found for: {target_url}")
        
        # 获取所有上下文
        contexts = self.browser.contexts
        
        # 如果没有上下文，创建一个新的
        if not contexts:
            print("📂 No context found, creating a new one...")
            context = await self.browser.new_context()
            page = await context.new_page()
            return page
        
        # 使用第一个上下文
        context = contexts[0]
        pages = context.pages
        
        # 如果没有页面，创建一个新的
        if not pages:
            print("📄 No pages found, creating a new one...")
            page = await context.new_page()
            return page
        
        # 返回最后一个活跃页面
        return pages[-1]
    
    async def find_page_by_url(
        self,
        target_url: str,
        exact_match: bool = False
    ) -> Page | None:
        """
        在所有打开的标签页中查找匹配指定URL的页面
        
        Args:
            target_url: 目标URL
            exact_match: 是否精确匹配
                - False（默认）: 部分匹配（页面URL包含target_url）
                - True: 精确匹配（页面URL完全等于target_url）
        
        Returns:
            Page: 找到的页面对象，如果没找到返回None
        """
        if not self.browser:
            return None
        
        # 规范化目标URL
        target_url_normalized = target_url.lower().strip()
        
        # 遍历所有上下文和页面
        for context in self.browser.contexts:
            for page in context.pages:
                try:
                    page_url = page.url.lower()
                    
                    # 匹配逻辑
                    if exact_match:
                        if page_url == target_url_normalized:
                            return page
                    else:
                        if target_url_normalized in page_url:
                            return page
                except Exception as e:
                    # 页面可能已关闭或无法访问
                    continue
        
        return None
    
    async def list_all_pages(self) -> list[dict]:
        """
        列出所有打开的页面信息
        
        Returns:
            包含所有页面信息的列表
        """
        if not self.browser:
            return []
        
        pages_info = []
        
        for ctx_idx, context in enumerate(self.browser.contexts):
            for page_idx, page in enumerate(context.pages):
                try:
                    pages_info.append({
                        "context_index": ctx_idx,
                        "page_index": page_idx,
                        "url": page.url,
                        "title": await page.title(),
                        "is_closed": page.is_closed()
                    })
                except Exception as e:
                    pages_info.append({
                        "context_index": ctx_idx,
                        "page_index": page_idx,
                        "url": "[Error]",
                        "title": str(e),
                        "is_closed": True
                    })
        
        return pages_info
    
    async def get_context(self) -> BrowserContext:
        """获取浏览器上下文"""
        if not self.browser:
            raise RuntimeError("Browser not started.")
        
        contexts = self.browser.contexts
        if not contexts:
            return await self.browser.new_context()
        
        return contexts[0]
    
    def get_browser(self) -> Browser:
        """获取浏览器实例"""
        if not self.browser:
            raise RuntimeError("Browser not started.")
        return self.browser
    
    async def close(self):
        """关闭浏览器"""
        # 如果是外部 Chrome，不关闭浏览器
        if self._is_external_browser:
            print("🔗 External Chrome remains open (not closed by manager)")
        elif self.browser:
            await self.browser.close()
            print("🚪 Browser closed")
        
        # 关闭 Playwright
        if self.playwright:
            await self.playwright.stop()
    
    def get_info(self) -> dict:
        """获取浏览器信息"""
        if not self.browser:
            return {"status": "not_started"}
        
        contexts = self.browser.contexts
        total_pages = sum(len(ctx.pages) for ctx in contexts)
        
        return {
            "status": "running",
            "mode": self.mode,
            "is_external": self._is_external_browser,
            "contexts": len(contexts),
            "total_pages": total_pages,
            "cdp_url": self.cdp_url if self.mode == "connect" else None
        }