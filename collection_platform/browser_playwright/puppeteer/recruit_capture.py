"""
招聘页面采集模块
================
用微信文章（微信公众号），同时提取：
1. 页面 HTML（<body> outerHTML）
2. 全页截图（PNG，供 LLM 视觉分析）

结果保存至 local_data/raw/ 目录。
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime

from browser_playwright.browser import BrowserManager

logger = logging.getLogger(__name__)

# 截图和 raw 数据存储目录
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.resolve()
SCREENSHOT_DIR = _PROJECT_ROOT / "local_data" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def capture_recruit_page(url: str) -> dict:
    """
    采集单个招聘页面。

    Args:
        url: 微信文章 URL

    Returns:
        dict: {
            "title": str,
            "body_html": str,         # <body> 的 outerHTML
            "screenshot_path": str,   # 全页截图绝对路径
            "url": str,
            "captured_at": str,
        }
    """
    async with BrowserManager(mode="connect") as bm:
        browser = bm.get_browser()
        context = browser.contexts[0]

        # 先尝试查找已有的微信文章标签页（保留登录态）
        page_was_existing = False

        # 从 URL 中提取 mid 参数（微信文章唯一标识）
        mid_match = re.search(r'mid=(\d+)', url)
        mid_param = mid_match.group(1) if mid_match else None

        if mid_param:
            page = await bm.find_page_by_url(f"mid={mid_param}", exact_match=False)
        else:
            page = await bm.find_page_by_url(url, exact_match=False)

        if not page:
            logger.info("未在已打开标签页中找到该文章，尝试在新标签页打开")
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        else:
            page_was_existing = True
            logger.info("复用已有标签页: %s", page.url[:80])
            # 确保页面已加载完成
            await page.bring_to_front()
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
            # 回到顶部，确保滚动加载从顶部开始触发
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)

        # 等待微信文章正文渲染（微信公众号是异步加载 + 滚动懒加载）
        try:
            await page.wait_for_selector("#js_content", timeout=15000)

            # 步骤 1: 从顶部开始，分多次小幅度滚动，每次停留 1.5 秒触发懒加载
            logger.info("开始滚动页面以触发图片懒加载...")
            await page.evaluate("""() => {
                return new Promise((resolve) => {
                    const scrollStep = window.innerHeight;
                    let currentScroll = 0;

                    const scroll = () => {
                        currentScroll += scrollStep;
                        window.scrollTo(0, currentScroll);

                        setTimeout(() => {
                            if (currentScroll >= document.body.scrollHeight) {
                                resolve(true);
                            } else {
                                scroll();
                            }
                        }, 1500);
                    };

                    window.scrollTo(0, 0);
                    setTimeout(scroll, 500);
                });
            }""")
            logger.info("滚动完成，等待图片加载...")

            # 步骤 2: 等待所有图片加载完成
            await page.evaluate("""() => {
                const images = document.querySelectorAll('img');
                const promises = Array.from(images).map(img => {
                    if (img.complete && img.naturalWidth > 0) {
                        return Promise.resolve();
                    }
                    return new Promise(resolve => {
                        img.onload = () => resolve();
                        img.onerror = () => resolve();
                        setTimeout(() => resolve(), 5000);
                    });
                });
                return Promise.all(promises);
            }""")

            # 额外等待 2 秒确保所有内容渲染完毕
            await page.wait_for_timeout(2000)
            logger.info("所有图片加载完成")
        except Exception as e:
            logger.warning("等待正文加载超时: %s，继续执行", e)
            await page.wait_for_timeout(3000)

        # 提取标题和 <body> outerHTML
        page_data = await page.evaluate("""() => {
            const title = document.title;
            return {
                title: title,
                bodyHtml: document.body.outerHTML
            };
        }""")

        # 截图前滚动回顶部
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)

        # 全页截图
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"recruit_{timestamp}.png"
        screenshot_path = SCREENSHOT_DIR / screenshot_filename

        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info("截图已保存: %s", screenshot_path)

        # 如果是新开的标签页则关闭，复用的已有标签页保留
        if not page_was_existing:
            await page.close()

    result = {
        "title": page_data.get("title", ""),
        "body_html": page_data.get("bodyHtml", ""),
        "screenshot_path": str(screenshot_path),
        "url": url,
        "captured_at": datetime.now().isoformat(),
    }

    # 保存到 raw 目录
    raw_filename = _save_to_raw(result)
    result["raw_filename"] = raw_filename
    logger.info("数据已保存至 raw: %s", raw_filename)

    return result


def _save_to_raw(data: dict) -> str:
    """将采集结果保存到 local_data/raw/。"""
    from common import file_manager

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 标题中提取账号名（微信文章通常是公众号名）
    account = "recruit"
    filename = f"recruit_{account}_{timestamp}.json"

    file_manager.write_json(data, filename, data_type="raw")
    return filename
