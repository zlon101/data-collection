"""
app_uiautomator2 采集器启动入口。
将前端传入的标量参数转换为完整的爬虫配置（含硬编码的回调函数）。
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import uiautomator2 as u2

from app_uiautomator2.examples.config import (
    BlackCompany,
    JobKeys,
    MAX_DISTANCE,
    MoneyMin,
    SpeicalRe,
    parse_money,
)
from app_uiautomator2.examples.merge_job_data import get_seen_unique_keys
from app_uiautomator2.lib import DetailPageSpiderUniversal, ListPageSpider, ListPageSpiderParam

from common.logger import log


def _get_output_path() -> str:
    now = datetime.now()
    local_data_dir = Path(os.getenv("LOCAL_DATA_DIR", "./local_data")) / "job"
    local_data_dir.mkdir(parents=True, exist_ok=True)
    return str(local_data_dir / f"boss_{now.strftime('%m%d_%H%M')}.json")


def run_app_scraper(
    max_items: int = 20,
    is_search: bool = True,
    is_new_job_list: bool = False,
    job_keys: list[str] | None = None,
    black_company: list[str] | None = None,
    money_min: float | None = None,
    max_distance: float | None = None,
    task_id: str | None = None,
) -> str:
    """执行 app_uiautomator2 采集，返回输出文件路径。"""
    job_keys = job_keys or JobKeys
    black_company = black_company or BlackCompany
    money_min = money_min if money_min is not None else MoneyMin
    max_distance = max_distance if max_distance is not None else MAX_DISTANCE

    log("连接 Android 设备...", task_id=task_id)
    device = u2.connect()

    seen_unique_keys: set[str] = get_seen_unique_keys()
    now = datetime.now()
    output_file = _get_output_path()

    # ── 详情页配置 ──
    def generate_unique_key_detail(detail_data: dict[str, str]) -> str:
        unique_keys = ["职位", "HR", "薪资"]
        val_arr: list[str] = []
        for k in unique_keys:
            val = detail_data[k]
            if "职位" == k:
                val = [s.strip() for s in val.split("-") if s.strip()][0]
                val = SpeicalRe.sub("", val or "")
            elif "HR" == k:
                if (
                    detail_data.get("客户公司")
                    and "客户公司" in detail_data["客户公司"]
                ):
                    val = detail_data["客户公司"]
                    val = [s.strip() for s in val.split(":") if s.strip()][1]
                else:
                    val = [s.strip() for s in val.split("•") if s.strip()][0]
                val = SpeicalRe.sub("", val or "")
            val_arr.append(val)
        return "/".join(val_arr)

    def custom_stop(item: dict[str, str]) -> bool:
        distance_str = re.sub(r"[^\d.]", "", item.get("距离", "") or "")
        distance = float(distance_str) if distance_str.strip() else 0
        return bool(distance) and distance > max_distance

    detail_spider = DetailPageSpiderUniversal(
        device=device,
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
                "optional": True,
            },
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
            "客户公司": {
                "resourceId": "com.hpbr.bosszhipin:id/tv_com_name",
                "optional": True,
            },
        },
    )

    # ── 列表页配置 ──
    if is_search:
        container_selector = "com.hpbr.bosszhipin:id/recyclerView_list"
    elif is_new_job_list:
        container_selector = "com.hpbr.bosszhipin:id/recycler_view"
    else:
        container_selector = "com.hpbr.bosszhipin:id/rv_list"

    def generate_unique_key(item: dict[str, Any]) -> str:
        unique_keys = ["职位", "公司", "薪资"]
        val_arr: list[str] = []
        for k in unique_keys:
            val = str(item.get(k, ""))
            if "职位" == k:
                val = [s.strip() for s in val.split("-") if s.strip()][0]
                val = SpeicalRe.sub("", val or "")
            elif "公司" == k:
                val = SpeicalRe.sub("", val or "")
            val_arr.append(val)
        return "/".join(val_arr)

    def item_filter_func(item_value: dict[str, str]) -> bool:
        job = item_value["职位"]
        job_ok = bool(job) and "GIS" not in job and any(t in job for t in job_keys)

        company = item_value["公司"]
        company_ok = not company or all(b not in company for b in black_company)

        money = parse_money(item_value.get("薪资", "") or "")
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
        },
        generate_unique_key=generate_unique_key,
        item_processing_callback=detail_spider.parse_and_return,
        item_filter=item_filter_func,
        max_items=max_items,
        format_data=format_data,
    )

    log(f"开始抓取，目标 {max_items} 条...", task_id=task_id)
    list_spider = ListPageSpider(config=list_config)
    list_spider.crawl()
    list_spider.save_to_json(output_file)
    log(f"采集完成，已保存至 {output_file}", task_id=task_id)

    return output_file
