#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智联
uv run examples/xxx.py
"""

import uiautomator2 as u2
import sys
from pathlib import Path
from typing import Dict, Any
import re
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    BlackCompany,
    JobKeys,
    SpeicalRe,
    MAX_DISTANCE,
    MoneyMin,
    parse_money,
)

from lib import ListPageSpider, ListPageSpiderParam, DetailPageSpiderUniversal
from examples.merge_job_data import get_seen_unique_keys

console = Console()
now = datetime.now()
seen_unique_keys: set[str] = get_seen_unique_keys()

is_search = True  # 搜索后的列表
output_file = f"./data_json/智联_{now.strftime('%m%d_%H%M')}.json"
max_items = 20

def main():
    console.print(
        Panel.fit(
            "[bold cyan]Boss 直聘爬虫 - 通用解析器版本[/bold cyan]\n"
            "[dim]特性: 自动分屏 + 智能滚动 + 底部检测[/dim]",
            border_style="cyan",
        )
    )
    start_time = time.perf_counter()
    # 1. 连接设备
    device = u2.connect()

    # 2. 配置详情页爬虫
    def generate_unique_key_detail(detail_data: Dict[str, str]) -> str:
        unique_keys = ["职位", "公司", "薪资"]
        valArr: list[str] = []
        for k in unique_keys:
            val = detail_data[k]
            if "职位" == k:
                val = [s.strip() for s in val.split("-") if s.strip()][0]
                val = SpeicalRe.sub("", val or "")
            elif "公司" == k:
                val = SpeicalRe.sub("", val or "")[:4]
            valArr.append(val)
        return "/".join(valArr)

    def custom_stop(item: dict[str, str]) -> bool:
        distanceStr = re.sub(r"[^\d.]", "", item["距离"] or "")
        distance = float(distanceStr) if distanceStr.strip() else 0
        distanceNotMatch = bool(distance) and distance > MAX_DISTANCE
        return distanceNotMatch

    detail_spider = DetailPageSpiderUniversal(
        device=device,
        # 详情页底部标识
        bottom_indicator_resourceId="com.zhaopin.social:id/tv_safety_title",
        generate_unique_key=generate_unique_key_detail,
        custom_stop=custom_stop,
        detail_selectors={
            "职位": {
                "resourceId": "com.zhaopin.social:id/tv_job_name_new",
                "optional": False,
            },
            "公司": {
                "resourceId": "com.zhaopin.social:id/tv_hr_comany",
                "optional": True,
            },
            "薪资": {
                "resourceId": "com.zhaopin.social:id/tv_salary_new",
                "optional": False,
            },
            "详细地址": {
                "resourceId": "com.zhaopin.social:id/tv_company_address_new",
                "optional": False,
            },
            "职位描述": {
                "resourceId": "com.zhaopin.social:id/tv_desc",
                "optional": True,
                "textPattern": r"岗位|职责|任职|负责",
            },
            "距离": {
                "resourceId": "com.zhaopin.social:id/tv_right_distance",
                "optional": True,  # 可选，有些职位可能不显示距离
            },
            # 猎头/派遣
            # "客户公司": {
            #     "resourceId": "com.hpbr.bosszhipin:id/tv_com_name",
            #     "optional": True
            # },
        },
    )

    # 列表页配置
    # 生成唯一标识
    def generate_unique_key(item: Dict[str, Any]) -> str:
        unique_keys = ["职位", "公司", "薪资"]
        valArr: list[str] = []
        for k in unique_keys:
            val = str(item.get(k, ""))
            if "职位" == k:
                val = [s.strip() for s in val.split("-") if s.strip()][0]
                val = SpeicalRe.sub("", val or "")
            elif "公司" == k:
                val = SpeicalRe.sub("", val or "")[:4]
            valArr.append(val)
        return "/".join(valArr)

    # 过滤item, false 表示排除
    def item_filter(item_value: Dict[str, str]) -> bool:
        job = item_value["职位"]
        job_ok = bool(job) and "GIS" not in job and any(t in job for t in JobKeys)

        company = item_value["公司"]
        company_ok = not company or all(
            black_item not in company for black_item in BlackCompany
        )

        active = item_value["活跃度"]
        active_ok = bool(active) and any(t2 in active for t2 in ["分", "日", "周"])

        money = parse_money(item_value["薪资"] or "")
        return (
            job_ok
            and active_ok
            and company_ok
            and item_value.get("unique_item_key") not in seen_unique_keys
            and money["max"] >= MoneyMin
        )

    def format_data(data_list: list[dict[str, Any]]):
        for item in data_list:
            item["来源"] = "智联"
            item["日期"] = now.strftime("%m-%d %H:%M:%S")

    container_selector = (
        "com.zhaopin.social:id/rv_job_list"
        if is_search
        else "com.zhaopin.social:id/rv_position_recommend_new"
    )
    list_config = ListPageSpiderParam(
        device=device,
        container_selector=container_selector,
        item_selector="com.zhaopin.social:id/cl_root",
        selectors={
            "公司": "com.zhaopin.social:id/tv_company_name",
            "职位": "com.zhaopin.social:id/tv_position_name",
            "薪资": "com.zhaopin.social:id/tv_position_salary",
            "活跃度": "com.zhaopin.social:id/tv_hr_status",
        },
        max_items=max_items,
        generate_unique_key=generate_unique_key,
        item_processing_callback=detail_spider.parse_and_return,
        item_filter=item_filter,
        format_data=format_data,
    )
    list_spider = ListPageSpider(config=list_config)

    # 5. 开始爬取
    list_spider.crawl()
    # 6. 保存结果
    list_spider.save_to_json(output_file)
    # 时长计算
    end_time = time.perf_counter()
    elapsed = (end_time - start_time) / 60  # 分
    # 30 条耗时9分钟
    console.print(f"耗时: {elapsed:.2f} 分")


if __name__ == "__main__":
    main()
