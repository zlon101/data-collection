# core/__init__.py
"""
core 包公共导出。
外部模块只需 `from core import setup_android_device, create_android_poco`
即可获取最常用的初始化函数，无需了解内部文件布局。
"""

from core.device_manager import setup_android_device, setup_with_auto
from core.poco_helper import create_android_poco

__all__ = [
    "setup_android_device",
    "setup_with_auto",
    "create_android_poco",
]
