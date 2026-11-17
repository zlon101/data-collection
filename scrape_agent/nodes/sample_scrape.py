from browser_playwright.puppeteer import UniversalScraper, create_scraper_config
from browser_playwright.puppeteer.merged_scraper import (
    MergedScraper,
    create_merged_scraper_config,
)

from common.logger import log
from scrape_agent.browser_session import open_target_page
from scrape_agent.state import GraphState

SAMPLE_SIZE = 3


async def sample_scrape(state: GraphState) -> dict:
    cfg = state["scraper_config"]
    log("试抓以供确认...")
    list_config = create_scraper_config(
        url=cfg["url"],
        fields=cfg["fields"],
        container_selector=cfg["container_selector"],
        delay=3.0,
        max_pages=1,
    )
    async with open_target_page(cfg["url"]) as page:
        if cfg.get("enable_detail"):
            merged_config = create_merged_scraper_config(
                list_config=list_config,
                detail_fields=cfg["detail_fields"],
                detail_container_selector=cfg["detail_container_selector"],
                detail_entry="click",
            )
            scraper = MergedScraper(page, merged_config)
            list_items = await scraper.list_scraper.scrape_current_page()
            if not list_items:
                log("试抓为空，用户可拒绝以重新解析", level="WARNING")
                return {"sample_data": []}
            containers = await page.locator(cfg["container_selector"]).all()
            item = await scraper.scrape_list_item_with_detail(
                list_item=list_items[0],
                container=containers[0] if containers else None,
                item_index=0,
                page_num=1,
            )
            sample = [item]
            log("试抓 1 条（含点击进入的详情）")
        else:
            scraper = UniversalScraper(page, list_config)
            data = await scraper.scrape_current_page()
            sample = data[:SAMPLE_SIZE]
            log(f"试抓得到 {len(data)} 条，展示前 {len(sample)} 条")

    for i, item in enumerate(sample, 1):
        log(f"样本 {i}: {item}")
    if not sample:
        log("试抓为空，用户可拒绝以重新解析", level="WARNING")
    return {"sample_data": sample}
