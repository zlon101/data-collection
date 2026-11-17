from datetime import datetime
from urllib.parse import urlparse

from browser_playwright.launcher import run_browser_scraper

from common.logger import log
from scrape_agent.state import GraphState


async def full_scrape(state: GraphState) -> dict:
    cfg = state["scraper_config"]
    host = urlparse(cfg["url"]).hostname or "web"
    host = host.replace("www.", "").split(".")[0]
    filename = f"web_{host}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    max_pages = int(cfg.get("max_pages") or state.get("max_pages") or 1)
    next_button = cfg.get("next_button_selector") or None
    enable_detail = bool(cfg.get("enable_detail"))
    log(
        f"用户已确认配置，开始完整抓取 max_pages={max_pages} "
        f"next={next_button or '(无)'} detail={enable_detail}"
    )
    path = await run_browser_scraper(
        url=cfg["url"],
        fields=cfg["fields"],
        container_selector=cfg["container_selector"],
        next_button_selector=next_button,
        max_pages=max_pages,
        delay=3.0,
        output_filename=filename,
        detail_fields=cfg.get("detail_fields") if enable_detail else None,
        detail_container_selector=(
            cfg.get("detail_container_selector") if enable_detail else None
        ),
        detail_entry="click" if enable_detail else "url",
    )
    if path:
        log(f"完整抓取完成: {path}")
    else:
        log("完整抓取未得到数据", level="WARNING")
    return {"output_path": path}
