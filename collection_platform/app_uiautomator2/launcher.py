"""
app_uiautomator2 采集器启动入口。
根据 app_type 分别调用 Boss 或 智联 采集逻辑。
"""

from collections.abc import Callable

from app_uiautomator2.examples.boss_universal_example import main as boss_main
from app_uiautomator2.examples.zhilian_example import main as zhilian_main

COLLECTOR_PROFILES = {
    "boss": {
        "label": "Boss 直聘",
    },
    "zhilian": {
        "label": "智联",
    },
}


def run_app_scraper(
    app_type: str,
    max_items: int = 20,
    is_search: bool = True,
    is_new_job_list: bool = False,
    job_keys: list[str] | None = None,
    black_company: list[str] | None = None,
    money_min: float | None = None,
    max_distance: float | None = None,
    task_id: str | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> bool:
    """执行 app_uiautomator2 采集。

    Returns:
        True 表示被取消，False 表示正常完成。

    Args:
        app_type: "boss" 或 "zhilian"
    """
    profile = COLLECTOR_PROFILES.get(app_type)
    if not profile:
        raise ValueError(f"不支持的采集器类型: {app_type}")

    if app_type == "boss":
        return boss_main(
            max_items=max_items,
            is_new_job_list=is_new_job_list,
            is_search=is_search,
            job_keys=job_keys,
            black_company=black_company,
            money_min=money_min,
            max_distance=max_distance,
            task_id=task_id,
            is_cancelled=is_cancelled,
        )
    else:
        return zhilian_main(
            max_items=max_items,
            is_search=is_search,
            job_keys=job_keys,
            black_company=black_company,
            money_min=money_min,
            max_distance=max_distance,
            task_id=task_id,
            is_cancelled=is_cancelled,
        )
