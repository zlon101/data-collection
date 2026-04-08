# scrapers/page_navigator.py
"""
页面导航：滚动、点击、返回、截图。
所有导航操作都基于 Airtest 实现。
"""

import logging
import os
from pathlib import Path

from airtest.core.api import (
    connect_device,
    keyevent,
    sleep,
    snapshot,
    swipe,
    touch,
    wake,
)

logger = logging.getLogger(__name__)

_SNAP_DIR = Path(__file__).parent.parent / "outputs" / "wechat_snaps"
_SNAP_DIR.mkdir(parents=True, exist_ok=True)


def init_device(adb_path: str = "/opt/homebrew/bin/adb") -> None:
    if adb_path and Path(adb_path).is_file():
        os.environ["AIRTEST_ADB_PATH"] = adb_path
    connect_device("Android:///")
    wake()
    logger.info("设备初始化完成")


def take_snapshot(name: str) -> str:
    """截图并保存，返回文件路径。"""
    path = str(_SNAP_DIR / f"{name}.jpg")
    snapshot(filename=path)
    return path


def scroll_down(screen_width: int, screen_height: int, duration: float = 0.4) -> None:
    """向下滚动一屏（从 70% 滑到 30%）。"""
    swipe(
        (screen_width * 0.5, screen_height * 0.7),
        (screen_width * 0.5, screen_height * 0.3),
        duration=duration,
    )


def tap(x: int, y: int) -> None:
    """点击指定坐标。"""
    touch((x, y))


def go_back() -> None:
    """发送 Android 返回键。"""
    keyevent("BACK")


def wait(seconds: float = 1.5) -> None:
    sleep(seconds)