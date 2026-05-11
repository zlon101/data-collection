#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boss 直聘爬虫 - 使用通用页面解析器
演示如何使用 UniversalPageParser 和 DetailPageSpiderUniversal
uv run --package app-script python -m app_uiautomator2.examples.boss_universal_example
"""

import os
from pathlib import Path
import random
import re
import time
from datetime import datetime
from typing import Any, Callable, Dict

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
    is_new_job_list: bool = False,
    is_search: bool = True,
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
    output_file = str(_local_data_dir / f"boss_{now.strftime('%m%d_%H%M')}.json")
    seen_unique_keys: set[str] = get_seen_unique_keys()

    if task_id:
        from common.logger import log
        log(f"连接 Android 设备，采集器: Boss 直聘...", task_id=task_id)

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

    # 配置详情页爬虫
    def custom_stop(item_value: Dict[str, str]) -> bool:
        active = item_value.get("活跃度", "")
        activeNotMatch = bool(active) and all(
            t2 not in active for t2 in ["分钟", "日", "周"]
        )
        distanceStr = re.sub(r"[^\d.]", "", item_value.get("距离", "") or "")
        distance = float(distanceStr) if distanceStr.strip() else 0
        distanceNotMatch = bool(distanceStr) and distance > max_dist
        return activeNotMatch or distanceNotMatch

    def generate_unique_key_detail(detail_data: Dict[str, str]) -> str:
        unique_keys = ["职位", "HR", "薪资"]
        valArr: list[str] = []
        for k in unique_keys:
            val = detail_data[k]
            if "职位" == k:
                val = [s.strip() for s in val.split("-") if s.strip()][0]
                val = SpeicalRe.sub("", val)
            elif "HR" == k:
                # 处理猎头、外派
                if (
                    detail_data.get("客户公司")
                    and "客户公司" in detail_data["客户公司"]
                ):
                    val = detail_data["客户公司"]
                    val = [s.strip() for s in val.split(":") if s.strip()][1]
                else:
                    val = [s.strip() for s in val.split("•") if s.strip()][0]
                val = SpeicalRe.sub("", val)

            valArr.append(val)

        return "/".join(valArr)

    detail_spider = DetailPageSpiderUniversal(
        device=device,
        # Boss直聘详情页底部标识
        bottom_indicator_resourceId="com.hpbr.bosszhipin:id/tv_safe_tips",
        generate_unique_key=generate_unique_key_detail,
        custom_stop=custom_stop,
        detail_selectors={
            "详细地址": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_required_location",
                "optional": False,
            },
            "活跃度": {
                "resourceId": "com.hpbr.bosszhipin:id/boss_label_tv",
                "optional": True,
            },
            "职位描述": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_description",
                "optional": False,
            },
            "距离": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_title",
                "textPattern": r"距离家庭住址",
                "optional": True,  # 可选，有些职位可能不显示距离
            },
            # 用于生成唯一key
            "职位": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_job_name",
                "optional": False,
            },
            "HR": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_boss_title",
                "optional": True,
            },
            "薪资": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_job_salary",
                "optional": False,
            },
            # 猎头/派遣
            "客户公司": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_com_name",
                "optional": True,
            },
        },
    )

    # 列表页配置
    container_selector = ""
    if is_search:
        container_selector = "com.hpbr.bosszhipin:id/recyclerView_list"
    elif is_new_job_list:
        container_selector = "com.hpbr.bosszhipin:id/recycler_view"
    else:
        container_selector = "com.hpbr.bosszhipin:id/rv_list"

    # 生成唯一标识
    def generate_unique_key(item: Dict[str, Any]) -> str:
        unique_keys = ["职位", "公司", "薪资"]
        valArr: list[str] = []
        for k in unique_keys:
            val = str(item.get(k, ""))
            if "职位" == k:
                val = [s.strip() for s in val.split("-") if s.strip()][0]
                val = SpeicalRe.sub("", val)
            elif "公司" == k:
                val = SpeicalRe.sub("", val)
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

        money = parse_money(item_value["薪资"] or "")
        return (
            job_ok
            and company_ok
            and item_value.get("unique_item_key") not in seen_unique_keys
            and money["max"] >= money_min
        )

    def format_data(data_list: list[dict[str, Any]]):
        for item in data_list:
            item["来源"] = "boss"
            item["日期"] = now.strftime("%m-%d %H:%M:%S")

    list_config = ListPageSpiderParam(
        device=device,
        container_selector=container_selector,
        item_selector="com.hpbr.bosszhipin:id/cl_card_container",
        selectors={
            "公司": "com.hpbr.bosszhipin:id/tv_company_name",
            "职位": "com.hpbr.bosszhipin:id/tv_position_name",
            "薪资": "com.hpbr.bosszhipin:id/tv_salary_statue",
            # "HR": "com.hpbr.bosszhipin:id/tv_employer"
        },
        generate_unique_key=generate_unique_key,
        item_processing_callback=detail_spider.parse_and_return,
        item_filter=item_filter,
        max_items=max_items,
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
    # 30 条耗时9分钟
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
