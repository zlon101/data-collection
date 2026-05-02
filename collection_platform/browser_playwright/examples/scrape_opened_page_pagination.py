"""
在已打开的列表页面上进行分页抓取
"""

import asyncio
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from browser import BrowserManager
from puppeteer import UniversalScraper, create_scraper_config


async def scrape_opened_page_with_pagination():
    """
    场景：在已打开的页面上进行分页抓取
    
    步骤：
    1. 连接到已打开的 Chrome
    2. 查找目标页面
    3. 在当前页面上进行分页抓取
    """
    print("\n" + "="*60)
    print("🎯 在已打开的页面上进行分页抓取")
    print("="*60 + "\n")

    async with BrowserManager(mode="connect") as bm:
        # 列出所有打开的页面
        pages_info = await bm.list_all_pages()
        if not pages_info:
            print("❌ 没有找到打开的标签页")
            return

        # 连接到已打开的页面
        page = await bm.get_or_create_page(target_url="https://segmentfault.com")

        if not page:
            print("❌ 未找到指定页面")
            return

        print(f"✅ 连接到页面: {page.url}")

        parseBug = False
        # 云效任务配置
        fileName = "test_云效任务统计.json"
        config = create_scraper_config(
            url=page.url,
            container_selector="li.item-wrap.py-3.list-group-item",
            next_button_selector=".next-btn.next-pagination-item.next-next",  # 下一页按钮
            delay=3.0,  # 每页等待3秒
            max_pages=1,  # 抓取2页
            fields={
                "标题": "h3 a.title",
            },
        )

        

        # 创建抓取器
        scraper = UniversalScraper(page, config)

        # ⭐ 关键：使用 scrape_from_current_page() 而不是 scrape()
        # 这样不会重新导航，直接在当前页面上抓取
        print("🚀 开始分页抓取...\n")
        data = await scraper.scrape_from_current_page()

        # 保存数据
        if data:
            scraper.save_to_json(fileName)
            print(f"\n✅ 成功!")
            print(f"   总条数: {len(data)}")
        else:
            print("\n⚠️ 未抓取到数据")


async def main():
    print("\n⚠️ 准备工作:")
    print("   1. 启动 Chrome: chrome.exe --remote-debugging-port=9222")
    print("   2. 打开要抓取的网页（如 SegmentFault 搜索结果页）")
    
    try:
        await scrape_opened_page_with_pagination()
    except ConnectionError as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n💡 解决方法:")
        print("   1. 启动 Chrome: chrome.exe --remote-debugging-port=9222")
        print("   2. 重新运行")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
