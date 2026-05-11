#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智联
uv run --package app-script app_uiautomator2.examples.zhilian_example
"""

import os
import re
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import uiautomator2 as u2
from rich.console import Console
from rich.panel import Panel

from app_uiautomator2.examples.config import (
    SpeicalRe,
    parse_money,
)
from app_uiautomator2.examples.merge_job_data import get_seen_unique_keys
from app_uiautomator2.lib import DetailPageSpiderUniversal, ListPageSpider, ListPageSpiderParam

console = Console()


# 输出路径（可通过 LOCAL_DATA_DIR 环境变量配置）
_local_data_dir = Path(os.getenv("LOCAL_DATA_DIR", "./local_data")) / "job"
_local_data_dir.mkdir(parents=True, exist_ok=True)


def main(
    max_items: int = 20,
    is_search: bool = False,
    job_keys: list[str] | None = None,
    black_company: list[str] | None = None,
    money_min: float | None = None,
    max_distance: float | None = None,
    task_id: str | None = None,
    is_cancelled: Callable[[], bool] | None = None,
):
    from app_uiautomator2.examples.config import (
        BlackCompany,
        JobKeys,
        MAX_DISTANCE,
        MoneyMin,
    )

    job_keys = job_keys or JobKeys
    black_company = black_company or BlackCompany
    money_min = money_min if money_min is not None else MoneyMin
    max_dist = max_distance if max_distance is not None else MAX_DISTANCE

    now = datetime.now()
    seen_unique_keys: set[str] = get_seen_unique_keys()
    output_file = str(_local_data_dir / f"智联_{now.strftime('%m%d_%H%M')}.json")

    if task_id:
        from common.logger import log
        log(f"连接 Android 设备，采集器: 智联...", task_id=task_id)

    console.print(
        Panel.fit(
            "[bold cyan]智联招聘爬虫 - 通用解析器版本[/bold cyan]\n"
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
            val = detail_data.get(k, "")
            if "职位" == k:
                val = [s.strip() for s in val.split("-") if s.strip()][0]
                val = SpeicalRe.sub("", val or "")
            elif "公司" == k:
                val = SpeicalRe.sub("", val or "")[:4]
            valArr.append(val)
        return "/".join(valArr)

    def custom_stop(item: dict[str, str]) -> bool:
        distanceStr = re.sub(r"[^\d.]", "", item.get("距离", "") or "")
        distance = float(distanceStr) if distanceStr.strip() else 0
        distanceNotMatch = bool(distance) and distance > max_dist
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
        job_ok = bool(job) and "GIS" not in job and any(t in job for t in job_keys)

        company = item_value["公司"]
        company_ok = not company or all(
            black_item not in company for black_item in black_company
        )

        active = item_value.get("活跃度", "")
        active_ok = bool(active) and any(t2 in active for t2 in ["分", "日", "周"])

        money = parse_money(item_value["薪资"] or "")
        return (
            job_ok
            and active_ok
            and company_ok
            and item_value.get("unique_item_key") not in seen_unique_keys
            and money["max"] >= money_min
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
        is_cancelled=is_cancelled,
    )

    if task_id:
        from common.logger import log
        log(f"开始抓取，目标 {max_items} 条...", task_id=task_id)

    list_spider = ListPageSpider(config=list_config)

    # 5. 开始爬取
    list_spider.crawl()
    # 6. 保存结果
    list_spider.save_to_json(output_file)
    # 时长计算
    end_time = time.perf_counter()
    elapsed = (end_time - start_time) / 60  # 分
    console.print(f"耗时: {elapsed:.2f} 分")

    if list_spider.cancelled:
        if task_id:
            from common.logger import log
            log("采集已取消", task_id=task_id)
        return True

    if task_id:
        from common.logger import log
        log(f"采集完成，已保存至 {output_file}", task_id=task_id)

    return False


if __name__ == "__main__":
    main()
