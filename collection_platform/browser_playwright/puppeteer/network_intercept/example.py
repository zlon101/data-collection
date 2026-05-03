"""
网络拦截采集示例 — 通过监听 API 响应抓取分页数据

使用场景：
    页面中有一个分页表格，数据来自某个 API 接口。
    不需要解析 DOM，直接收集 API 返回的 JSON 数据。
"""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from browser import BrowserManager
from puppeteer.network_intercept import ApiCollectorConfig, ApiCollector


def format_articles(all_data: list[dict]) -> list[dict]:
    """将微信公众号 API 原始数据列表转为标准格式。"""
    results = []
    for item in all_data:
        if isinstance(item, str):
            json_item = json.loads(item)
            for pub_item in json_item.get("publish_list", []):
                info_str = pub_item.get("publish_info", "")
                try:
                    info_obj = json.loads(info_str)
                    appmsgex = info_obj.get("appmsgex", [])
                    if not appmsgex:
                        continue
                    raw_title = appmsgex[0].get("title", "")
                    link = appmsgex[0].get("link", "")
                    title = re.sub(r"[^一-龥0-9]", "", raw_title)
                    results.append({"title": title, "link": link})
                except json.JSONDecodeError as e:
                    print(f"解析失败: {e!r}, 原始值: {info_str[:100]}...")
        else:
            results.append(item)
    return results


async def collect_api_data():
    """示例：连接已有页面，采集分页 API 数据。"""

    target_url = "https://mp.weixin.qq.com/"
    save_name = "api_collected_data.json"
    config = ApiCollectorConfig(
        # 匹配目标 API 的 URL（正则）
        url_pattern=r".*/cgi-bin/appmsgpublish.*",
        # 响应 JSON 中数据列表的路径，留空则取整个响应
        json_path="publish_page",
        # 下一页按钮的 CSS 选择器
        next_button_selector="a.weui-desktop-btn.weui-desktop-btn_default.weui-desktop-btn_mini",
        # 最多采集多少页，0 表示不限制
        max_pages=2,
        # 请求超时（毫秒）
        timeout=2000,
        # 点击下一页后的等待时间（毫秒）
        next_page_delay=1000,
        # 数据格式化回调
        data_format=format_articles,
    )

    async with BrowserManager(mode="connect") as bm:
        # 连接到目标页面
        page = await bm.get_or_create_page(target_url=target_url)
        if not page:
            print("❌ 未找到目标页面")
            return

        print(f"✅ 连接到页面: {page.url}")

        # 创建采集器并执行
        collector = ApiCollector(page, config)

        print("\n💡 请在浏览器中手动打开弹窗/触发列表加载")
        print("   脚本会自动捕获首次 API 响应，然后自动翻页\n")

        all_data = await collector.collect_all_pages()

        # 采集统计
        stats = collector.get_stats()
        print(f"\n📊 统计: {stats}")

        # 保存结果
        if all_data:
            collector.save_to_json(save_name)
            print(f"\n前 2 条数据预览:")
            for i, item in enumerate(all_data[:2], 1):
                print(f"  {i}. {json.dumps(item, ensure_ascii=False)[:100]}")
        else:
            print("⚠️ 未采集到数据")


if __name__ == "__main__":
    asyncio.run(collect_api_data())
