"""
browser_playwright 采集器启动入口。
"""

from pathlib import Path

from browser_playwright.browser import BrowserManager
from browser_playwright.puppeteer import UniversalScraper, create_scraper_config

from common.file_manager import write_json_path
from common.logger import log


async def run_browser_scraper(
    url: str,
    fields: dict[str, str],
    container_selector: str,
    next_button_selector: str | None = None,
    max_pages: int = 0,
    delay: float = 3.0,
    output_filename: str = "scraped_data.json",
    task_id: str | None = None,
) -> str:
    """执行 browser_playwright 采集，返回输出文件路径。"""
    log("连接浏览器...", task_id=task_id)

    async with BrowserManager(mode="connect") as bm:
        page = await bm.get_or_create_page(target_url=url)
        if not page:
            log(f"未找到页面: {url}", level="ERROR", task_id=task_id)
            raise RuntimeError(f"No tab found for: {url}")

        log(f"已连接页面: {page.url}", task_id=task_id)

        config = create_scraper_config(
            url=url,
            fields=fields,
            container_selector=container_selector,
            next_button_selector=next_button_selector,
            max_pages=max_pages,
            delay=delay,
        )

        scraper = UniversalScraper(page, config)
        log("开始抓取...", task_id=task_id)
        data = await scraper.scrape_from_current_page()

        if data:
            output_path = Path("local_data") / "raw" / output_filename
            write_json_path(data, output_path)
            log(f"采集完成，共 {len(data)} 条，已保存至 {output_path}", task_id=task_id)
            return str(output_path)
        else:
            log("未抓取到数据", level="WARNING", task_id=task_id)
            return ""
