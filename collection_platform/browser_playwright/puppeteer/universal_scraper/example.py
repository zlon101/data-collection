"""
通用抓取器使用示例
演示如何抓取 SegmentFault 和其他网站数据
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv


from browser import BrowserManager
from puppeteer.universal_scraper import UniversalScraper, create_scraper_config

load_dotenv()


# ==========================================
# 示例 1: SegmentFault 列表数据
# ==========================================

async def example_segmentfault():
    """
    示例：抓取 SegmentFault 首页文章列表
    """
    print("\n" + "="*60)
    print("📌 示例 1: SegmentFault 文章列表")
    print("="*60 + "\n")
    
    async with BrowserManager(mode="launch", headless=False) as bm:
        page = await bm.get_or_create_page()
        
        # 配置抓取参数
        config = create_scraper_config(
            url="https://segmentfault.com/",
            fields={
                "标题": "h3 a.text-body",
                "投票数量": ".num-card .font-size-16",
                "阅读数量": ".num-card.text-secondary .font-size-16"
            },
            container_selector=".list-group.list-group-flush > .list-group-item",
            next_button_selector="a.page-link[rel='next']",
            delay=5.0,  # 页面至少停留5秒
            max_pages=2  # 抓取2页
        )
        
        # 执行抓取
        scraper = UniversalScraper(page, config)
        data = await scraper.scrape()
        
        # 保存数据
        scraper.save_to_json("segmentfault_articles.json")
        
        # 显示前3条
        print("\n📊 数据示例（前3条）:")
        for i, item in enumerate(data[:3], 1):
            print(f"\n{i}. {item}")


# ==========================================
# 示例 2: 单页抓取（无分页）
# ==========================================

async def example_single_page():
    """
    示例：抓取单页数据（无分页）
    """
    print("\n" + "="*60)
    print("📌 示例 2: 单页抓取")
    print("="*60 + "\n")
    
    async with BrowserManager(mode="launch", headless=False) as bm:
        page = await bm.get_or_create_page()
        
        config = create_scraper_config(
            url="https://news.ycombinator.com/",
            fields={
                "标题": ".titleline > a",
                "分数": ".score",
                "作者": ".hnuser"
            },
            container_selector=".athing",
            delay=3.0
        )
        
        scraper = UniversalScraper(page, config)
        data = await scraper.scrape()
        
        scraper.save_to_json("hackernews_top.json")
        
        print(f"\n✅ 抓取了 {len(data)} 条数据")


# ==========================================
# 示例 3: 页码范围抓取
# ==========================================

async def example_page_range():
    """
    示例：抓取指定页码范围
    """
    print("\n" + "="*60)
    print("📌 示例 3: 页码范围抓取")
    print("="*60 + "\n")
    
    async with BrowserManager(mode="launch", headless=False) as bm:
        page = await bm.get_or_create_page()
        
        config = create_scraper_config(
            url="https://segmentfault.com/",
            fields={
                "标题": "h3 a.text-body",
                "投票数": ".num-card .font-size-16"
            },
            container_selector=".list-group-item",
            next_button_selector="a.page-link[rel='next']",
            page_range=(1, 3),  # 只抓取第1-3页
            delay=4.0
        )
        
        scraper = UniversalScraper(page, config)
        data = await scraper.scrape()
        
        scraper.save_to_json("segmentfault_pages_1_3.json")


# ==========================================
# 示例 4: 提取属性值
# ==========================================

async def example_extract_attributes():
    """
    示例：提取元素属性（如 href, src）
    """
    print("\n" + "="*60)
    print("📌 示例 4: 提取属性值")
    print("="*60 + "\n")
    
    from puppeteer.universal_scraper.scraper import FieldConfig, ScraperConfig
    
    async with BrowserManager(mode="launch", headless=False) as bm:
        page = await bm.get_or_create_page()
        
        # 使用高级字段配置
        config = ScraperConfig(
            url="https://segmentfault.com/",
            fields=[
                FieldConfig(name="标题", selector="h3 a.text-body"),
                FieldConfig(name="链接", selector="h3 a.text-body", attribute="href"),
                FieldConfig(name="投票数", selector=".num-card .font-size-16")
            ],
            container_selector=".list-group-item",
            delay=3.0
        )
        
        scraper = UniversalScraper(page, config)
        data = await scraper.scrape()
        
        scraper.save_to_json("segmentfault_with_links.json")
        
        print("\n📊 示例数据（包含链接）:")
        if data:
            print(data[0])


# ==========================================
# 示例 5: 自定义延迟时间
# ==========================================

async def example_custom_delay():
    """
    示例：自定义页面等待时间
    """
    print("\n" + "="*60)
    print("📌 示例 5: 自定义延迟时间")
    print("="*60 + "\n")
    
    async with BrowserManager(mode="launch", headless=False) as bm:
        page = await bm.get_or_create_page()
        
        config = create_scraper_config(
            url="https://segmentfault.com/",
            fields={
                "标题": "h3 a.text-body"
            },
            container_selector=".list-group-item",
            next_button_selector="a.page-link[rel='next']",
            delay=8.0,  # 每页停留8秒
            max_pages=2
        )
        
        scraper = UniversalScraper(page, config)
        await scraper.scrape()
        
        scraper.save_to_json("slow_scrape.json")


# ==========================================
# 示例 6: 直接使用（不通过工具）
# ==========================================

async def example_direct_usage():
    """
    示例：直接使用抓取器（用于脚本）
    完整演示用户需求的场景
    """
    print("\n" + "="*60)
    print("📌 示例 6: 完整用户场景")
    print("="*60 + "\n")
    
    print("用户输入:")
    print("---")
    user_input = '''
    打开 https://segmentfault.com/ 页面，
    获取 .list-group.list-group-flush 对应的列表数据，
    
    采集的信息和对应的选择器如下：
    标题：h3 a.text-body
    投票数量：.num-card .font-size-16
    阅读数量：.num-card.text-secondary .font-size-16
    
    下一页按钮选择器是 a.page-link[rel='next']，
    页面至少停留5秒
    '''
    print(user_input)
    print("---\n")
    
    async with BrowserManager(mode="launch", headless=False) as bm:
        page = await bm.get_or_create_page()
        
        # 根据用户输入创建配置
        config = create_scraper_config(
            url="https://segmentfault.com/",
            fields={
                "标题": "h3 a.text-body",
                "投票数量": ".num-card .font-size-16",
                "阅读数量": ".num-card.text-secondary .font-size-16"
            },
            container_selector=".list-group.list-group-flush > .list-group-item",
            next_button_selector="a.page-link[rel='next']",
            delay=5.0,
            max_pages=2
        )
        
        # 执行抓取
        print("🚀 开始抓取...")
        scraper = UniversalScraper(page, config)
        data = await scraper.scrape()
        
        # 保存为用户期望的格式
        import json
        
        # 简化格式（只保留数据数组）
        simple_output = data
        
        with open("output.json", 'w', encoding='utf-8') as f:
            json.dump(simple_output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 输出已保存到 output.json")
        print(f"   总条目: {len(data)}")
        
        print("\n📄 输出示例:")
        print(json.dumps(data[:2], ensure_ascii=False, indent=2))


# ==========================================
# 主菜单
# ==========================================

async def main():
    """主菜单"""
    examples = {
        "1": ("SegmentFault 文章列表", example_segmentfault),
        "2": ("单页抓取", example_single_page),
        "3": ("页码范围", example_page_range),
        "4": ("提取属性", example_extract_attributes),
        "5": ("自定义延迟", example_custom_delay),
        "6": ("完整用户场景", example_direct_usage)
    }
    
    print("\n" + "="*60)
    print("🎓 通用抓取器使用示例")
    print("="*60)
    print("\n可用示例:")
    for key, (name, _) in examples.items():
        print(f"   {key}. {name}")
    
    choice = input("\n选择示例 (1-6): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\n🚀 运行示例: {name}")
        await func()
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    asyncio.run(main())
