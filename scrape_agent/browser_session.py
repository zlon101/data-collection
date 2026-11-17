from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from browser_playwright.browser import BrowserManager
from playwright.async_api import Page

from common.logger import log


@asynccontextmanager
async def open_target_page(url: str) -> AsyncIterator[Page]:
    """通过 CDP 连接已有 Chrome，定位或打开目标页。"""
    async with BrowserManager(mode="connect") as bm:
        page = await bm.get_or_create_page(target_url=url)
        if url.rstrip("/") not in page.url and page.url.rstrip("/") not in url:
            log(f"当前标签不是目标页，导航到 {url}")
            await page.goto(url, wait_until="domcontentloaded")
        yield page
