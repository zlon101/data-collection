"""
browser_playwright 采集器启动入口。
"""

from collections.abc import Callable
from pathlib import Path

from browser_playwright.browser import BrowserManager
from browser_playwright.puppeteer import UniversalScraper, create_scraper_config
from browser_playwright.puppeteer.merged_scraper import (
    MergedScraper,
    create_merged_scraper_config,
)

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
    is_cancelled: Callable[[], bool] | None = None,
    # 详情页抓取参数
    detail_fields: dict[str, str] | None = None,
    detail_container_selector: str | None = None,
    detail_url_field: str | None = None,
    detail_url_attribute: str = "href",
    detail_entry: str = "url",
    navigation_mode: str = "go_back",
    back_wait_time: float = 2.0,
    detail_page_wait_time: float = 2.0,
    max_detail_retries: int = 2,
    continue_on_error: bool = True,
) -> str | None:
    """执行 browser_playwright 采集。

    Returns:
        输出文件路径（正常完成），None 表示被取消或无数据。
    """
    log("连接浏览器...", task_id=task_id)

    async with BrowserManager(mode="connect") as bm:
        page = await bm.get_or_create_page(target_url=url)
        if not page:
            log(f"未找到页面: {url}", level="ERROR", task_id=task_id)
            raise RuntimeError(f"No tab found for: {url}")

        log(f"已连接页面: {page.url}", task_id=task_id)

        list_config = create_scraper_config(
            url=url,
            fields=fields,
            container_selector=container_selector,
            next_button_selector=next_button_selector,
            max_pages=max_pages,
            delay=delay,
        )

        # 判断是否启用详情页抓取模式
        enable_detail = (
            detail_fields is not None
            and detail_container_selector is not None
            and (detail_entry == "click" or detail_url_field is not None)
        )

        if enable_detail:
            assert detail_fields is not None
            assert detail_container_selector is not None
            merged_config = create_merged_scraper_config(
                list_config=list_config,
                detail_fields=detail_fields,
                detail_container_selector=detail_container_selector,
                detail_url_field=detail_url_field or "",
                detail_url_attribute=detail_url_attribute,
                detail_entry=detail_entry,
                navigation_mode=navigation_mode,
                back_wait_time=back_wait_time,
                detail_page_wait_time=detail_page_wait_time,
                max_detail_retries=max_detail_retries,
                continue_on_error=continue_on_error,
            )
            scraper = MergedScraper(page, merged_config, is_cancelled=is_cancelled)
            log("开始抓取（列表+详情页模式）...", task_id=task_id)
            data = await scraper.scrape_from_current_page()
        else:
            scraper = UniversalScraper(page, list_config, is_cancelled=is_cancelled)
            log("开始抓取...", task_id=task_id)
            data = await scraper.scrape_from_current_page()

        if scraper.cancelled:
            log("采集任务已取消", level="INFO", task_id=task_id)
            return None

        if data:
            output_path = Path("local_data") / "raw" / output_filename
            write_json_path(data, output_path)
            log(f"采集完成，共 {len(data)} 条，已保存至 {output_path}", task_id=task_id)
            return str(output_path)
        else:
            log("未抓取到数据", level="WARNING", task_id=task_id)
            return None
